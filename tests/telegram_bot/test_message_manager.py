import pytest
import json
from src.telegram_bot.message_manager import MessageManager

# Mock data
MOCK_MESSAGES = {
    "en": {"hello": "Hello, {name}!", "welcome": "Welcome"},
    "de": {"hello": "Hallo, {name}!", "welcome": "Willkommen"},
}


@pytest.fixture
def mock_locales_file(tmp_path):
    locales_file = tmp_path / "messages.json"
    with open(locales_file, "w", encoding="utf-8") as f:
        json.dump(MOCK_MESSAGES, f)
    return str(locales_file)


def test_load_messages(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    assert manager.messages == MOCK_MESSAGES


def test_get_message_en(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    msg = manager.get_message("hello", lang="en", name="World")
    assert msg == "Hello, World!"


def test_get_message_de(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    msg = manager.get_message("hello", lang="de", name="Welt")
    assert msg == "Hallo, Welt!"


def test_get_message_fallback(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    # Requesting 'fr' which is not in mock, should fallback to 'en'
    msg = manager.get_message("welcome", lang="fr")
    assert msg == "Welcome"


def test_get_message_missing_key(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    msg = manager.get_message("missing_key", lang="en")
    assert msg == "Missing message: missing_key"


def test_get_message_missing_format_arg(mock_locales_file):
    manager = MessageManager(locales_path=mock_locales_file)
    # Missing 'name' argument
    msg = manager.get_message("hello", lang="en")
    # Should return unformatted string if formatting fails
    assert msg == "Hello, {name}!"
