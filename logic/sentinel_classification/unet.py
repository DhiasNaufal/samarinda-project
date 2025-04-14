from keras.layers import Activation, Input, Conv2D, MaxPooling2D, BatchNormalization, Conv2DTranspose, concatenate, LayerNormalization, Layer, Dropout, Dense, MultiHeadAttention
from keras.models import Model
from tensorflow import Tensor
import tensorflow as tf


# --- Swin Transformer Block ---
class SwinTransformerBlock(Layer):
    def __init__(self, num_heads, embed_dim, **kwargs):
        super(SwinTransformerBlock, self).__init__(**kwargs)
        self.num_heads = num_heads
        self.embed_dim = embed_dim

    def build(self, input_shape):
        self.norm1 = LayerNormalization(epsilon=1e-5)
        self.attn = MultiHeadAttention(num_heads=self.num_heads, key_dim=self.embed_dim)
        self.norm2 = LayerNormalization(epsilon=1e-5)
        self.mlp = tf.keras.Sequential([
            Dense(self.embed_dim, activation='gelu'),
            Dense(self.embed_dim)
        ])

    def call(self, x):
        B, H, W, C = tf.shape(x)[0], tf.shape(x)[1], tf.shape(x)[2], tf.shape(x)[3]
        x_flat = tf.reshape(x, [B, H * W, C])  # Patch flattening

        shortcut = x_flat
        x_flat = self.norm1(x_flat)
        x_flat = self.attn(x_flat, x_flat)
        x_flat = shortcut + x_flat

        x_flat = self.norm2(x_flat)
        x_flat = self.mlp(x_flat)

        x = tf.reshape(x_flat, [B, H, W, C])  # Restore to spatial shape
        return x

    def get_config(self):
        config = super().get_config()
        config.update({
            "num_heads": self.num_heads,
            "embed_dim": self.embed_dim
        })
        return config


# --- Encoding Block ---
def _encoding_block(inputs: Tensor, filters: int, max_pooling=True):
    C = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(inputs)
    C = BatchNormalization()(C)
    C = Activation("relu")(C)

    C = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(C)
    C = BatchNormalization()(C)
    C = Activation("relu")(C)
    skip_connection = C

    if max_pooling:
        next_layer = MaxPooling2D(pool_size=(2, 2))(C)
    else:
        next_layer = C
    return next_layer, skip_connection


# --- Decoding Block ---
def _decoding_block(inputs: Tensor, skip_connection_input: Tensor, filters: int):
    CT = Conv2DTranspose(filters, 3, strides=(2, 2), padding="same", kernel_initializer="he_normal")(inputs)
    residual_connection = concatenate([CT, skip_connection_input], axis=3)
    C = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(residual_connection)
    C = BatchNormalization()(C)
    C = Activation("relu")(C)
    C = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(C)
    C = BatchNormalization()(C)
    C = Activation("relu")(C)
    return C


# --- Full UNet with Swin Transformer bottleneck ---
def unet_model(input_size, filters, n_classes):
    inputs = Input(input_size)

    C1, S1 = _encoding_block(inputs, filters, max_pooling=True)
    C2, S2 = _encoding_block(C1, filters * 2, max_pooling=True)
    C3, S3 = _encoding_block(C2, filters * 4, max_pooling=True)
    C4, S4 = _encoding_block(C3, filters * 8, max_pooling=True)
    C5, _  = _encoding_block(C4, filters * 16, max_pooling=False)

    # Swin Transformer Block on bottleneck
    swin_block = SwinTransformerBlock(num_heads=8, embed_dim=filters * 16)
    C5 = swin_block(C5)

    U6 = _decoding_block(C5, S4, filters * 8)
    U7 = _decoding_block(U6, S3, filters * 4)
    U8 = _decoding_block(U7, S2, filters * 2)
    U9 = _decoding_block(U8, S1, filters)

    C10 = Conv2D(filters, 3, activation='relu', padding='same', kernel_initializer='he_normal')(U9)
    C11 = Conv2D(filters=n_classes, kernel_size=(1, 1), activation='softmax', padding='same')(C10)
    model = Model(inputs=inputs, outputs=C11)

    return model
