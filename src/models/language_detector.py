from langdetect import detect, LangDetectException
from src.utils.logger import get_logger

logger = get_logger(__name__)


def detect_language(text: str) -> str | None:
    """Detect the language of the given text.

    Args:
        text: The text to analyze.

    Returns:
        The 2-letter language code (e.g., 'en', 'de') or None if detection fails.
    """
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        logger.warning(f"Could not detect language for text: '{text}'")
        return None
