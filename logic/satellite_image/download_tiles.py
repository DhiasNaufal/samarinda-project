import requests
import mercantile
import rasterio
import numpy as np

from io import BytesIO
from PIL import Image
from shapely.geometry import Polygon
from PyQt6.QtCore import QThread, QObject, pyqtSignal
from typing import Optional
from rasterio.transform import from_origin, Affine
from pyproj import CRS, Transformer

from .tile_providers import TILE_PROVIDERS
from utils.common import get_file_extension

Image.MAX_IMAGE_PIXELS = None
class DownloadTiles(QThread):
    error_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()

    def __init__(
            self, 
            tile_provider: str,
            zoom_level: int,
            polygon: Polygon,
            output_path: str,
            parent: Optional[QObject] = None
        ) -> None:
        super().__init__(parent)
        self.zoom = zoom_level
        self.polygon = polygon
        self.output_path = output_path

        self.tile_provider = tile_provider
        self.tile_url = next((tile_provider["url"] for tile_provider in TILE_PROVIDERS if tile_provider["name"] == self.tile_provider), None)

    def run(self):
        try:
            merged_image, tile_range = self.download_tiles()   
            cropped_image = self.crop_image(merged_image, tile_range)

            if get_file_extension(self.output_path) == "tif":
                self.save_as_tiff(cropped_image)
            else:
                cropped_image.save(self.output_path) 
            
            self.finish_signal.emit()   
        except Exception as e:
            self.error_signal.emit(str(e))

    def tile_to_quadkey(self, x, y):
        """Convert tile coordinates to a Bing Maps quadkey."""
        quadkey = ""
        for i in range(self.zoom, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if (x & mask) != 0:
                digit += 1
            if (y & mask) != 0:
                digit += 2
            quadkey += str(digit)
        return quadkey

    def get_tile_bounds(self):
        """Get the tile range (x, y) covering the polygon at a given zoom level."""
        min_lng, min_lat, max_lng, max_lat = self.polygon.bounds

        # Convert lat/lon bounds to tile indices
        top_left_tile = mercantile.tile(min_lng, max_lat, self.zoom)
        bottom_right_tile = mercantile.tile(max_lng, min_lat, self.zoom)

        # Get tile range
        x_min, y_min = top_left_tile.x, top_left_tile.y
        x_max, y_max = bottom_right_tile.x, bottom_right_tile.y

        return x_min, x_max, y_min, y_max

    def download_tile(self, x, y):
        """Download a single tile from the server."""
        if self.tile_provider == "Bing Maps":
            quadkey = self.tile_to_quadkey(x, y)
            url = self.tile_url.format(quadkey=quadkey)
        else:
            url = self.tile_url.format(x=x, y=y, z=self.zoom)

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            print(f"Failed to download tile {x},{y} at zoom {self.zoom}")
            return None

    def download_tiles(self):
        """Download all tiles covering the polygon and merge them into a single image."""
        x_min, x_max, y_min, y_max = self.get_tile_bounds()

        tiles = []
        for y in range(y_min, y_max + 1):
            row_tiles = []
            for x in range(x_min, x_max + 1):
                tile = self.download_tile(x, y)
                if tile:
                    row_tiles.append(tile)
            if row_tiles:
                tiles.append(row_tiles)

        if not tiles:
            raise ValueError("No tiles downloaded!")

        # Merge tiles into a single image
        tile_width, tile_height = tiles[0][0].size  # 256x256 by default
        self.tile_size = tile_width
        merged_width = (x_max - x_min + 1) * self.tile_size
        merged_height = (y_max - y_min + 1) * self.tile_size

        merged_image = Image.new("RGB", (merged_width, merged_height))
        for row_idx, row in enumerate(tiles):
            for col_idx, tile in enumerate(row):
                merged_image.paste(tile, (col_idx * tile_width, row_idx * tile_height))

        return merged_image, (x_min, y_min, x_max, y_max)

    def lonlat_to_pixel(self, lon, lat, tile_range):
        """Convert lat/lon to pixel coordinates in the merged image."""
        x_min, y_min, _, _ = tile_range

        tile = mercantile.tile(lon, lat, self.zoom)
        xtile, ytile = tile.x, tile.y
        bbox = mercantile.bounds(xtile, ytile, self.zoom)

        # Convert lon/lat to pixel coordinates within the tile
        px = int(((lon - bbox.west) / (bbox.east - bbox.west)) * self.tile_size)
        py = int(((bbox.north - lat) / (bbox.north - bbox.south)) * self.tile_size)

        # Convert to pixel coordinates in the merged image
        px += (xtile - x_min) * self.tile_size
        py += (ytile - y_min) * self.tile_size

        return px, py

    def crop_image(self, image, tile_range):
        """Crop the merged image to the exact polygon shape."""
        # Convert polygon to pixel coordinates
        poly_pixels = [self.lonlat_to_pixel(lon, lat, tile_range) for lon, lat in self.polygon.exterior.coords]

        # Get bounding box in pixel coordinates
        x_coords, y_coords = zip(*poly_pixels)
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # Crop the image to the bounding box
        cropped_image = image.crop((x_min, y_min, x_max, y_max))

        return cropped_image
    
    def get_utm_crs(self, lon, lat):
        """Menentukan EPSG UTM berdasarkan koordinat longitude dan latitude."""
        utm_zone = int((lon + 180) / 6) + 1
        is_southern = lat < 0  # Cek apakah di belahan bumi selatan
        epsg_code = 32700 + utm_zone if is_southern else 32600 + utm_zone
        return epsg_code
    
    def save_as_tiff(self, image):
        """Menyimpan gambar yang telah di-crop sebagai GeoTIFF dengan CRS proyeksi."""

        # Bounding box dari polygon dalam EPSG:4326 (WGS 84)
        lon_min, lat_min, lon_max, lat_max = self.polygon.bounds
        
        # Tentukan EPSG UTM berdasarkan lokasi (Samarinda: UTM 50S, EPSG:32750)
        epsg_code = self.get_utm_crs((lon_min + lon_max) / 2, (lat_min + lat_max) / 2)
        utm_crs = CRS.from_epsg(epsg_code)
        print(f"Using EPSG:{epsg_code}")

        # Transformasi dari WGS 84 ke UTM
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        x_min, y_min = transformer.transform(lon_min, lat_min) # Bottom-left
        x_max, y_max = transformer.transform(lon_max, lat_max) # Top-right

        # Hitung resolusi berdasarkan ukuran tile
        width, height = image.size
        res_x = (x_max - x_min) / width # pixel resolution
        res_y = (y_max - y_min) / height # pixel resolution
        transform = Affine(
            res_x, 0, x_min,  # Scale X, Shear X, Origin X (Top-left X)
            0, -res_y, y_max  # Shear Y, Scale Y (Negative), Origin Y (Top-left Y)
        )

        # Konversi gambar menjadi array numpy
        image_array = np.array(image)

        # Pastikan gambar memiliki 3 band (RGB)
        if len(image_array.shape) == 2:
            image_array = np.expand_dims(image_array, axis=2)  # Ubah grayscale ke RGB
        if image_array.shape[2] == 4:  # Jika ada alpha channel, hapus
            image_array = image_array[:, :, :3]

        # Simpan sebagai GeoTIFF dengan CRS yang sesuai
        with rasterio.open(
            self.output_path,
            "w",
            driver="GTiff",
            height=image_array.shape[0],
            width=image_array.shape[1],
            count=3,  # RGB
            dtype=image_array.dtype,
            crs=utm_crs.to_wkt(),  # CRS dalam format WKT
            transform=transform
        ) as dst:
            for i in range(3):  # Simpan masing-masing band RGB
                dst.write(image_array[:, :, i], i + 1)

        print(f"Saved: {self.output_path} with EPSG:{epsg_code}")