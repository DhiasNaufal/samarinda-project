import datetime
from pathlib import Path

def get_current_time() -> str:
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def get_filename(filepath: str):
    return Path(filepath).name