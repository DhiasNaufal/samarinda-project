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
