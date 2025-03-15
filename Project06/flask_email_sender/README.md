## Install Python Packages
`pip install -r .\requirements.txt`

## Start Redis Server

- To start the Redis, run the following command
`redis-server`

- Run the following command to check if Redis is active:
🔹 On Windows (Command Prompt or PowerShell)
`netstat -ano | findstr :6379`

then the result shows like below
TCP    127.0.0.1:65179        127.0.0.1:6379         SYN_SENT        5856

- To Stop a process is already using port 6379, find the PID (Process ID  ex:5856) and stop it:
`taskkill /PID <your_PID> /F` (ex: taskkill /PID 5856 /F)



### Start Celery Worker in background

- To start the Celery Worker in background, run the following command
`celery -A celery_worker worker --loglevel=info`

- Run Celery with the solo execution mode:
`celery -A celery_worker worker --loglevel=info --pool=solo`
💡 Use this for testing/debugging since it's single-threaded.

- If you want concurrency while still using Windows, use thread-based execution:
`celery -A celery_worker worker --loglevel=info --pool=threads`
💡 Use this if you need to process multiple emails in parallel.


### Run Flask app

- To start the Flask app, run the following command
`python app.py`