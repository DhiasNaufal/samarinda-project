import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import argparse
import rasterio
import matplotlib.pyplot as plt

# Konfigurasi awal
os.environ["SM_FRAMEWORK"] = "tf.keras"
num_classes = 4

# Warna Kelas (RGB)
colors = {
    'ground': [167, 168, 167],  # Abu-abu
    'hutan': [21, 194, 59],     # Hijau
    'palmoil': [46, 15, 15],    # Coklat
    'vegetation': [102, 237, 69]  # Hijau terang
}

class_colors = list(colors.values())

# ================================
# 1️⃣ Normalisasi dan Loading Gambar
# ================================

def normalize_image(image):
    return image.astype(np.float32) / 255.0

def load_image(image_path, selected_bands=[1, 2, 3]):
    if image_path.lower().endswith((".tif", ".tiff")):
        with rasterio.open(image_path) as src:
            print(f"📷 Membaca TIFF: {image_path}")
            print(f"🛰 Jumlah band tersedia: {src.count}")

            if src.count < 3:
                raise ValueError("Gambar memiliki kurang dari 3 band, tidak bisa diolah sebagai RGB.")

            print(f"🎯 Band yang digunakan sebagai RGB: {selected_bands}")
            image = np.stack([src.read(b) for b in selected_bands], axis=-1)

            if image.dtype != np.uint8:
                image = np.clip(image / image.max() * 255, 0, 255).astype(np.uint8)
    else:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Gambar tidak ditemukan: {image_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print("📷 Membaca gambar format JPG/PNG (RGB default)")

    # plt.figure(figsize=(6, 6))
    # plt.imshow(image)
    # plt.title("Gambar Input (RGB)")
    # plt.axis("off")
    # plt.show()

    return image, image.shape[:2]  # (H, W)

'''
Perbedaan nya di sini mas
'''

# def load_image(image_path):
#     image = cv2.imread(image_path)
#     if image is None:
#         raise ValueError(f"Gambar tidak ditemukan: {image_path}")
#     return image, image.shape[:2]  # (H, W)

# ================================
# 2️⃣ Patching dengan Overlap
# ================================

'''
Perbedaan nya di sini mas
'''

def extract_patches(image, patch_size=256, overlap=128):
    h, w, c = image.shape
    step = patch_size - overlap
    patches = []
    positions = []

    for y in range(0, h, step):
        for x in range(0, w, step):
            patch = image[y:y+patch_size, x:x+patch_size]
            h_patch, w_patch = patch.shape[:2]

            if h_patch < patch_size or w_patch < patch_size:
                patch_padded = np.zeros((patch_size, patch_size, 3), dtype=np.uint8)
                patch_padded[:h_patch, :w_patch] = patch
                patch = patch_padded

            patches.append(patch)
            positions.append((y, x))

    return np.array(patches), positions, (h, w)

# ================================
# 3️⃣ Prediksi Patch
# ================================

def predict_patched_image(model, image_path, patch_size=256, overlap=128):
    image, original_size = load_image(image_path)
    patches, positions, padded_size = extract_patches(image, patch_size, overlap)
    
    predictions = []

    for patch in patches:
        patch_input = normalize_image(patch)
        patch_input = np.expand_dims(patch_input, axis=0)
        prediction = model.predict(patch_input)
        predicted_mask = np.argmax(prediction, axis=-1)[0]
        predictions.append(predicted_mask)

    predictions = np.array(predictions)
    reconstructed_mask = reconstruct_from_patches(predictions, positions, padded_size, patch_size, overlap)

    return reconstructed_mask[:original_size[0], :original_size[1]]

# ================================
# 4️⃣ Rekonstruksi Blending
# ================================

def reconstruct_from_patches(patches, positions, padded_size, patch_size=256, overlap=128):
    h, w = padded_size
    step = patch_size - overlap

    reconstructed = np.zeros((h, w), dtype=np.float32)
    weight = np.zeros((h, w), dtype=np.float32)

    for index, ((y, x), patch) in enumerate(zip(positions, patches)):
        h_patch, w_patch = patch.shape

        h_patch = min(h_patch, h - y)
        w_patch = min(w_patch, w - x)

        alpha = np.ones((h_patch, w_patch), dtype=np.float32)
        if x > 0:
            alpha[:, :min(overlap, w_patch)] *= np.linspace(0.2, 1, min(overlap, w_patch))[None, :]
        if y > 0:
            alpha[:min(overlap, h_patch), :] *= np.linspace(0.2, 1, min(overlap, h_patch))[:, None]

        reconstructed[y:y+h_patch, x:x+w_patch] += patch[:h_patch, :w_patch] * alpha
        weight[y:y+h_patch, x:x+w_patch] += alpha

    reconstructed /= np.maximum(weight, 1)

    reconstructed = np.clip(reconstructed, 0, num_classes - 1).astype(np.uint8)

    return reconstructed

# ================================
# 5️⃣ Dekoding Mask 
# ================================

def decode_segmentation_mask(mask):
    seg_img = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    
    for i, color in enumerate(class_colors):
        seg_img[mask == i] = color
    
    return seg_img

# ================================
# 6️⃣ Simpan Hasil
# ================================

def save_result(mask, output_path):
    seg_img = decode_segmentation_mask(mask)
    cv2.imwrite(output_path, cv2.cvtColor(seg_img, cv2.COLOR_RGB2BGR))
    print(f"Hasil segmentasi disimpan di: {output_path}")

# ================================
# 7️⃣ Main Execution
# ================================

def main(image_path, model_path, output_path):
    print("Memuat model...")
    model = load_model(model_path, compile=False)
    
    print("Melakukan prediksi...")
    mask = predict_patched_image(model, image_path)
    
    print("Menyimpan hasil segmentasi...")
    save_result(mask, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str, required=True, help="Path ke gambar input")
    parser.add_argument('--model', type=str, default="logic/classification/model/best_model_100e.h5", help="Path ke model terlatih")
    parser.add_argument('--output', type=str, default="output.png", help="Path untuk menyimpan hasil")
    args = parser.parse_args()
    
    main(args.image, args.model, args.output)
