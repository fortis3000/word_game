"""Telegram bot for launching the Word Similarity Game Web App."""

import os
import json

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
    MessageHandler,
    filters,
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

    # Check for deep linking arguments (seed)
    current_game_url = GAME_URL
    if context.args and len(context.args) > 0:
        seed = context.args[0]
        # Validate seed is safe (alphanumeric check handled by Telegram usually, but good to be safe)
        if len(seed) < 20:  # Simple length check
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


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle data sent from the Web App (score sharing)."""
    if not update.effective_message or not update.effective_message.web_app_data:
        return

    try:
        data = json.loads(update.effective_message.web_app_data.data)
        score = data.get("score", 0)
        seed = data.get("seed", "random")

        logger.info(f"Received web app data: score={score}, seed={seed}")

        # Create a button to share the score via inline query
        # We use a specific prefix "score" to distinguish from normal challenges
        query_text = f"score {score} {seed}"

        keyboard = [
            [InlineKeyboardButton("Share Score 📢", switch_inline_query=query_text)],
            [InlineKeyboardButton("Play Again 🔄", web_app=WebAppInfo(url=GAME_URL))],
        ]

        await update.message.reply_text(
            f"Game Over! 🏁\n\nYou scored: *{score}*\n\nShare your result with your friends!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Error processing web app data: {e}", exc_info=True)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query. Triggered when user types @botname ..."""
    query = update.inline_query.query

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

            deep_link = f"https://t.me/{bot_username}?start={seed}"

            logger.info(f"Generating inline query result with deep link: {deep_link}")

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="⚔️ Challenge Friend",
                    description="Send a PvP invitation",
                    input_message_content=InputTextMessageContent(
                        "I challenge you to a game of Context! ⚔️\nCan you beat my score?"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Accept Challenge 🎮", url=deep_link)]]
                    ),
                )
            )

        await update.inline_query.answer(results, cache_time=0)
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
    # Handle Web App Data (Sent when user clicks Share Score in the Game)
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    # No CallbackQueryHandler needed anymore

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot application shutting down.")


if __name__ == "__main__":
    main()
