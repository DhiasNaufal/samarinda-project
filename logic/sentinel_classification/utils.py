import os
import glob
from random import randint

from utils.logger import setup_logger
logger = setup_logger()


def get_labels_directory():
    return os.path.join(os.getcwd(), "data", "labels")


def get_images_directory():
    return os.path.join(os.getcwd(), "data", "images")


def _create_file_paths_for_images_and_labels(img_directory, label_directory):
    img_paths = sorted(glob.glob(img_directory + '/*.tif'))
    label_paths = sorted(glob.glob(label_directory + '/*.tif'))
    return img_paths, label_paths


def _get_count_number_of_images_and_labels(images, labels):
    return len(images), len(labels)


def get_number_of_images_and_labels(images_dir, labels_dir):    
    images_directory = get_images_directory() if images_dir is None else images_dir
    labels_directory = get_labels_directory() if labels_dir is None else labels_dir
    
    image_paths, label_paths = _create_file_paths_for_images_and_labels(images_directory, labels_directory)
    return _get_count_number_of_images_and_labels(image_paths, label_paths)


def get_file_paths_for_images_and_labels(images_dir, labels_dir):
    images_directory = get_images_directory() if images_dir is None else images_dir
    labels_directory = get_labels_directory() if labels_dir is None else labels_dir
    
    image_paths, label_paths = _create_file_paths_for_images_and_labels(images_directory, labels_directory)
    number_of_images, number_of_labels = _get_count_number_of_images_and_labels(image_paths, label_paths)

    logger.info(f"There are {number_of_images} images and {number_of_labels} labels in our dataset")
    if number_of_images > 0:
        logger.info(f"An example of an image path is: \n {image_paths[0]}")
        logger.info(f"An example of a mask path is: \n {label_paths[0]}")

    return image_paths, label_paths


