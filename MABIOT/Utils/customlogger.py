import logging

import logging

default_message = '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'  # date format


# Define ANSI color codes
class LogColors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# Color formatter class


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: LogColors.BLUE,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.MAGENTA,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, LogColors.WHITE)
        message = super().format(record)
        return f'{color}{message}{LogColors.RESET}'

# Updated function with color support


def setupCustomLogger(name, filename=None, format=default_message, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler with color
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            ColorFormatter(format, datefmt=date_format))
        logger.addHandler(stream_handler)

        # File handler without color
        if filename:
            file_handler = logging.FileHandler(filename, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter(format, datefmt=date_format))
            logger.addHandler(file_handler)

    return logger
