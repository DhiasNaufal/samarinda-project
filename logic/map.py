from shapely import Geometry
from typing import Sequence

import folium
import webbrowser
import ee

class Map:
  def __init__(self, location: Sequence[float], zoom_start: int = 12) -> None:
    self.map = None
    self.name = "Sentinel 2 Masked"

    self.create_map(location, zoom_start)

  def create_map(self, location: Sequence[float], zoom_start: int):
    self.map = folium.Map(location=location, zoom_start=zoom_start)

  def add_ee_layer(self, ee_image_object) -> None:
    """Adds a method for displaying Earth Engine image tiles to folium map."""
    rgb_vis = { 'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2'] }

    map_id_dict = ee.Image(ee_image_object).getMapId(rgb_vis)

    # Print tile URL for debugging
    print(f"Tile URL for {self.name}: {map_id_dict['tile_fetcher'].url_format}")

    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=self.name,
        overlay=True,
        control=True
    ).add_to(self.map)

  def add_roi_layer(self, geom: Geometry) -> None:
    folium.GeoJson(geom, name="ROI").add_to(self.map)
    
    # add LayerControl immediately
    self.map.add_child(folium.LayerControl())

  def save_and_open_map(self, map_path: str = "sentinel_map.html") -> None:
    self.map.save(map_path)
    webbrowser.open(map_path)