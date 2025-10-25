"""Telegram bot for running the word similarity game."""

import logging
import os
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.game.main import WordGame, WordManager, load_words
from src.shared.embedding_client import EmbeddingClient

# Define keyboards
START_KEYBOARD = ReplyKeyboardMarkup([["/start"]], resize_keyboard=True, one_time_keyboard=True)
STOP_KEYBOARD = ReplyKeyboardMarkup([["/stop"]], resize_keyboard=True)
DIFFICULTY_KEYBOARD = ReplyKeyboardMarkup([["Easy", "Medium", "Hard"]], resize_keyboard=True)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Store active games and clients
active_games: Dict[int, tuple[WordGame, WordManager, EmbeddingClient]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id

    if user_id in active_games:
        await update.message.reply_text(
            "You already have an active game! Use /stop to end it first.",
            reply_markup=STOP_KEYBOARD,
        )
        return

    # Load words and initialize game components
    words = load_words("dicts/german/top1000.csv")
    word_manager = WordManager(words, target_words_count=5)

    # Create a new client for this game
    client = EmbeddingClient(api_url=os.getenv("EMBEDDING_SERVICE_URL"))
    await client.__aenter__()  # Initialize the client

    game = WordGame(word_manager, client)
    active_games[user_id] = (game, word_manager, client)

    # Initialize the game
    word_manager.init_game()
    current_words = word_manager.get_current_words()

    await update.message.reply_text(
        f"Welcome to the Word Similarity Game! Try to find words similar to these:\n\n"
        f"{', '.join(current_words)}\n\n"
        "Just type an English word to play!",
        reply_markup=STOP_KEYBOARD,
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the current game."""
    user_id = update.effective_user.id

    if user_id in active_games:
        game, word_manager, client = active_games[user_id]
        await client.__aexit__(None, None, None)  # Properly close the client
        del active_games[user_id]
        await update.message.reply_text(
            "Game stopped. Use /start to begin a new game!", reply_markup=START_KEYBOARD
        )
    else:
        await update.message.reply_text(
            "You don't have an active game. Use /start to begin!", reply_markup=START_KEYBOARD
        )


async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's word submission."""
    user_id = update.effective_user.id

    if user_id not in active_games:
        await update.message.reply_text(
            "You don't have an active game. Use /start to begin!", reply_markup=START_KEYBOARD
        )
        return

    game, word_manager, client = active_games[user_id]
    user_word = update.message.text.strip().lower()

    try:
        result = await game.play_round(user_word)

        # Prepare response message
        response = [
            f"Your word: {user_word}",
            "\nSimilarities:",
            *[f"{word}: {sim:.3f}" for word, sim in result.similarities.items()],
            f"\nRemoved words: {', '.join(result.removed_words) if result.removed_words else 'None'}",
            f"Added words: {', '.join(result.added_words) if result.added_words else 'None'}",
            f"\nCurrent words: {', '.join(result.current_words)}",
        ]

        if result.game_over:
            response.append("\nGame Over! All words have been seen!")
            game, word_manager, client = active_games[user_id]
            await client.__aexit__(None, None, None)  # Properly close the client
            del active_games[user_id]

        await update.message.reply_text("\n".join(response))

    except Exception as e:
        logger.error(f"Error processing word: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your word. Please try again."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Word Similarity Game Commands:\n\n"
        "/start - Start a new game\n"
        "/stop - Stop the current game\n"
        "/help - Show this help message\n\n"
        "To play, simply type English words that you think are similar to the shown words. "
        "The more similar your word is to the target words, the more likely they are to be removed "
        "and replaced with new ones!"
    )
    # If no active game, show start button, otherwise show stop button
    keyboard = STOP_KEYBOARD if update.effective_user.id in active_games else START_KEYBOARD
    await update.message.reply_text(help_text, reply_markup=keyboard)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
