import json
import os
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MessageManager:
    def __init__(
        self, locales_path: str = "src/telegram_bot/locales/messages.json", default_lang: str = "en"
    ):
        self.locales_path = locales_path
        self.default_lang = default_lang
        self.messages: dict[str, dict[str, str]] = self._load_messages()

    def _load_messages(self) -> dict[str, dict[str, str]]:
        if not os.path.exists(self.locales_path):
            logger.error(f"Locales file not found at {self.locales_path}")
            return {}

        try:
            with open(self.locales_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading messages from {self.locales_path}: {e}")
            return {}

    def get_message(self, key: str, lang: str = None, **kwargs) -> str:
        if not lang or lang not in self.messages:
            lang = self.default_lang

        # If language is still not found (e.g. default_lang is missing), try 'en'
        if lang not in self.messages:
            lang = "en"

        lang_messages = self.messages.get(lang, {})
        message = lang_messages.get(key)

        if message is None:
            # Fallback to default language if key missing in requested language
            lang_messages = self.messages.get(self.default_lang, {})
            message = lang_messages.get(key)

        if message is None:
            return f"Missing message: {key}"

        try:
            return message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format key {e} for message {key}")
            return message
