import json
import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash
from werkzeug.utils import secure_filename
from tasks import send_bulk_emails
from celery.result import AsyncResult
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Increase max request size to 20MB
MEGABYTE = 20 * 1024 * 1024  # 20MB
app.config['MAX_CONTENT_LENGTH'] = MEGABYTE
app.config['MAX_FORM_MEMORY_SIZE'] = 50 * MEGABYTE

app.secret_key = os.getenv("SECRET_KEY")
# print(app.secret_key or os.urandom(24).hex())

EMAIL_DETAILS_FILE = "email_details.json"

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
REPORT_FOLDER = os.getenv("REPORT_FOLDER", "reports")
ATTACHMENT_FOLDER = os.getenv("ATTACHMENT_FOLDER", "attachments")

ALLOWED_EXTENSIONS = {"csv", "xlsx"}  # Allowed file types
# ALLOWED_ATTACHMENT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "txt", "docx"}  # Allowed attachment types

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(ATTACHMENT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if the uploaded file is allowed (CSV or XLSX)."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_email_details(subject, body_format, body):
    """Save the latest email details to a file (overwrite each time)"""
    if not body_format:  # Default to 'rtf' if no format is provided
        body_format = "rtf"

    emaildata = {
        "subject": subject,
        "body_format": body_format,
        "body": body
    }
    
    # Save latest email data to file (overwrite previous entry)
    with open(EMAIL_DETAILS_FILE, "w") as file:
        json.dump(emaildata, file, indent=4)

def load_email_details():
    """Read stored email_details from the JSON file"""
    if os.path.exists(EMAIL_DETAILS_FILE):
        with open(EMAIL_DETAILS_FILE, "r") as file:
            try:
                email_data = json.load(file)
                return (
                    email_data.get("subject", ""),
                    email_data.get("body_format", "rtf"),
                    email_data.get("body", "")
                )
            except json.JSONDecodeError:
                return "", "rtf", ""  # Return default values if JSON is corrupted
    return "", "rtf", ""  # Default values if the file does not exist

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            file = request.files["file"]
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{original_filename}"  # Add timestamp
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)

                EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
                EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
                EMAIL_FROM = os.getenv("EMAIL_FROM")
                subject = request.form["subject"]
                body_format = request.form["body_format"]  # Get selected format
                # Get email body based on format
                if body_format == "rtf":
                    body = request.form["rtf_body"]  # Get RTF content (HTML from Quill)
                else:
                    body = request.form["body"]

                # Handle Attachments
                attachment_paths = []
                if "attachments" in request.files:
                    attachments = request.files.getlist("attachments")
                    for attachment in attachments:
                        # if attachment.filename and allowed_file(attachment.filename, ALLOWED_ATTACHMENT_EXTENSIONS):
                        if attachment.filename:
                            attachment_filename = secure_filename(attachment.filename)
                            attachment_path = os.path.join(ATTACHMENT_FOLDER, f"{timestamp}_{attachment_filename}")
                            attachment.save(attachment_path)
                            attachment_paths.append(attachment_path)

                # Save the email details locally
                save_email_details(subject, body_format, body)

                # Call Celery task
                task = send_bulk_emails.apply_async(args=[file_path, EMAIL_FROM, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, subject, body, body_format, timestamp, attachment_paths])

                return redirect(url_for("task_status", task_id=task.id))
            else:
                flash("Invalid file type! Only CSV and XLSX files are allowed.", "error")
                return redirect(url_for("index"))
        except Exception as e:
            flash(str(e), "error")
    # Load latest email details
    subject, body_format, body = load_email_details()
    return render_template("index.html", subject=subject, body_format=body_format, body=body)

@app.route("/task/<task_id>")
def task_status(task_id):
    return render_template("task_status.html", task_id=task_id)

@app.route("/task_status/<task_id>")
def get_task_status(task_id):
    task = AsyncResult(task_id)
    response = {"status": task.status}

    if task.state == "PROGRESS":
        response.update(task.info)
    elif task.state == "SUCCESS":
        response.update(task.info)

    return jsonify(response)

@app.route("/all_reports")
def all_reports():
    """Fetch all report files, extract timestamp, and format date."""
    reports = []
    for filename in os.listdir(REPORT_FOLDER):
        match = re.search(r"(\d{8}_\d{6})\_email_report.csv", filename)
        if match:
            timestamp_str = match.group(1)
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            reports.append({"filename": filename, "timestamp": timestamp})
    reports.sort(key=lambda x: x["timestamp"], reverse=True)  # Sort by newest first
    return render_template("all_reports.html", reports=reports)

@app.route("/download/<filename>")
def download_report(filename):
    report_path = os.path.join(REPORT_FOLDER, filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    return "Report not found.", 404

if __name__ == "__main__":
    app.run(debug=True)
