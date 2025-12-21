"""Telegram bot for running the word similarity game."""

import os
import re
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update, WebAppInfo, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown

from src.game.main import WordGame, WordManager
from src.data.loader import load_words, load_config
from src.shared.embedding_client import EmbeddingClient
from src.utils.logger import get_logger
from src.telegram_bot.message_manager import MessageManager

# Define keyboards
GAME_URL = os.getenv("GAME_URL", "http://localhost:8001")  # Default to example, user must configure
START_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("Play Word Game", web_app=WebAppInfo(url=GAME_URL))], ["/start"]],
    resize_keyboard=True,
)
STOP_KEYBOARD = ReplyKeyboardMarkup([["/stop"]], resize_keyboard=True)

logger = get_logger(__name__)

# Store active games and clients
active_games: Dict[int, tuple[WordGame, WordManager, EmbeddingClient]] = {}
message_manager = MessageManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /start command.")

    if user_id in active_games:
        logger.warning(
            f"User {user_id} tried to start a new game while one is active. Not starting a new game."
        )
        await update.message.reply_text(
            message_manager.get_message("already_active_game", update.effective_user.language_code),
            reply_markup=STOP_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # Load words and initialize game components
    config = load_config()
    words = load_words(config["data"]["default_dict"])
    word_manager = WordManager(words, target_words_count=5)

    # Create a new client for this game
    client = EmbeddingClient(api_url=os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8000"))
    await client.__aenter__()  # Initialize the client

    game = WordGame(word_manager, client)
    active_games[user_id] = (game, word_manager, client)
    logger.info(f"New game successfully started for user {user_id}.")

    # Initialize the game
    word_manager.init_game()
    current_words = word_manager.get_current_words()
    logger.info(f"Game for user {user_id} initialized with words: {current_words}")

    # Escape words for proper markdown rendering
    current_words_escaped = [escape_markdown(w, version=2) for w in current_words]

    await update.message.reply_text(
        message_manager.get_message(
            "welcome_message",
            update.effective_user.language_code,
            current_words=", ".join(current_words_escaped),
        ),
        reply_markup=STOP_KEYBOARD,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the current game."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /stop command.")

    if user_id in active_games:
        game, word_manager, client = active_games[user_id]

        # Capture stats before closing
        total_score = word_manager.total_score
        seen_count = len(word_manager.seen_words)

        await client.__aexit__(None, None, None)  # Properly close the client
        del active_games[user_id]
        logger.info(f"Game successfully stopped for user {user_id}.")

        summary_text = message_manager.get_message(
            "game_summary",
            update.effective_user.language_code,
            total_score=total_score,
            seen_count=seen_count,
        )

        await update.message.reply_text(
            summary_text,
            reply_markup=START_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        logger.warning(f"User {user_id} tried to stop a game that wasn't active. No game to stop.")
        await update.message.reply_text(
            message_manager.get_message("no_active_game_stop", update.effective_user.language_code),
            reply_markup=START_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's word submission."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    if not update.message.text:
        return
    user_word = update.message.text.strip()

    # Validate input length
    if len(user_word) > 50:
        logger.warning(f"User {user_id} submitted word exceeding length limit: '{user_word}'")
        await update.message.reply_text(
            message_manager.get_message("input_too_long", update.effective_user.language_code),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # Validate characters (alphanumeric, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-ZäöüÄÖÜß\s\-\']+$", user_word):
        logger.warning(f"User {user_id} submitted word with invalid characters: '{user_word}'")
        await update.message.reply_text(
            message_manager.get_message("invalid_characters", update.effective_user.language_code),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    logger.info(f"User {user_id} submitted word: '{user_word}'")

    if user_id not in active_games:
        logger.warning(
            f"User {user_id} submitted word '{user_word}' without an active game. Prompting to start a game."
        )
        await update.message.reply_text(
            message_manager.get_message("no_active_game_play", update.effective_user.language_code),
            reply_markup=START_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    game, word_manager, client = active_games[user_id]

    try:
        result = await game.play_round(user_word)
        logger.info(
            f"Game round played for user {user_id} with word '{user_word}'. Game over: {result.game_over}. "
            f"Removed words: {result.removed_words}, Added words: {result.added_words}"
        )

        # Prepare response message
        lang = update.effective_user.language_code

        # Escape dynamic variables
        user_word_escaped = escape_markdown(user_word, version=2)
        removed_words_escaped = [escape_markdown(w, version=2) for w in result.removed_words]
        added_words_escaped = [escape_markdown(w, version=2) for w in result.added_words]
        current_words_escaped = [escape_markdown(w, version=2) for w in result.current_words]

        removed_words_text = (
            ", ".join(removed_words_escaped)
            if result.removed_words
            else message_manager.get_message("none", lang)
        )
        added_words_text = (
            ", ".join(added_words_escaped)
            if result.added_words
            else message_manager.get_message("none", lang)
        )

        # Choose message key based on whether words were removed
        message_key = "round_result_strike" if result.removed_words else "round_result"

        # Generate feedback
        if result.removed_words:
            feedback = message_manager.get_message(
                "feedback_good", lang, count=len(result.removed_words)
            )
        else:
            feedback = message_manager.get_message("feedback_bad", lang)

        response_text = message_manager.get_message(
            message_key,
            lang,
            feedback=feedback,
            user_word=user_word_escaped,
            removed_words=removed_words_text,
            added_words=added_words_text,
            round_score=result.round_score,
            total_score=result.total_score,
            current_words=", ".join(current_words_escaped),
        )

        if result.game_over:
            response_text += message_manager.get_message("game_over", lang)
            game, word_manager, client = active_games[user_id]
            await client.__aexit__(None, None, None)  # Properly close the client
            del active_games[user_id]
            logger.info(f"Game over for user {user_id}. Game state cleared.")

        logger.debug(f"Sending response to user {user_id}:\n{response_text}")

        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception:
        logger.exception(f"Error processing word '{user_word}' for user {user_id}.")
        await update.message.reply_text(
            message_manager.get_message("error_processing", update.effective_user.language_code),
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /help command.")
    help_text = message_manager.get_message("help_message", update.effective_user.language_code)
    logger.debug(f"Sending help message to user {user_id}:\n{help_text}")
    # If no active game, show start button, otherwise show stop button
    keyboard = STOP_KEYBOARD if update.effective_user.id in active_games else START_KEYBOARD
    await update.message.reply_text(
        help_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


def main() -> None:
    """Start the bot."""
    logger.info("Telegram bot application starting up.")
    # Create the Application
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot application shutting down.")


if __name__ == "__main__":
    main()
