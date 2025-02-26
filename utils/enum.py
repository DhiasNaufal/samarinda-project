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