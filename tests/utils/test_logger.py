import logging
import sys
from unittest.mock import patch

from src.utils.logger import get_logger


def test_get_logger_returns_logger_instance():
    logger = get_logger()
    assert isinstance(logger, logging.Logger)


def test_get_logger_level():
    logger = get_logger(level=logging.DEBUG)
    assert logger.level == logging.DEBUG


def test_get_logger_handlers_and_formatter():
    logger = get_logger(name="test_logger_handlers")
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream == sys.stdout
    assert isinstance(handler.formatter, logging.Formatter)


def test_get_logger_propagate_false():
    logger = get_logger(name="test_logger_propagate")
    assert logger.propagate is False


def test_get_logger_same_instance_for_same_name():
    logger1 = get_logger(name="my_specific_logger")
    logger2 = get_logger(name="my_specific_logger")
    assert logger1 is logger2


def test_get_logger_different_instance_for_different_name():
    logger1 = get_logger(name="logger_a")
    logger2 = get_logger(name="logger_b")
    assert logger1 is not logger2


def test_get_logger_message_format():
    with patch("sys.stdout") as mock_stdout:
        logger = get_logger(name="test_message_format", level=logging.INFO)
        logger.info("Test message")
        output = mock_stdout.write.call_args[0][0]
        # Check for basic format components: timestamp, levelname, name, message
        assert "INFO test_message_format: Test message" in output
        assert "202" in output  # Check for year in timestamp
