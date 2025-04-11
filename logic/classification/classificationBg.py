from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import Optional

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

import rasterio
import os

from .process_result import ProcessResult
from utils.common import resource_path

class ClassificationBgProcess(QThread):
    progress = pyqtSignal(str)
    result = pyqtSignal(dict)

    def __init__(self,image_path: str, output_path: str, result_name: str, parent : Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.image_path = image_path
        self.result_name = result_name
        self.output_path = output_path

    def normalize_image(self, image):
        return image.astype(np.float32) / 255.0

    def load_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Gambar tidak ditemukan: {image_path}")
        return image, image.shape[:2]  # (H, W)

    # ================================
    # 2️⃣ Patching dengan Overlap
    # ================================

    def extract_patches(self, image, patch_size=256, overlap=128):
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

    def predict_patched_image(self, model, image_path, patch_size=256, overlap=128):
        image, original_size = self.load_image(image_path)
        patches, positions, padded_size = self.extract_patches(image, patch_size, overlap)
        
        predictions = []

        for patch in patches:
            patch_input = self.normalize_image(patch)
            patch_input = np.expand_dims(patch_input, axis=0)
            prediction = model.predict(patch_input)
            predicted_mask = np.argmax(prediction, axis=-1)[0]
            predictions.append(predicted_mask)

        predictions = np.array(predictions)
        reconstructed_mask = self.reconstruct_from_patches(predictions, positions, padded_size, patch_size, overlap)

        return reconstructed_mask[:original_size[0], :original_size[1]]

    # ================================
    # 4️⃣ Rekonstruksi Blending
    # ================================

    def reconstruct_from_patches(self, patches, positions, padded_size, patch_size=256, overlap=128, num_classes=5):
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

    def decode_segmentation_mask(self, mask):
        # Warna Kelas (RGB)
        colors = {
            'ground': [167, 168, 167],  # Abu-abu
            'hutan': [21, 194, 59],     # Hijau
            'palmoil': [46, 15, 15],    # Coklat
            'urban': [237, 92, 14],     # Orange
            'vegetation': [102, 237, 69]  # Hijau terang
        }

        class_colors = list(colors.values())

        seg_img = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        
        for i, color in enumerate(class_colors):
            seg_img[mask == i] = color
        
        return seg_img

    # ================================
    # 6️⃣ Simpan Hasil
    # ================================

    def save_result(self, mask, output_path):
        # with rasterio.open(self.image_path) as src:
        #     meta = src.meta.copy()
        #     meta.update(dtype=rasterio.uint8)

        seg_img = self.decode_segmentation_mask(mask)
        # # Convert OpenCV (H, W, C) to Rasterio (Bands, H, W)
        # image = np.transpose(image, (2, 0, 1))  # Rearrange dimensions
        # with rasterio.open(output_path, "w", **meta) as dst:
        #     dst.write(image)
        cv2.imwrite(output_path, cv2.cvtColor(seg_img, cv2.COLOR_RGB2BGR))
        # self.progress.emit(f"Hasil segmentasi disimpan di: {output_path}")

    def run(self):
        self.progress.emit("Memuat model...")
        model = load_model(resource_path("best_model_fix.h5"), compile=False)

        self.progress.emit("Melakukan prediksi...")
        mask = self.predict_patched_image(model, self.image_path)
        
        # self.progress.emit("Menyimpan hasil segmentasi...")
        image = self.decode_segmentation_mask(mask)
        self.progress.emit("Berhasil menyelesaikan proses prediksi...")

        self.progress.emit("Hitung luas area...")
        process = ProcessResult(self.image_path, image=image)
        total_area = process.calculate_area()
        self.progress.emit("Proses klasifikasi selesai...")
        self.result.emit({
            "total_area": total_area,
            "gdf": process.gdf, 
            "meta": process.meta, 
            "class_array": process.class_array,
            "image": image,
        })



