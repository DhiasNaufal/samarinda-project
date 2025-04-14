import os
import numpy as np
import rasterio
from rasterio.windows import Window
from keras.models import load_model
from keras.utils import custom_object_scope
from unet import SwinTransformerBlock
from train_model import _masked_sparse_categorical_crossentropy
from PIL import Image
import geopandas as gpd
from shapely.geometry import shape
import rasterio.features
from constants import LAND_COVER_CLASSES
from scipy.ndimage import generic_filter

# # ================================
# # 1️⃣ Colormap untuk Mask Berwarna
# # ================================

# def create_colormap():
#     return {
#         0: (0, 0, 0),          # NO_DATA
#         1: (167, 168, 167),    # GROUND
#         2: (46, 15, 15),       # PALMOIL
#         3: (102, 237, 69),     # VEGETASI
#     }

# # ================================
# # 2️⃣ Simpan Hasil Warna (.PNG)
# # ================================

# def save_colored_prediction(prediction_mask, output_path_colored):
#     colormap = create_colormap()
#     height, width = prediction_mask.shape
#     rgb_image = np.zeros((height, width, 3), dtype=np.uint8)

#     for class_idx, color in colormap.items():
#         mask = prediction_mask == class_idx
#         rgb_image[mask] = color

#     Image.fromarray(rgb_image).save(output_path_colored)
#     print(f"Hasil prediksi berwarna disimpan di: {output_path_colored}")

# ================================
# 3️⃣ Load Model Swin
# ================================

def load_unet_model(model_path):
    with custom_object_scope({
        'SwinTransformerBlock': SwinTransformerBlock,
        '_masked_sparse_categorical_crossentropy': _masked_sparse_categorical_crossentropy
    }):
        return load_model(model_path)

# ================================
# 4️⃣ Fungsi Filter Mayoritas (untuk smoothing)
# ================================

def majority_filter(values):
    values = values.astype(int)
    values_no_zero = values[values != 0]
    if len(values_no_zero) == 0:
        return values[len(values) // 2]
    counts = np.bincount(values_no_zero)
    return np.argmax(counts)

def smooth_mask(mask, size=5):
    print(f"Melakukan smoothing mask dengan kernel size: {size}x{size}")
    smoothed = generic_filter(mask, majority_filter, size=size, mode='nearest')
    print("Kelas unik setelah smoothing:", np.unique(smoothed))
    return smoothed

# ================================
# 6️⃣ Prediksi Citra
# ================================

def predict_large_image(image_path, model_path, output_path, tile_size=256):
    model = load_unet_model(model_path)

    with rasterio.open(image_path) as src:
        height, width = src.height, src.width
        channels = src.count

        prediction_mask = np.zeros((height, width), dtype=np.uint8)

        for row in range(0, height, tile_size):
            for col in range(0, width, tile_size):
                print(f"Memproses tile row={row}, col={col}")
                window = Window(col_off=col, row_off=row,
                                width=min(tile_size, width - col),
                                height=min(tile_size, height - row))
                
                image_tile = src.read(window=window)
                image_tile = np.transpose(image_tile, (1, 2, 0))

                padded = np.zeros((tile_size, tile_size, channels), dtype=image_tile.dtype)
                padded[:image_tile.shape[0], :image_tile.shape[1], :] = image_tile

                input_tile = np.expand_dims(padded, axis=0)
                pred_tile = model.predict(input_tile, verbose=0)
                pred_mask = np.argmax(pred_tile.squeeze(), axis=-1).astype(np.uint8)

                pred_mask = pred_mask[:image_tile.shape[0], :image_tile.shape[1]]
                prediction_mask[row:row + pred_mask.shape[0], col:col + pred_mask.shape[1]] = pred_mask

        profile = src.profile
        profile.update(dtype=rasterio.uint8, count=1, compress='lzw', nodata=0)

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(prediction_mask, 1)

        print(f"Hasil prediksi disimpan di: {output_path}")

    # output_colored = f"{os.path.splitext(output_path)[0]}_colored.png"
    # save_colored_prediction(prediction_mask, output_colored)
    output_shp = f"{os.path.splitext(output_path)[0]}.shp"

    # Terapkan smoothing sebelum export SHP
    smoothed_mask = smooth_mask(prediction_mask, size=5)
    
    # Validasi kelas akhir (buang kelas tidak valid)
    smoothed_mask[~np.isin(smoothed_mask, [1, 2, 3])] = 0
    save_shapefile_from_mask(smoothed_mask, image_path, output_shp)

# ================================
# 7️⃣ Simpan ke Shapefile
# ================================

def save_shapefile_from_mask(mask, reference_tif, output_shp):
    """
    Mengubah mask menjadi SHP dengan mengabaikan kelas tidak valid.
    """
    with rasterio.open(reference_tif) as src:
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

        gdf.to_file(output_shp)
        print(f"Hasil SHP disimpan di: {output_shp}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Predict large satellite image using trained U-Net model.")
    parser.add_argument("--image-path", type=str, required=True, help="Path to input .tif image.")
    parser.add_argument("--model-path", type=str, default="D:\\samarinda-project\\logic\\sentinel_classification\\unet_model_2025-04-09_12-12-51.keras", help="Path to trained model (.h5).")
    parser.add_argument("--output-path", type=str, required=True, help="Path to save the predicted mask (.tif).")
    parser.add_argument("--tile-size", type=int, default=256, help="Tile size for prediction (default: 256).")

    args = parser.parse_args()

    predict_large_image(args.image_path, args.model_path, args.output_path, args.tile_size)
