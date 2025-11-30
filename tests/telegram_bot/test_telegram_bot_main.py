from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.__main__ import (
    START_KEYBOARD,
    STOP_KEYBOARD,
    active_games,
    handle_word,
    help_command,
    start,
    stop,
)

# Constants for testing
TEST_USER_ID = 123
TEST_SIMILARITY_SCORE = 0.5
TEST_TARGET_WORDS_COUNT = 5


@pytest.mark.asyncio
async def test_help_command():
    """Test the help_command function."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    # Test with no active game
    with patch("src.telegram_bot.__main__.active_games", {}):
        await help_command(update, context)
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Word Similarity Game Commands:" in call_args[0][0]
        assert call_args[1]["reply_markup"] == START_KEYBOARD

    update.message.reply_text.reset_mock()

    # Test with an active game
    with patch(
        "src.telegram_bot.__main__.active_games",
        {TEST_USER_ID: (MagicMock(), MagicMock(), MagicMock())},
    ):
        await help_command(update, context)
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Word Similarity Game Commands:" in call_args[0][0]
        assert call_args[1]["reply_markup"] == STOP_KEYBOARD


@pytest.mark.asyncio
async def test_handle_word_valid():
    """Test the handle_word function for a valid word."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.text = "testword"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    mock_game = MagicMock()
    mock_game.play_round = AsyncMock()
    mock_game.play_round.return_value = MagicMock(
        similarities={"word1": TEST_SIMILARITY_SCORE},
        removed_words=["word2"],
        added_words=["word3"],
        current_words=["word1", "word3"],
        game_over=False,
    )

    with patch(
        "src.telegram_bot.__main__.active_games",
        {TEST_USER_ID: (mock_game, MagicMock(), MagicMock())},
    ):
        await handle_word(update, context)

        mock_game.play_round.assert_called_once_with("testword")
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "Your word: testword" in call_args
        assert "Removed words: word2" in call_args
        assert "Added words: word3" in call_args
        assert "Current words: word1, word3" in call_args


@pytest.mark.asyncio
async def test_handle_word_no_active_game():
    """Test the handle_word function when there is no active game."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    with patch("src.telegram_bot.__main__.active_games", {}):
        await handle_word(update, context)

        update.message.reply_text.assert_called_once_with(
            "You don't have an active game. Use /start to begin!",
            reply_markup=START_KEYBOARD,
        )


@pytest.mark.asyncio
async def test_handle_word_game_over():
    """Test the handle_word function when the game is over."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.text = "testword"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    mock_game = MagicMock()
    mock_game.play_round = AsyncMock()
    mock_game.play_round.return_value = MagicMock(
        similarities={"word1": TEST_SIMILARITY_SCORE},
        removed_words=["word2"],
        added_words=["word3"],
        current_words=["word1", "word3"],
        game_over=True,
    )
    mock_client = MagicMock()
    mock_client.__aexit__ = AsyncMock()

    with patch(
        "src.telegram_bot.__main__.active_games",
        {TEST_USER_ID: (mock_game, MagicMock(), mock_client)},
    ):
        await handle_word(update, context)

        mock_game.play_round.assert_called_once_with("testword")
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "Game Over!" in call_args
        assert TEST_USER_ID not in active_games


@pytest.mark.asyncio
async def test_stop_active_game():
    """Test the stop command for an active game."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    mock_client = MagicMock()
    mock_client.__aexit__ = AsyncMock()

    # Simulate an active game for the user
    with patch(
        "src.telegram_bot.__main__.active_games",
        {TEST_USER_ID: (MagicMock(), MagicMock(), mock_client)},
    ):
        await stop(update, context)

        # Assert that the game is stopped and the appropriate message is sent
        update.message.reply_text.assert_called_once_with(
            "Game stopped. Use /start to begin a new game!", reply_markup=START_KEYBOARD
        )
        assert TEST_USER_ID not in active_games


@pytest.mark.asyncio
async def test_stop_no_active_game():
    """Test the stop command when there is no active game."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    with patch("src.telegram_bot.__main__.active_games", {}):
        await stop(update, context)

        # Assert that the appropriate message is sent
        update.message.reply_text.assert_called_once_with(
            "You don't have an active game. Use /start to begin!",
            reply_markup=START_KEYBOARD,
        )


@pytest.mark.asyncio
async def test_start_new_game():
    """Test the start command for a new game."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    with (
        patch("src.telegram_bot.__main__.load_words") as mock_load_words,
        patch("src.telegram_bot.__main__.WordManager") as mock_word_manager,
        patch("src.telegram_bot.__main__.EmbeddingClient") as mock_embedding_client,
        patch("src.telegram_bot.__main__.WordGame") as mock_word_game,
    ):
        # Mock the return values of the patched objects
        mock_load_words.return_value = ["word1", "word2", "word3"]
        mock_word_manager.return_value.get_current_words.return_value = [
            "word1",
            "word2",
        ]
        mock_embedding_client.return_value.__aenter__.return_value = None
        mock_word_manager.return_value.target_words_count = (
            TEST_TARGET_WORDS_COUNT  # Set target_words_count
        )
        mock_word_game.return_value = MagicMock()

        # Call the function to be tested
        await start(update, context)

        # Assert that the reply_text method was called with the welcome message
        update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_start_game_already_active():
    """Test the start command when a game is already active."""
    update = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    # Simulate an active game for the user
    with patch(
        "src.telegram_bot.__main__.active_games",
        {TEST_USER_ID: (MagicMock(), MagicMock(), MagicMock())},
    ):
        await start(update, context)

        # Assert that the appropriate message is sent
        update.message.reply_text.assert_called_once_with(
            "You already have an active game! Use /stop to end it first.",
            reply_markup=STOP_KEYBOARD,
        )
