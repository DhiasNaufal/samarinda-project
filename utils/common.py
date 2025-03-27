import datetime
from pathlib import Path
import re

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

def is_default_filename(filename, prefix):
    pattern = fr".*[/\\]{re.escape(prefix)} \d{{4}}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])(?:[01][0-9]|2[0-3])(?:[0-5][0-9])(?:[0-5][0-9])\.tif$"
    return bool(re.match(pattern, filename))
