from src.models.language_detector import detect_language
from unittest.mock import patch

def test_detect_language_success():
    assert detect_language("This is a longer sentence in English to be sure.") == "en"
    assert detect_language("Das ist ein längerer Satz auf Deutsch.") == "de"
    assert detect_language("Ceci est une phrase plus longue en français.") == "fr"

def test_detect_language_short_text():
    # Short text might be harder, but let's see what langdetect does.
    # Often it returns something.
    assert detect_language("The") == "en"

def test_detect_language_failure():
    # Should handle empty string or weird chars gracefully (return None or raise?)
    # My implementation catches LangDetectException and returns None.
    # langdetect raises LangDetectException on empty string or no features.
    assert detect_language("") is None
    assert detect_language("12345") is None
