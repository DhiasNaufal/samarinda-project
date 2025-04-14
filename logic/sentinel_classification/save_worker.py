from PyQt6.QtCore import pyqtSignal, QThread
from scipy.ndimage import generic_filter 
from shapely.geometry import shape

import rasterio
import numpy as np
import geopandas as gpd

from .constants import LAND_COVER_CLASSES
from utils.logger import setup_logger

logger = setup_logger()

class SentinelImageSaveWorker(QThread):
    error = pyqtSignal(str)

    def __init__(self, mode, output_path, reference_tif: str = None, class_array: np.ndarray = None):
        super().__init__()
        self.mode = mode  # "vector" or "raster"
        self.output_path = output_path

        self.class_array = class_array
        self.reference_tif = reference_tif

    def run(self):
        try:
            if self.mode == "vector":
                self.save_shapefile()
            elif self.mode == "raster":
                self.save_geotiff()
            else:
                raise ValueError("Unsupported save mode")
        except Exception as e:
            self.error.emit(str(e))
            logger.critical(f"Error in save worker: {e}")

    def save_geotiff(self):
        with rasterio.open(self.reference_tif) as src:
            profile = src.profile
            profile.update(dtype=rasterio.uint8, count=1, compress='lzw', nodata=0)

            with rasterio.open(self.output_path, "w", **profile) as dst:
                dst.write(self.class_array, 1)
            logger.info(f"GeoTIFF saved: {self.output_path}")

    def majority_filter(self, values):
        values = values.astype(int)
        values_no_zero = values[values != 0]
        if len(values_no_zero) == 0:
            return values[len(values) // 2]
        counts = np.bincount(values_no_zero)
        return np.argmax(counts)

    def smooth_mask(self, mask, size=5):
        logger.info(f"Melakukan smoothing mask dengan kernel size: {size}x{size}")
        smoothed = generic_filter(mask, self.majority_filter, size=size, mode='nearest')
        logger.info("Kelas unik setelah smoothing:", np.unique(smoothed))
        return smoothed


    def save_shapefile(self):
        """
        Mengubah mask menjadi SHP dengan mengabaikan kelas tidak valid.
        """
        # Terapkan smoothing sebelum export SHP
        mask = self.smooth_mask(self.class_array)
        # Validasi kelas akhir (buang kelas tidak valid)
        mask[~np.isin(mask, [1, 2, 3])] = 0

        with rasterio.open(self.reference_tif) as src:
            transform = src.transform
            crs = src.crs

            shapes = []
            class_ids = []
            class_names = []

            for geom, value in rasterio.features.shapes(mask, transform=transform):
                class_value = int(value)
                if class_value not in [1, 2, 3]:
                    continue

                geometry = shape(geom)
                if geometry.is_valid and geometry.area > 0:
                    shapes.append(geometry)
                    class_ids.append(class_value)
                    class_names.append(LAND_COVER_CLASSES.get(class_value, "UNKNOWN"))

            gdf = gpd.GeoDataFrame({
                'class_id': class_ids,
                'class_name': class_names,
                'geometry': shapes
            }, crs=crs)

            gdf.to_file(self.output_path)
            logger.info(f"Hasil SHP disimpan di: {self.output_path}")

    