# logger.py
import logging

def setup_logger(name='dev'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Console handler only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger
