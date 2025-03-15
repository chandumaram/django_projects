import os
import smtplib
import base64
import re
import imghdr
import pandas as pd
import time
from email.message import EmailMessage
from celery import Celery
# from celery.utils.log import get_task_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Celery Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

app = Celery("tasks", broker=REDIS_URL, backend=RESULT_BACKEND)

# Get Celery task-specific logger
# logger = get_task_logger(__name__)

# Ensure the backend is enabled
app.conf.update(
    result_backend=RESULT_BACKEND,
    task_track_started=True,
    task_ignore_result=False,
)

# Reports Directory
REPORT_FOLDER = os.getenv("REPORT_FOLDER", "reports")
ATTACHMENTS_FOLDER = os.getenv("ATTACHMENTS_FOLDER", "attachments")
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 5))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))  # Default to 10 if not set
DELAY_BETWEEN_BATCHES = int(os.getenv("DELAY_BETWEEN_BATCHES", 5))  # Default to 5 seconds

def process_inline_images(body_html):
    """
    Extracts base64 images from HTML content, embeds them as attachments in the email,
    and replaces the base64 image sources with CID references.
    """
    inline_files = []
    # img_pattern = re.compile(r'data:image/png;base64,([A-Za-z0-9+/=]+)')  # Regex to find base64 images
    img_pattern = re.compile(r'<img[^>]+src="data:image/[^;]+;base64,([^"]+)"') # Regex to find base64 images
    img_cids = {}

    def replace_img(match):
        img_data = match.group(1)

        # Decode base64 and attach to email
        image_bytes = base64.b64decode(img_data)
        # Detect image type
        image_type = imghdr.what(None, h=image_bytes)  # 'png', 'jpeg', 'gif', etc.
        # Default to 'png' if detection fails
        image_type = image_type if image_type else "png"

        img_index = len(img_cids)  # Keep track of images using dictionary keys
        img_filename = f"image_{img_index}.{image_type}"
        img_cid = f"image_{img_index}"

        inline_files.append({"image_bytes":image_bytes, "maintype":"image", "subtype":image_type, "filename":img_filename, "cid":img_cid})

        # Store CID reference
        img_cids[img_data] = img_cid

        return f'<img src="cid:{img_cid}"'  # Replace base64 data with CID reference

    # Replace all base64 images in a **single pass**
    body_html = img_pattern.sub(replace_img, body_html)

    return body_html, inline_files

def send_email(entry, subject, formatted_body, inline_files, attachment_paths, EMAIL_FROM, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD):
    """
    Sends an individual email and returns status.
    """

    try:
        recipient = entry["Email Id"]
        recipient_name = entry.get("Name", "")
        recipient_name = recipient_name if pd.notna(recipient_name) else ""  # Convert NaN to empty string

        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Process email body
        formatted_body = formatted_body.replace("{Name}", recipient_name)  # Replace placeholders
        # if body_format == "plain":
        #     formatted_body = formatted_body.replace("\n", "<br>")

        msg = EmailMessage()
        msg.set_content(formatted_body, subtype="html")
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = recipient

        # attache inline files
        for inline_file in inline_files:
            msg.add_attachment(inline_file["image_bytes"], maintype=inline_file["maintype"], subtype=inline_file["subtype"], filename=inline_file["filename"], cid=inline_file["cid"])

        # Attach files
        for attachment_path in attachment_paths:
            # Open and read the file to attach
            with open(attachment_path, "rb") as attachment:
                file_data = attachment.read()
                file_name = os.path.basename(attachment_path)
                # Attach the file using EmailMessage
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        # Use 'with' to automatically handle server connection closure
        with smtplib.SMTP(smtp_server, smtp_port) as server:  # Use SMTP on port 587 with starttls()
            server.starttls()  # Secure the connection
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)  # Login with your Gmail credentials
            server.send_message(msg)  # Send the email with attachments

        return recipient, "Success"
    except Exception as e:
        # Log error for debugging
        # logger.error(f"Error sending email to {entry['Email Id']}: {str(e)}")
        return recipient, f"Failed: {str(e)}"

@app.task(bind=True)
def send_bulk_emails(self, file_path, EMAIL_FROM, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, subject, body, body_format, timestamp, attachment_paths=[]):
    try:
        """Celery task to send bulk emails in batches."""
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        if "Email Id" not in df.columns:
            return {"status": "FAILURE", "message": "Missing 'Email Id' column in file."}
        elif "Name" not in df.columns:
            return {"status": "FAILURE", "message": "Missing 'Name' column in file."}

        # recipients = df["Email Id"].tolist()
        recipients = df[["Email Id", "Name"]].to_dict(orient="records")

        # Save email content
        content_file = os.path.join(ATTACHMENTS_FOLDER, f"{timestamp}_email_content.txt")
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(f"Subject: {subject}\n\nBody:\n{body}")

        total_emails = int(os.getenv("TOTAL_NUMBER_OF_EMAILS", len(recipients)))

        if len(recipients) < total_emails:
            total_emails = len(recipients)
        success_count = 0
        failure_count = 0
        report = []

        # Update Status every (20) emails
        update_status_interval = int(os.getenv("UPDATE_STATUS_INTERVAL", 20))
        update_status_counter = 0

        # Update Celery state (for live tracking)
        self.update_state(state="PROGRESS", meta={"total": total_emails, "success": 0, "failed": 0, "pending": total_emails})

        # formatting email body
        inline_files = []
        if body_format == "plain":
            formatted_body = body.replace("\n", "<br>")
        elif body_format == "rtf":
            formatted_body, inline_files = process_inline_images(body)
        else: # for HTML text
            formatted_body = body

        for i in range(0, total_emails, BATCH_SIZE):
            batch = recipients[i:i + BATCH_SIZE]

            # Use ThreadPoolExecutor for concurrent email sending
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_email = {
                    executor.submit(
                        send_email, entry, subject, formatted_body, inline_files, attachment_paths, EMAIL_FROM, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
                    ): entry for entry in batch
                }

                for future in as_completed(future_to_email):
                    entry = future_to_email[future]
                    try:
                        email, status = future.result()
                        report.append({"Email Id": email, "Name": entry["Name"], "Status": status})
                        if status == "Success":
                            success_count += 1
                        else:
                            failure_count += 1

                        # **Update Celery status (live tracking)**
                        update_status_counter += 1
                        if update_status_counter >= update_status_interval:
                            self.update_state(state="PROGRESS", meta={
                                "total": total_emails, 
                                "success": success_count, 
                                "failed": failure_count, 
                                "pending": total_emails - (success_count + failure_count) 
                            })
                            update_status_counter = 0  # Reset counter
                    except Exception as e:
                        # logger.error(f"Error processing email for {entry['Email Id']}: {str(e)}")
                        failure_count += 1
                        report.append({"Email Id": entry["Email Id"], "Name": entry["Name"], "Status": f"{str(e)}"})

            time.sleep(DELAY_BETWEEN_BATCHES) # Wait before next batch

        # Save the report with timestamp to a CSV file
        report_filename = f"{timestamp}_email_report.csv"
        report_path = os.path.join(REPORT_FOLDER, report_filename)

        report_df = pd.DataFrame(report)
        report_df.to_csv(report_path, index=False)
        # return f"Emails sent successfully! Report saved: {report_path}"
        return { 
            "status": "COMPLETED", 
            "total": total_emails, 
            "success": success_count, 
            "failed": failure_count, 
            "pending": total_emails - (success_count + failure_count), 
            "report": report_filename 
        }
    except Exception as e:
        return {"status": "FAILURE", "message": str(e)}
