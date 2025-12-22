"""Telegram bot for launching the Word Similarity Game Web App."""

import os

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    BotCommand,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
import uuid
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
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

    play_text = "Play Word Game 🎮"

    # Check for deep linking arguments (seed)
    current_game_url = GAME_URL
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        # Check if argument contains language: seed_lang
        if "_" in arg:
            seed, lang = arg.split("_", 1)
            # Validate simple length check
            if len(seed) < 20:
                separator = "&" if "?" in current_game_url else "?"
                current_game_url = f"{current_game_url}{separator}seed={seed}&lang={lang}"
                logger.info(f"Starting game with seed: {seed}, lang: {lang}")
        else:
            # Fallback for old style simple seed
            seed = arg
            if len(seed) < 20:
                separator = "&" if "?" in current_game_url else "?"
                current_game_url = f"{current_game_url}{separator}seed={seed}"
                logger.info(f"Starting game with seed: {seed}")

    keyboard = [[InlineKeyboardButton(play_text, web_app=WebAppInfo(url=current_game_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Message text
    msg = "Welcome to the Word Context Game! 🎮\n\nClick the button below to start playing."
    if context.args:
        msg = "Welcome to the PvP Challenge! ⚔️\n\nClick below to accept the duel."

    await update.message.reply_text(msg, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested /help command.")

    help_text = "Click 'Play Word Game' to open the app and start playing! You can search for words related to a hidden context."

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query. Triggered when user types @botname ..."""
    query = update.inline_query.query if update.inline_query else ""

    try:
        results = []

        # Scenario 1: Share Score (query starts with "score")
        if query.startswith("score"):
            parts = query.split()
            # Expected format: "score <value> <seed>"
            if len(parts) >= 3:
                score = parts[1]
                seed = parts[2]

                # Get bot username for deep linking
                bot_username = context.bot.username
                if not bot_username:
                    me = await context.bot.get_me()
                    bot_username = me.username

                # Link to play the SAME seed
                deep_link = f"https://t.me/{bot_username}?start={seed}"

                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=f"I scored {score}!",
                        description=f"Can you beat my score on seed {seed}?",
                        input_message_content=InputTextMessageContent(
                            f"I scored *{score}* in the Word Game! 🏆\n\nCan you beat me? 👇"
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Accept Challenge ⚔️", url=deep_link)]]
                        ),
                    )
                )

        # Scenario 2: Default "New Challenge" (empty query or just random typing)
        else:
            # Generate a unique seed for this challenge
            seed = str(uuid.uuid4())[:8]

            # Get bot username for deep linking
            bot_username = context.bot.username
            if not bot_username:
                # Fallback if username not cached yet (shouldn't happen usually)
                me = await context.bot.get_me()
                bot_username = me.username

            # Helper to create result for a language
            def create_lang_result(lang_code, lang_name):
                deep_link = f"https://t.me/{bot_username}?start={seed}_{lang_code}"
                return InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"Challenge in {lang_name}",
                    description=f"Send a {lang_name} PvP invitation",
                    input_message_content=InputTextMessageContent(
                        f"I challenge you to a game of Context ({lang_name})! ⚔️\nCan you beat my score?"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Accept Challenge 🎮", url=deep_link)]]
                    ),
                )

            logger.info(f"Generating language specific inline query results with seed: {seed}")

            results.append(create_lang_result("en", "English"))
            results.append(create_lang_result("de", "German"))
            results.append(create_lang_result("ru", "Russian"))

        await update.inline_query.answer(results, cache_time=0) if update.inline_query else None
    except Exception as e:
        logger.error(f"Error in inline query handler: {e}", exc_info=True)


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
    application.add_handler(InlineQueryHandler(inline_query))
    # No CallbackQueryHandler needed anymore

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot application shutting down.")


if __name__ == "__main__":
    main()
