from enum import Enum

class LogLevel(Enum):
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
  PNG = 'PNG FILES (*.png *.PNG)'

class FileInputType(Enum):
  FILENAME = "filename"
  FILEPATH = "filepath"
  DIRECTORY = "directory"

class LayoutDirection(Enum):
  VERTICAL = "vertical"
  HORIZONTAL = "horizontal"

class ColorOptions(Enum):
  BLACK = "#000000"
  RED = "#FF0000"
  Yellow = "#FFFF00"
  WHITE = "#FFFFFF"
  LIGHT_GRAY = "#F0F0F0"
  MEDIUM_GRAY = "#E0E0E0"