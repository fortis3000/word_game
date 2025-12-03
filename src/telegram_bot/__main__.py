"""Telegram bot for running the word similarity game."""

import asyncio
import os
import re
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.game.main import WordGame, WordManager
from src.data.loader import load_words, load_config
from src.shared.embedding_client import EmbeddingClient
from src.utils.logger import get_logger

# Define keyboards
START_KEYBOARD = ReplyKeyboardMarkup([["/start"]], resize_keyboard=True, one_time_keyboard=True)
STOP_KEYBOARD = ReplyKeyboardMarkup([["/stop"]], resize_keyboard=True)
DIFFICULTY_KEYBOARD = ReplyKeyboardMarkup([["Easy", "Medium", "Hard"]], resize_keyboard=True)

logger = get_logger(__name__)

# Store active games and clients
active_games: Dict[int, tuple[WordGame, WordManager, EmbeddingClient]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /start command.")

    if user_id in active_games:
        logger.warning(
            f"User {user_id} tried to start a new game while one is active. Not starting a new game."
        )
        await update.message.reply_text(
            "⚠️ You already have an active game! Use /stop to end it first.",
            reply_markup=STOP_KEYBOARD,
        )
        return

    # Load words and initialize game components
    config = load_config()
    words = load_words(config["data"]["default_dict"])
    word_manager = WordManager(words, target_words_count=5)

    # Create a new client for this game
    client = EmbeddingClient(api_url=os.getenv("EMBEDDING_SERVICE_URL"))
    await client.__aenter__()  # Initialize the client

    game = WordGame(word_manager, client)
    active_games[user_id] = (game, word_manager, client)
    logger.info(f"New game successfully started for user {user_id}.")

    # Initialize the game
    word_manager.init_game()
    current_words = word_manager.get_current_words()
    logger.info(f"Game for user {user_id} initialized with words: {current_words}")

    await update.message.reply_text(
        f"👋 Welcome to the Word Similarity Game! 🎮\n\n"
        f"🎯 Try to find words similar to these:\n\n"
        f"✨ {', '.join(current_words)} ✨\n\n"
        "⌨️ Just type a German word to play! 🍀",
        reply_markup=STOP_KEYBOARD,
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the current game."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /stop command.")

    if user_id in active_games:
        game, word_manager, client = active_games[user_id]
        await client.__aexit__(None, None, None)  # Properly close the client
        del active_games[user_id]
        logger.info(f"Game successfully stopped for user {user_id}.")
        await update.message.reply_text(
            "🛑 Game stopped. Use /start to begin a new game! 🚀", reply_markup=START_KEYBOARD
        )
    else:
        logger.warning(f"User {user_id} tried to stop a game that wasn't active. No game to stop.")
        await update.message.reply_text(
            "🤔 You don't have an active game. Use /start to begin! 🌟",
            reply_markup=START_KEYBOARD,
        )


async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's word submission."""
    user_id = update.effective_user.id
    user_word = update.message.text.strip()

    # Validate input length
    if len(user_word) > 50:
        logger.warning(f"User {user_id} submitted word exceeding length limit: '{user_word}'")
        await update.message.reply_text(
            "🚫 Your message is too long. Please keep it under 50 characters. 📏"
        )
        return

    # Validate characters (alphanumeric, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z0-9\s\-\']+$", user_word):
        logger.warning(f"User {user_id} submitted word with invalid characters: '{user_word}'")
        await update.message.reply_text(
            "🚫 Invalid characters detected. Please use only letters, numbers, spaces, hyphens, and apostrophes. 🔤"
        )
        return

    user_word = user_word.lower()
    logger.info(f"User {user_id} submitted word: '{user_word}'")

    if user_id not in active_games:
        logger.warning(
            f"User {user_id} submitted word '{user_word}' without an active game. Prompting to start a game."
        )
        await update.message.reply_text(
            "❓ You don't have an active game. Use /start to begin! 🚀",
            reply_markup=START_KEYBOARD,
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
        response_lines = [
            f"📝 Your word: {user_word}",
            "\n📊 Similarities:",
            *[f"{word}: {sim:.3f}" for word, sim in result.similarities.items()],
            f"\n✨ Removed words: {', '.join(result.removed_words) if result.removed_words else 'None'}",
            f"🆕 Added words: {', '.join(result.added_words) if result.added_words else 'None'}",
            f"\n🏆 Round Score: {result.round_score}",
            f"🌟 Total Score: {result.total_score}",
            f"\n📋 Current words: {', '.join(result.current_words)}",
        ]

        if result.game_over:
            response_lines.append("\n🎉 Game Over! All words have been seen! 🏆")
            game, word_manager, client = active_games[user_id]
            await client.__aexit__(None, None, None)  # Properly close the client
            del active_games[user_id]
            logger.info(f"Game over for user {user_id}. Game state cleared.")

        response_text = "\n".join(response_lines)
        logger.debug(f"Sending response to user {user_id}:\n{response_text}")

        message = await update.message.reply_text(response_text)

        if result.removed_words:
            # Animation sequence
            # Step 1: Strikethrough
            await asyncio.sleep(1)
            response_lines_strike = [
                f"📝 Your word: {user_word}",
                "\n📊 Similarities:",
                *[f"{word}: {sim:.3f}" for word, sim in result.similarities.items()],
                f"\n✨ Removed words: {'~' + ', '.join(result.removed_words) + '~'}",
                f"🆕 Added words: {', '.join(result.added_words) if result.added_words else 'None'}",
                f"\n🏆 Round Score: {result.round_score}",
                f"🌟 Total Score: {result.total_score}",
                f"\n📋 Current words: {', '.join(result.current_words)}",
            ]
            if result.game_over:
                response_lines_strike.append("\n🎉 Game Over! All words have been seen! 🏆")
            await message.edit_text("\n".join(response_lines_strike))

            # Step 2: Explosion
            await asyncio.sleep(1)
            response_lines_explode = [
                f"📝 Your word: {user_word}",
                "\n📊 Similarities:",
                *[f"{word}: {sim:.3f}" for word, sim in result.similarities.items()],
                "\n✨ Removed words: 💥",
                f"🆕 Added words: {', '.join(result.added_words) if result.added_words else 'None'}",
                f"\n🏆 Round Score: {result.round_score}",
                f"🌟 Total Score: {result.total_score}",
                f"\n📋 Current words: {', '.join(result.current_words)}",
            ]
            if result.game_over:
                response_lines_explode.append("\n🎉 Game Over! All words have been seen! 🏆")
            await message.edit_text("\n".join(response_lines_explode))

            # Step 3: Gone/Dust
            await asyncio.sleep(1)
            response_lines_final = [
                f"📝 Your word: {user_word}",
                "\n📊 Similarities:",
                *[f"{word}: {sim:.3f}" for word, sim in result.similarities.items()],
                "\n✨ Removed words: 💨",
                f"🆕 Added words: {', '.join(result.added_words) if result.added_words else 'None'}",
                f"\n🏆 Round Score: {result.round_score}",
                f"🌟 Total Score: {result.total_score}",
                f"\n📋 Current words: {', '.join(result.current_words)}",
            ]
            if result.game_over:
                response_lines_final.append("\n🎉 Game Over! All words have been seen! 🏆")
            await message.edit_text("\n".join(response_lines_final))

    except Exception:
        logger.exception(f"Error processing word '{user_word}' for user {user_id}.")
        await update.message.reply_text(
            "😵‍💫 Sorry, there was an error processing your word. Please try again. 🔄"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /help command.")
    help_text = (
        "📚 Word Similarity Game Commands:\n\n"
        "🟢 /start - Start a new game\n"
        "🛑 /stop - Stop the current game\n"
        "ℹ️ /help - Show this help message\n\n"
        "🎮 To play, simply type English words that you think are similar to the shown words. "
        "The more similar your word is to the target words, the more likely they are to be removed "
        "and replaced with new ones! 🍀"
    )
    logger.debug(f"Sending help message to user {user_id}:\n{help_text}")
    # If no active game, show start button, otherwise show stop button
    keyboard = STOP_KEYBOARD if update.effective_user.id in active_games else START_KEYBOARD
    await update.message.reply_text(help_text, reply_markup=keyboard)


def main() -> None:
    """Start the bot."""
    logger.info("Telegram bot application starting up.")
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

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
