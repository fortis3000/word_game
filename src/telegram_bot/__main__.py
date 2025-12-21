"""Telegram bot for launching the Word Similarity Game Web App."""

import os

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    BotCommand,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from src.utils.logger import get_logger
from src.telegram_bot.message_manager import MessageManager

logger = get_logger(__name__)

# Game URL from environment
GAME_URL = os.getenv("GAME_URL", "http://localhost:8080")

message_manager = MessageManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send game launcher button."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /start command.")

    # Create Web App Button
    # Link directly to the game URL, language selection happens in the UI
    play_text = "Play Word Game 🎮"

    keyboard = [[InlineKeyboardButton(play_text, web_app=WebAppInfo(url=GAME_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Simple welcome message
    await update.message.reply_text(
        "Welcome to the Word Context Game! 🎮\n\nClick the button below to start playing.",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /help command.")

    help_text = "Click 'Play Word Game' to open the app and start playing! You can search for words related to a hidden context."

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def post_init(application: Application) -> None:
    """Set up persistent menu commands."""
    commands = [
        BotCommand("start", "Start Game"),
        BotCommand("help", "Help"),
    ]
    await application.bot.set_my_commands(commands)


def main() -> None:
    """Start the bot."""
    logger.info("Telegram bot application starting up.")
    # Create the Application
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    application = Application.builder().token(token).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # No CallbackQueryHandler needed anymore

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot application shutting down.")


if __name__ == "__main__":
    main()
