import rasterio

from typing import Union
from rasterio.plot import reshape_as_image
from sklearn.model_selection import train_test_split
from .constants import INPUT_SHAPE, LABEL_SHAPE
from .utils import get_file_paths_for_images_and_labels

import tensorflow as tf

from utils.logger import setup_logger
logger = setup_logger()


def prepare_datasets(batch_size, train_size, images_dir, labels_dir):
    (train_image_paths, val_image_paths, test_image_paths,
     train_label_paths, val_label_paths, test_label_paths) = (
        _split_data_for_training_testing_and_validation(train_size, images_dir, labels_dir))

    train_dataset = _create_tf_datasets(train_image_paths, train_label_paths)
    test_dataset = _create_tf_datasets(test_image_paths, test_label_paths)
    val_dataset = _create_tf_datasets(val_image_paths, val_label_paths)
    train_dataset, val_dataset, test_dataset = _preprocess_datasets(
        train_dataset, val_dataset, test_dataset, batch_size)

    return train_dataset, val_dataset, test_dataset


def _split_data_for_training_testing_and_validation(test_size, images_dir, labels_dir):
    image_paths, label_paths = get_file_paths_for_images_and_labels(images_dir, labels_dir)
    train_image_paths, test_image_paths, train_label_paths, test_label_paths = _train_test_split_paths(
        image_paths, label_paths, test_size)

    val_image_paths, test_image_paths, val_label_paths, test_label_paths = _train_test_split_paths(
        test_image_paths, test_label_paths, test_size)

    logger.info(f'There are {len(train_image_paths)} images in the Training Set')
    logger.info(f'There are {len(val_image_paths)} images in the Validation Set')
    logger.info(f'There are {len(test_image_paths)} images in the Test Set')
    return train_image_paths, val_image_paths, test_image_paths, train_label_paths, val_label_paths, test_label_paths


def _train_test_split_paths(image_paths, label_paths, train_size):  
    train_image_paths, test_image_paths, train_label_paths, test_label_paths = train_test_split(
        image_paths, label_paths, train_size=train_size, random_state=0)
    return train_image_paths, test_image_paths, train_label_paths, test_label_paths


def _create_tf_datasets(image_paths, label_paths):
    image_tf_list = tf.constant(image_paths)
    label_tf_list = tf.constant(label_paths)
    return tf.data.Dataset.from_tensor_slices((image_tf_list, label_tf_list))


# Load and preprocess an image-label pair given their paths
def _load_and_preprocess(image_path, label_path):
    with rasterio.open(image_path.numpy().decode(), 'r') as img_src, \
         rasterio.open(label_path.numpy().decode(), 'r') as lbl_src:
        
        img = img_src.read()  # Baca seluruh band gambar
        img = reshape_as_image(img)
        img = tf.convert_to_tensor(img, dtype=tf.float32)
        img = img / 10000.0  # Normalisasi jika rentang nilai 0-10000

        lbl = lbl_src.read(1)  # Ambil hanya satu band label (grayscale mask)
        lbl = tf.convert_to_tensor(lbl, dtype=tf.uint8)

        # Mask nilai 255 tanpa mengubah kelas 0
        lbl = tf.where(lbl == 255, 0, lbl)  

        lbl = tf.expand_dims(lbl, axis=-1)  # FIX: Tambahkan dimensi channel agar sesuai dengan model

    return img, lbl

# Wrapper function for using 'load_and_preprocess' with TensorFlow operations
def _load_and_preprocess_wrapper(image_path, label_path):
    image, label = tf.py_function(func=_load_and_preprocess, inp=[image_path, label_path],
                                Tout=(tf.float32, tf.uint8))  # Fix: Gunakan uint8

    image.set_shape(INPUT_SHAPE)
    label.set_shape(LABEL_SHAPE)
    return image, label

def _augment(image, label):
    seed = tf.random.uniform(shape=(), maxval=10000, dtype=tf.int32)

    image = tf.image.stateless_random_flip_left_right(image, seed=[seed, 0])
    label = tf.image.stateless_random_flip_left_right(label, seed=[seed, 0])

    image = tf.image.stateless_random_flip_up_down(image, seed=[seed, 1])
    label = tf.image.stateless_random_flip_up_down(label, seed=[seed, 1])

    # brightness & contrast hanya diterapkan ke image (boleh)
    image = tf.image.stateless_random_brightness(image, max_delta=0.1, seed=[seed, 2])
    image = tf.image.stateless_random_contrast(image, lower=0.8, upper=1.2, seed=[seed, 3])

    return image, label


# Preprocess and batch the training, testing, and validation datasets
def _preprocess_datasets(train_dataset, val_dataset, test_dataset, batch_size):
    train_dataset = train_dataset.map(_load_and_preprocess_wrapper, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    train_dataset = train_dataset.map(_augment, num_parallel_calls=tf.data.experimental.AUTOTUNE)  # Augmentasi hanya di train

    test_dataset = test_dataset.map(_load_and_preprocess_wrapper, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    val_dataset = val_dataset.map(_load_and_preprocess_wrapper, num_parallel_calls=tf.data.experimental.AUTOTUNE)

    train_dataset = train_dataset.batch(batch_size)
    test_dataset = test_dataset.batch(batch_size)
    val_dataset = val_dataset.batch(batch_size)

    return train_dataset, val_dataset, test_dataset
