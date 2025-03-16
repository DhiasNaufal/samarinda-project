import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
from scipy.spatial import cKDTree
from PIL import Image

from utils.common import get_file_extension

def save_vector(gdf: gpd.GeoDataFrame, output_path: str):
  ext = get_file_extension(output_path)
  if ext == "shp":
    gdf.to_file(output_path)
    print(f"Shapefile berhasil disimpan : {output_path}")
  elif ext == "geojson":
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"Geojson file berhasil disimpan : {output_path}")

def save_geotiff(meta, class_array, output_path: str, nodata_value=255):
  meta.update({"dtype": rasterio.uint8, "nodata": nodata_value, "count": 1})
  with rasterio.open(output_path, "w", **meta) as dst:
      dst.write(class_array, 1)
  print(f"GeoTIFF berhasil disimpan: {output_path}")

decoded_classes = {
  (167, 168, 167): 0, 
  (21, 194, 59): 1,
  (46, 15, 15): 2,
  (237, 92, 14): 3,
  (102, 237, 69): 4
}

class_labels = {
    0: 'ground',
    1: 'hutan',
    2: 'palmoil',
    3: 'urban',
    4: 'vegetation'
}

class ProcessResult:
  def __init__(self, input_tif: str, input_png: str):
    self.input_tif = input_tif
    self.input_png = input_png
  
  # def run(self):
    self.meta, self.transform, self.crs = self.load_metadata(self.input_tif)
    segmentasi_array = self.load_segmentation_image(self.input_png)
    self.class_array = self.decode_segmentation(segmentasi_array)
    self.gdf = self.get_gdf()

  def load_metadata(self, input_tif):
    with rasterio.open(input_tif) as src:
        return src.meta.copy(), src.transform, src.crs
    
  def load_segmentation_image(self, input_png):
    image = Image.open(input_png).convert("RGB")
    return np.array(image)
  
  def decode_segmentation(self, segmentasi_array):
    height, width, _ = segmentasi_array.shape
    class_array = np.zeros((height, width), dtype=np.uint8)
    for color, class_id in decoded_classes.items():
        mask = np.all(segmentasi_array == color, axis=-1)
        class_array[mask] = class_id
    return class_array

  def generate_polygons(self):
    shapes_gen = shapes(self.class_array, transform=self.transform)
    polygons, values, labels = [], [], []
    for geom, value in shapes_gen:
        poly = shape(geom).buffer(1).buffer(-1)  
        polygons.append(poly)
        values.append(value)
        labels.append(class_labels.get(value, "Unknown"))
    return polygons, values, labels

  def create_geodataframe(self, polygons, values, labels):
    return gpd.GeoDataFrame({"class": values, "label": labels, "geometry": polygons}, crs=self.crs)

  def interpolate_small_polygons(self, gdf, min_area_threshold=200):
    small_polygons = gdf[gdf.geometry.area < min_area_threshold]
    large_polygons = gdf[gdf.geometry.area >= min_area_threshold]
    if not small_polygons.empty and not large_polygons.empty:
        small_centroids = np.array([geom.centroid.coords[0] for geom in small_polygons.geometry])
        large_centroids = np.array([geom.centroid.coords[0] for geom in large_polygons.geometry])
        tree = cKDTree(large_centroids)
        _, indices = tree.query(small_centroids)
        for small_idx, large_idx in zip(small_polygons.index, indices):
            gdf.at[small_idx, "class"] = large_polygons.iloc[large_idx]["class"]
            gdf.at[small_idx, "label"] = large_polygons.iloc[large_idx]["label"]
    return gdf

  def get_gdf(self):
    polygons, values, labels = self.generate_polygons()
    gdf = self.create_geodataframe(polygons, values, labels)
    gdf = self.interpolate_small_polygons(gdf)

    return gdf

  def calculate_area(self):
    self.gdf["luas"] = self.gdf.geometry.area  
    
    luas_total = self.gdf.groupby("label")["luas"].sum()
    
    # print("\n Total Luas Tiap Kelas:")
    # for label, area in luas_total.items():
    #     print(f" - {label}: {area:.2f} m2")
    
    return luas_total
  
  def save_shapefile(self, output_path: str):
    self.gdf.to_file(output_path)
    print(f"Shapefile berhasil disimpan: {output_path}")

  def save_geotiff(self, output_path: str, nodata_value=255):
    self.meta.update({"dtype": rasterio.uint8, "nodata": nodata_value, "count": 1})
    with rasterio.open(output_path, "w", **self.meta) as dst:
        dst.write(self.class_array, 1)
    print(f"GeoTIFF berhasil disimpan: {output_path}")

if __name__ == "__main__":
   process = ProcessResult(
      input_tif="D:\\samarinda-project\\data\\TEST1.tif",
      input_png="D:\\samarinda-project\output\\Hasil - TEST1-20250315170317.png"
   )
   print(process.calculate_area())

   process.save_shapefile("res.shp")
   process.save_geotiff("res.tif")

