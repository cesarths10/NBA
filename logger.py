import csv
from datetime import datetime
import os

from zoneinfo import ZoneInfo

LOG_FILE = "login_activity.csv"

def log_login(username):
    timestamp = datetime.now(ZoneInfo("US/Arizona")).strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Username", "Action"])
        writer.writerow([timestamp, username, "Login"])
