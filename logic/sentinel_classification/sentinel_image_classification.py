from PyQt6.QtCore import QThread, QObject, pyqtSignal

from typing import Optional

import os
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.features

from PIL import Image
from rasterio.windows import Window
from keras.models import load_model
from keras.utils import custom_object_scope
from shapely.geometry import shape
from scipy.ndimage import generic_filter

from .unet import SwinTransformerBlock
from .train_model import _masked_sparse_categorical_crossentropy
from .constants import LAND_COVER_CLASSES
from utils.common import resource_path

import numpy as np

class SentinelImageClassification(QThread):
  progress = pyqtSignal(str) 
  error = pyqtSignal(str)
  result = pyqtSignal(dict)

  def __init__(self, image_path: str, tile_size: int = 256, parent: Optional[QObject] = None) -> None:
    super().__init__(parent)

    self.image_path = image_path
    self.tile_size = tile_size

  def load_unet_model(self, model_path):
    with custom_object_scope({
        'SwinTransformerBlock': SwinTransformerBlock,
        '_masked_sparse_categorical_crossentropy': _masked_sparse_categorical_crossentropy
    }):
        return load_model(model_path)            

  def create_colormap(self):
      return {
          0: (0, 0, 0),          # NO_DATA
          1: (167, 168, 167),    # GROUND
          2: (46, 15, 15),       # PALMOIL
          3: (102, 237, 69),     # VEGETASI
      }

  def colored_prediction(self, prediction_mask):
      colormap = self.create_colormap()
      height, width = prediction_mask.shape
      rgb_image = np.zeros((height, width, 3), dtype=np.uint8)

      for class_idx, color in colormap.items():
          mask = prediction_mask == class_idx
          rgb_image[mask] = color

      return rgb_image
      # Image.fromarray(rgb_image).save(output_path_colored)
      # print(f"Hasil prediksi berwarna disimpan di: {output_path_colored}")

  def run(self):
    try:
      # model = load_unet_model(resource_path(os.path.join("logic", "sentinel_classification", "unet_model_2025-04-09_12-12-51.keras")))
      self.progress.emit("Memuat model...")
      self.model = self.load_unet_model(resource_path(os.path.join("logic", "sentinel_classification", "model", "unet_model_2025-04-09_12-12-51.keras")))

      self.progress.emit("Memuat gambar...")
      with rasterio.open(self.image_path, 'r') as src:
        height, width = src.height, src.width
        channels = src.count

        prediction_mask = np.zeros((height, width), dtype=np.uint8)

        for row in range(0, height, self.tile_size):
          for col in range(0, width, self.tile_size):
            self.progress.emit(f"Memproses tile row={row}, col={col}")
            window = Window(col_off=col, row_off=row,
                            width=min(self.tile_size, width - col),
                            height=min(self.tile_size, height - row))
            
            image_tile = src.read(window=window)
            image_tile = np.transpose(image_tile, (1, 2, 0))

            padded = np.zeros((self.tile_size, self.tile_size, channels), dtype=image_tile.dtype)
            padded[:image_tile.shape[0], :image_tile.shape[1], :] = image_tile

            input_tile = np.expand_dims(padded, axis=0)
            pred_tile = self.model.predict(input_tile, verbose=0)
            pred_mask = np.argmax(pred_tile.squeeze(), axis=-1).astype(np.uint8)

            pred_mask = pred_mask[:image_tile.shape[0], :image_tile.shape[1]]
            prediction_mask[row:row + pred_mask.shape[0], col:col + pred_mask.shape[1]] = pred_mask

        # self.result.emit(prediction_mask)
        # image: np.ndarray 
        image = self.colored_prediction(prediction_mask)
        self.progress.emit("Berhasil menyelesaikan proses prediksi...")

        self.progress.emit("Proses klasifikasi selesai...")
        self.result.emit({
            "total_area": None,
            "gdf": 0.0, 
            "meta": 0.0, 
            "class_array": prediction_mask,
            "image": image,
        })
    except Exception as e:
      print(f"Error: {e}")
      self.error.emit(str(e))