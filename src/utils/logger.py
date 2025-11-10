import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger instance.
    Args:
        name (str, optional): Name of the logger. Defaults to None (root logger).
        level (int): Logging level. Defaults to logging.INFO.
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
