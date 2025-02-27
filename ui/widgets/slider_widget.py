from PyQt6.QtWidgets import QWidget, QLabel, QSlider, QVBoxLayout
from PyQt6.QtCore import Qt

class SliderWidget(QWidget):
  def __init__(
      self, 
      label: str = "",
      default_value: int = 0,
      tick_interval: int = 20,
      orientation: Qt.Orientation = Qt.Orientation.Horizontal,
      tick_position: QSlider.TickPosition = QSlider.TickPosition.TicksBelow,
      parent=None
    ):
    super().__init__(parent)

    self.default_label = label
    self.default_value = default_value

    self.init_ui(
      tick_interval,
      tick_position,
      orientation
    )

  def init_ui(
      self,
      tick_interval,
      tick_position,
      orientation
    ):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)    

    self.label = QLabel(f"{self.default_label} {self.default_value}")
    layout.addWidget(self.label)

    self.slider = QSlider()
    self.slider.setOrientation(orientation)
    self.slider.setMinimum(0)
    self.slider.setMaximum(100)
    self.slider.setValue(self.default_value)
    self.slider.setTickInterval(tick_interval)
    self.slider.setTickPosition(tick_position)
    self.slider.valueChanged.connect(self.on_value_changed)
    layout.addWidget(self.slider)

  def on_value_changed(self, value):
    self.label.setText(f"{self.default_label} {value}")

  @property
  def get_value(self):
      return self.slider.value()
