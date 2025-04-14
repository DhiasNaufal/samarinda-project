import tensorflow as tf
import os
from datetime import datetime
from keras.callbacks import ReduceLROnPlateau, ModelCheckpoint
from .data_preprocessing import prepare_datasets
from .plotting import plot_training_results
from .unet import unet_model
from .constants import N_CLASSES

from utils.logger import setup_logger
logger = setup_logger()

logger.info(f"GPU Available: {tf.config.list_physical_devices('GPU')}")

def train_model(input_shape, filters, n_classes, epochs, batch_size, train_size, save_model,
                plot_training_summary, save_training_summary, images_dir, labels_dir):

    model = unet_model(input_shape, filters=filters, n_classes=n_classes)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss=_masked_sparse_categorical_crossentropy, metrics=['accuracy'])

    # Pastikan folder untuk menyimpan model ada
    os.makedirs("model", exist_ok=True)

    best_model_filename = f"model/best_model_{epochs}e_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.keras"
    checkpoint = ModelCheckpoint(best_model_filename, monitor='val_loss', save_best_only=True, mode='min')

    # Lebih stabil dengan val_loss daripada val_accuracy
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=5, verbose=1, min_lr=2e-6)

    train_dataset, val_dataset, test_dataset = prepare_datasets(batch_size, train_size, images_dir, labels_dir)

    history = model.fit(train_dataset,
                        validation_data=val_dataset,
                        epochs=epochs,
                        verbose=1,
                        callbacks=[checkpoint, reduce_lr],
                        shuffle=True)

    if plot_training_summary:
        plot_training_results(history, save_training_summary)

    if save_model:
        model_name = f"model/unet_model_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.keras"
        model.save(model_name)

    return best_model_filename

def _masked_sparse_categorical_crossentropy(y_true, y_pred):
    mask = tf.math.greater(y_true, 0)
    mask_squeezed = tf.squeeze(mask, axis=-1)

    y_true_masked = tf.boolean_mask(y_true, mask_squeezed)
    y_preds_list = [tf.boolean_mask(y_pred[..., i], mask_squeezed) for i in range(y_pred.shape[-1])]
    y_pred_masked = tf.stack(y_preds_list, axis=-1)

    loss = tf.keras.losses.sparse_categorical_crossentropy(y_true_masked, y_pred_masked)
    return tf.reduce_mean(loss)
