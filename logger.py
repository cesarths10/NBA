import datetime

def log_login(username):
    """Logs the login event to a file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("login_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - User: {username} logged in.\n")
