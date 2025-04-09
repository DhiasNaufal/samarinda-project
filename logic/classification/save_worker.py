from PyQt6.QtCore import pyqtSignal, QThread
from utils.common import get_file_extension
import rasterio

class SaveWorker(QThread):
    error = pyqtSignal(str)

    def __init__(self, mode, output_path, gdf=None, meta=None, class_array=None, nodata_value=255):
        super().__init__()
        self.mode = mode  # "vector" or "raster"
        self.output_path = output_path
        self.gdf = gdf
        self.meta = meta
        self.class_array = class_array
        self.nodata_value = nodata_value

    def run(self):
        try:
            if self.mode == "vector":
                self.save_vector()
            elif self.mode == "raster":
                self.save_geotiff()
            else:
                raise ValueError("Unsupported save mode")
        except Exception as e:
            self.error.emit(str(e))

    def save_vector(self):
        ext = get_file_extension(self.output_path)
        if ext == "shp":
            self.gdf.to_file(self.output_path)
        elif ext == "geojson":
            self.gdf.to_file(self.output_path, driver="GeoJSON")
        else:
            raise ValueError("Unsupported vector file format")
        print(f"Vector file saved: {self.output_path}")

    def save_geotiff(self):
        self.meta.update({
            "dtype": rasterio.uint8,
            "nodata": self.nodata_value,
            "count": 1
        })
        with rasterio.open(self.output_path, "w", **self.meta) as dst:
            dst.write(self.class_array, 1)
        print(f"GeoTIFF saved: {self.output_path}")