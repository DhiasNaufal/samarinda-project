import datetime
from pathlib import Path

def get_current_time() -> str:
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def get_filename(filepath: str, ext: bool = True):
    filename = Path(filepath).name
    if not ext:
        filename = filename.split(".")[0]
    return filename

def get_string_date():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    return formatted_time

def get_file_extension(filepath: str = ""):
    splitted = filepath.lower().split(".")
    
    return splitted[len(splitted)-1]

def calculate_time_diff(start_date, end_date):
    # Calculate time difference in seconds
    time_diff = (end_date - start_date).total_seconds()
    
    # Convert to hours, minutes, seconds
    hours = int(time_diff // 3600)
    minutes = int((time_diff % 3600) // 60)
    seconds = int(time_diff % 60)
    
    # Format as HH:MM:SS
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return formatted_time

