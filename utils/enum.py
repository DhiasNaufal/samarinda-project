from enum import Enum

class LayoutType(Enum):
  VERTICAL = "vertical"
  HORIZONTAL = "horizontal"

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
  PNG = 'PNG File (*.png *.PNG)'
  SHP = "SHP Files (*.shp *.SHP)"
  JPG = "JPG Files (*.jpg *.jpg)"

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
  LIGHT_BLUE = "#0096C3"
  MEDIUM_BLUE = "#017FA7"