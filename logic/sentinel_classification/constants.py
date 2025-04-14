# Constants
TRAIN_SIZE = 0.8
BATCH_SIZE = 16
INPUT_SHAPE = (256, 256, 10)  # 10 bands for input images
LABEL_SHAPE = (256, 256, 1)

FILTERS = 32
N_CLASSES = 4
EPOCHS = 100

# Classes
LAND_COVER_CLASSES = {
            0: "NO_DATA",
            1: "GROUND",
            2: "SAWIT",
            3: "VEGETASI",
        }