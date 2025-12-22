from unittest.mock import AsyncMock, MagicMock
import pytest
from telegram import InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
from src.telegram_bot.__main__ import start, help_command, GAME_URL

# Constants for testing
TEST_USER_ID = 123


@pytest.mark.asyncio
async def test_start_command():
    """Test that the start command sends the Web App button."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.args = []

    await start(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args

    # Check text
    assert "Welcome to the Word Context Game!" in call_args[0][0]

    # Check reply_markup
    reply_markup = call_args[1]["reply_markup"]
    assert isinstance(reply_markup, InlineKeyboardMarkup)

    # Check button details
    button = reply_markup.inline_keyboard[0][0]
    assert button.text == "Play Word Game 🎮"
    assert isinstance(button.web_app, WebAppInfo)
    assert button.web_app.url == GAME_URL


@pytest.mark.asyncio
async def test_start_command_with_seed():
    """Test start command with seed argument (PvP mode)."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    seed = "test-seed-123"
    context.args = [seed]

    await start(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args

    # Check PvP text
    assert "Welcome to the PvP Challenge!" in call_args[0][0]

    # Check WebApp URL has seed
    reply_markup = call_args[1]["reply_markup"]
    button = reply_markup.inline_keyboard[0][0]
    separator = "&" if "?" in GAME_URL else "?"
    expected_url = f"{GAME_URL}{separator}seed={seed}"
    assert button.web_app.url == expected_url


@pytest.mark.asyncio
async def test_help_command():
    """Test the help_command sends the correct help text."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    await help_command(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args

    expected_text = "Click 'Play Word Game' to open the app and start playing! You can search for words related to a hidden context."
    assert expected_text in call_args[0][0]
    assert call_args[1]["parse_mode"] == ParseMode.MARKDOWN
