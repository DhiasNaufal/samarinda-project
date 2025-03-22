import requests
from shapely.geometry import Polygon
from io import BytesIO
from PIL import Image
import mercantile

from PyQt6.QtCore import QThread, QObject
from typing import Optional
from .tile_providers import TILE_PROVIDERS


class DownloadTiles(QThread):
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
        merged_image, tile_range = self.download_tiles()   
        cropped_image = self.crop_image(merged_image, tile_range)
        cropped_image.save(self.output_path)     

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
        merged_width = (x_max - x_min + 1) * tile_width
        merged_height = (y_max - y_min + 1) * tile_height

        merged_image = Image.new("RGB", (merged_width, merged_height))
        for row_idx, row in enumerate(tiles):
            for col_idx, tile in enumerate(row):
                merged_image.paste(tile, (col_idx * tile_width, row_idx * tile_height))

        return merged_image, (x_min, y_min, x_max, y_max)

    def lonlat_to_pixel(self, lon, lat, tile_range):
        """Convert lat/lon to pixel coordinates in the merged image."""
        x_min, y_min, _, _ = tile_range
        tile_size = 256

        tile = mercantile.tile(lon, lat, self.zoom)
        xtile, ytile = tile.x, tile.y
        bbox = mercantile.bounds(xtile, ytile, self.zoom)

        # Convert lon/lat to pixel coordinates within the tile
        px = int(((lon - bbox.west) / (bbox.east - bbox.west)) * tile_size)
        py = int(((bbox.north - lat) / (bbox.north - bbox.south)) * tile_size)

        # Convert to pixel coordinates in the merged image
        px += (xtile - x_min) * tile_size
        py += (ytile - y_min) * tile_size

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