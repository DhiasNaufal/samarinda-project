from enum import Enum

class LogType(Enum):
  INFO = "Informasi"
  WARNING = "Peringatan"
  ERROR = "Eror"
  NONE = ""

class TextType(Enum):
  STRING = "str"
  INT = "int"
  FLOAT = "float"

class FileType(Enum):
  ALL_FILES = "All Files (*)"
  GEOJSON = "GeoJSON Files (*.geojson)"
  TIFF = "TIFF Files (*.tif *.tiff)"

class FileInputType(Enum):
  FILENAME = "filename"
  FILEPATH = "filepath"
  DIRECTORY = "directory"