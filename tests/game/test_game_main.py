from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.game.exceptions import InvalidLanguageError
from src.game.main import GameState, WordGame, WordManager, load_words
from src.shared.embedding_client import EmbeddingClient

# Constants for testing
TEST_TARGET_WORDS_COUNT = 5
TEST_SIMILARITY_THRESHOLD = 0.6
TEST_MAX_REMOVE = 3
TEST_SIMILARITY_HIGH = 0.9
TEST_SIMILARITY_MEDIUM = 0.8
TEST_SIMILARITY_LOW = 0.1
TEST_SIMILARITY_BELOW_THRESHOLD = 0.4
TEST_SIMILARITY_THRESHOLD_ALT = 0.7
TEST_WORD_ID_0 = 0
TEST_WORD_ID_1 = 1
TEST_WORD_ID_2 = 2
TEST_WORD_ID_3 = 3
TEST_WORD_ID_4 = 4
TEST_WORD_ID_5 = 5
TEST_WORD_ID_6 = 6
TEST_WORD_ID_7 = 7
TEST_WORD_ID_8 = 8
TEST_WORD_ID_9 = 9
TEST_TWO_WORDS = 2
TEST_ONE_WORD = 1
TEST_THREE_WORDS = 3
TEST_EIGHT_WORDS = 8
TEST_SIMILARITY_0_3 = 0.3
TEST_SIMILARITY_0_2 = 0.2
TEST_SIMILARITY_0_5 = 0.5


# Fixture for a sample words dictionary
@pytest.fixture
def sample_words():
    return {
        TEST_WORD_ID_0: "apple",
        TEST_WORD_ID_1: "banana",
        TEST_WORD_ID_2: "orange",
        TEST_WORD_ID_3: "grape",
        TEST_WORD_ID_4: "strawberry",
        TEST_WORD_ID_5: "blueberry",
        TEST_WORD_ID_6: "raspberry",
        TEST_WORD_ID_7: "pineapple",
        TEST_WORD_ID_8: "mango",
        TEST_WORD_ID_9: "kiwi",
    }


# --- Tests for load_words function ---
def test_load_words_valid_file(tmp_path):
    # Create a dummy CSV file
    csv_content = "id,word\n0,hello\n1,world"
    file_path = tmp_path / "test_words.csv"
    file_path.write_text(csv_content)
    words = load_words(file_path)
    assert words == {TEST_WORD_ID_0: "hello", TEST_WORD_ID_1: "world"}


def test_load_words_empty_file(tmp_path):
    csv_content = "id,word"
    file_path = tmp_path / "empty_words.csv"
    file_path.write_text(csv_content)
    words = load_words(file_path)
    assert words == {}


def test_load_words_non_existent_file():
    with pytest.raises(FileNotFoundError):
        load_words(Path("non_existent.csv"))


# --- Tests for WordManager class ---
def test_word_manager_init(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    assert manager.all_words == sample_words
    assert manager.target_words_count == TEST_TARGET_WORDS_COUNT
    assert manager.total_score == 0
    assert manager.lives == 5
    assert not manager.current_words
    assert not manager.seen_words


def test_word_manager_get_available_words(sample_words):
    manager = WordManager(sample_words)
    manager.seen_words.add(TEST_WORD_ID_0)  # 'apple'
    available = manager.get_available_words()
    assert TEST_WORD_ID_0 not in available
    assert TEST_WORD_ID_1 in available


def test_word_manager_init_game(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    assert len(manager.current_words) == TEST_TARGET_WORDS_COUNT
    assert manager.current_words.issubset(set(sample_words.keys()))
    assert manager.current_words == manager.seen_words


def test_word_manager_init_game_not_enough_words(sample_words):
    manager = WordManager(
        {TEST_WORD_ID_0: "one", TEST_WORD_ID_1: "two"},
        target_words_count=TEST_TARGET_WORDS_COUNT,
    )
    manager.init_game()
    assert len(manager.current_words) == TEST_TWO_WORDS
    assert len(manager.seen_words) == TEST_TWO_WORDS


def test_word_manager_init_game_no_words_available():
    manager = WordManager({}, target_words_count=TEST_TARGET_WORDS_COUNT)
    with pytest.raises(ValueError, match="No words available to start the game!"):
        manager.init_game()


def test_word_manager_get_current_words(sample_words):
    manager = WordManager(sample_words)
    manager.current_words = {TEST_WORD_ID_0, TEST_WORD_ID_1}
    assert manager.get_current_words() == ["apple", "banana"]


def test_word_manager_process_guess(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    manager.current_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }  # apple, banana, orange, grape, strawberry
    remaining_ids = [TEST_WORD_ID_5, TEST_WORD_ID_6, TEST_WORD_ID_7, TEST_WORD_ID_8, TEST_WORD_ID_9]
    manager.deck = remaining_ids

    manager.seen_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }

    # Similarities: apple (0.9), banana (0.8), orange (0.1)
    similarities = [
        TEST_SIMILARITY_HIGH,
        TEST_SIMILARITY_MEDIUM,
        TEST_SIMILARITY_LOW,
        TEST_SIMILARITY_LOW,
        TEST_SIMILARITY_LOW,
    ]
    removed, added, round_score = manager.process_guess(
        similarities, threshold=TEST_SIMILARITY_THRESHOLD_ALT, max_remove=TEST_ONE_WORD
    )

    assert removed == ["apple"]
    assert len(added) == TEST_ONE_WORD
    assert len(manager.current_words) == TEST_TARGET_WORDS_COUNT
    assert "apple" not in manager.get_current_words()
    assert "banana" in manager.get_current_words()
    assert "orange" in manager.get_current_words()
    assert set(manager.get_current_words()).isdisjoint(set(removed))
    assert set(manager.get_current_words()).issuperset(set(added))
    assert round_score == int(TEST_SIMILARITY_HIGH * 100)
    assert manager.total_score == int(TEST_SIMILARITY_HIGH * 100)


def test_word_manager_process_guess_max_remove_limit(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    manager.current_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }  # apple, banana, orange, grape, strawberry
    remaining_ids = [TEST_WORD_ID_5, TEST_WORD_ID_6, TEST_WORD_ID_7, TEST_WORD_ID_8, TEST_WORD_ID_9]
    manager.deck = remaining_ids

    manager.seen_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }

    # Similarities: apple (0.9), banana (0.8), orange (0.7)
    similarities = [
        TEST_SIMILARITY_HIGH,
        TEST_SIMILARITY_MEDIUM,
        TEST_SIMILARITY_THRESHOLD_ALT,
        TEST_SIMILARITY_LOW,
        TEST_SIMILARITY_LOW,
    ]
    removed, added, round_score = manager.process_guess(
        similarities, threshold=TEST_SIMILARITY_THRESHOLD, max_remove=TEST_TWO_WORDS
    )

    assert len(removed) == TEST_TWO_WORDS
    assert "apple" in removed
    assert "banana" in removed
    assert len(added) == TEST_TWO_WORDS
    assert len(manager.current_words) == TEST_TARGET_WORDS_COUNT
    assert round_score == int(TEST_SIMILARITY_HIGH * 100) + int(TEST_SIMILARITY_MEDIUM * 100)
    assert manager.total_score == int(TEST_SIMILARITY_HIGH * 100) + int(
        TEST_SIMILARITY_MEDIUM * 100
    )


def test_word_manager_process_guess_below_threshold(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    original_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }
    manager.current_words = original_words.copy()  # apple, banana, orange, grape, strawberry
    manager.seen_words = original_words.copy()

    # Similarities: apple (0.4), banana (0.3), orange (0.2)
    similarities = [
        TEST_SIMILARITY_BELOW_THRESHOLD,
        TEST_SIMILARITY_0_3,
        TEST_SIMILARITY_0_2,
        TEST_SIMILARITY_LOW,
        TEST_SIMILARITY_LOW,
    ]
    removed, added, round_score = manager.process_guess(
        similarities, threshold=TEST_SIMILARITY_0_5, max_remove=TEST_MAX_REMOVE
    )

    assert not removed
    assert not added
    assert len(manager.current_words) == TEST_TARGET_WORDS_COUNT
    assert manager.current_words == original_words
    assert round_score == 0
    assert manager.total_score == 0
    assert manager.lives == 4


def test_word_manager_add_random_words(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    # Manually setup deck
    manager.deck = [TEST_WORD_ID_5, TEST_WORD_ID_6, TEST_WORD_ID_7]
    manager.current_words = {TEST_WORD_ID_0, TEST_WORD_ID_1}  # Need 3 more words
    manager.seen_words = {
        TEST_WORD_ID_0,
        TEST_WORD_ID_1,
        TEST_WORD_ID_2,
        TEST_WORD_ID_3,
        TEST_WORD_ID_4,
    }  # Some words already seen

    added = manager._add_random_words()
    assert len(added) == TEST_THREE_WORDS
    assert len(manager.current_words) == TEST_TARGET_WORDS_COUNT
    assert len(manager.seen_words) == TEST_EIGHT_WORDS  # 5 initial + 3 new


def test_word_manager_add_random_words_not_needed(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TWO_WORDS)
    manager.current_words = {TEST_WORD_ID_0, TEST_WORD_ID_1}
    manager.seen_words = {TEST_WORD_ID_0, TEST_WORD_ID_1}
    added = manager._add_random_words()
    assert not added
    assert len(manager.current_words) == TEST_TWO_WORDS


def test_word_manager_add_random_words_no_available(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.current_words = {TEST_WORD_ID_0, TEST_WORD_ID_1}
    manager.seen_words = set(sample_words.keys())  # All words seen
    added = manager._add_random_words()
    assert not added
    assert len(manager.current_words) == TEST_TWO_WORDS


def test_word_manager_is_game_over(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_ONE_WORD)
    manager.current_words = {TEST_WORD_ID_0}
    manager.seen_words = set(sample_words.keys())  # All words seen

    # Deck is empty by default in init, so deck empty = True.
    # Current words not empty. -> Game Over False.
    assert not manager.is_game_over()

    # Now clear current words
    manager.current_words = set()
    assert manager.is_game_over()

    # If deck has words
    manager.deck = [TEST_WORD_ID_1]
    manager.current_words = set()
    assert not manager.is_game_over()


def test_word_manager_is_game_over_lives(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    assert not manager.is_game_over()
    manager.lives = 0
    assert manager.is_game_over()


def test_word_manager_process_guess_success_lives_unchanged(sample_words):
    manager = WordManager(sample_words, target_words_count=TEST_TARGET_WORDS_COUNT)
    manager.init_game(seed=42)
    manager.current_words = {TEST_WORD_ID_0}  # apple

    similarities = [TEST_SIMILARITY_HIGH]  # 0.9 > 0.6

    initial_lives = manager.lives
    manager.process_guess(similarities, threshold=0.6)

    assert manager.lives == initial_lives


# --- Tests for WordGame class ---
@pytest.fixture
def mock_embedding_client():
    mock_client = AsyncMock(spec=EmbeddingClient)
    mock_client.get_similarities.return_value = [
        TEST_SIMILARITY_HIGH,
        TEST_SIMILARITY_MEDIUM,
        TEST_SIMILARITY_LOW,
    ]  # Default return
    return mock_client


@pytest.fixture
def mock_word_manager(sample_words):
    manager = MagicMock(spec=WordManager)
    manager.all_words = sample_words
    manager.get_current_words.return_value = ["apple", "banana", "orange"]
    manager.process_guess.return_value = (["apple"], ["grape"], 90)
    manager.total_score = 90
    manager.lives = 5
    manager.is_game_over.return_value = False
    return manager


def test_word_game_init(mock_word_manager, mock_embedding_client):
    game = WordGame(
        mock_word_manager,
        mock_embedding_client,
        similarity_threshold=TEST_SIMILARITY_THRESHOLD,
    )
    assert game.manager == mock_word_manager
    assert game.embedding_client == mock_embedding_client
    assert game.threshold == TEST_SIMILARITY_THRESHOLD


@pytest.mark.asyncio
async def test_word_game_calculate_similarities(mock_embedding_client):
    # Create a dummy WordManager, not strictly needed for this test but for WordGame init
    manager = MagicMock(spec=WordManager)
    game = WordGame(manager, mock_embedding_client)

    user_word = "fruit"
    target_words = ["apple", "banana"]
    mock_embedding_client.get_similarities.return_value = [
        TEST_SIMILARITY_THRESHOLD_ALT,
        TEST_SIMILARITY_THRESHOLD,
    ]
    similarities = await game.calculate_similarities(user_word, target_words)
    assert similarities == [TEST_SIMILARITY_THRESHOLD_ALT, TEST_SIMILARITY_THRESHOLD]
    mock_embedding_client.get_similarities.assert_called_once_with(user_word, target_words)


@patch("src.game.main.detect_language")
@pytest.mark.asyncio
async def test_word_game_play_round(mock_detect, mock_word_manager, mock_embedding_client):
    mock_detect.return_value = "en"
    game = WordGame(
        mock_word_manager,
        mock_embedding_client,
        similarity_threshold=TEST_SIMILARITY_THRESHOLD,
    )
    user_word = "test_word"

    # Set up mock returns for a specific scenario
    mock_word_manager.get_current_words.side_effect = [
        ["apple", "banana", "orange"],  # First call in calculate_similarities
        ["banana", "orange", "grape"],  # Second call after process_guess
    ]
    mock_embedding_client.get_similarities.return_value = [
        TEST_SIMILARITY_HIGH,
        TEST_SIMILARITY_MEDIUM,
        TEST_SIMILARITY_LOW,
    ]
    mock_word_manager.process_guess.return_value = (["apple"], ["grape"], 90)
    mock_word_manager.total_score = 90
    mock_word_manager.is_game_over.return_value = False

    game_state = await game.play_round(user_word)

    mock_word_manager.get_current_words.assert_called()
    mock_embedding_client.get_similarities.assert_called_once_with(
        user_word, ["apple", "banana", "orange"]
    )
    mock_word_manager.process_guess.assert_called_once_with(
        [TEST_SIMILARITY_HIGH, TEST_SIMILARITY_MEDIUM, TEST_SIMILARITY_LOW],
        threshold=TEST_SIMILARITY_THRESHOLD,
    )
    mock_word_manager.is_game_over.assert_called_once()

    assert isinstance(game_state, GameState)
    assert game_state.current_words == ["banana", "orange", "grape"]
    assert game_state.removed_words == ["apple"]
    assert game_state.added_words == ["grape"]
    assert game_state.similarities == {
        "apple": TEST_SIMILARITY_HIGH,
        "banana": TEST_SIMILARITY_MEDIUM,
        "orange": TEST_SIMILARITY_LOW,
    }
    assert game_state.round_score == 90
    assert game_state.total_score == 90
    assert not game_state.game_over


@patch("src.game.main.detect_language")
@pytest.mark.asyncio
async def test_word_game_play_round_game_over(
    mock_detect, mock_word_manager, mock_embedding_client
):
    mock_detect.return_value = "en"
    game = WordGame(
        mock_word_manager,
        mock_embedding_client,
        similarity_threshold=TEST_SIMILARITY_THRESHOLD,
    )
    user_word = "test_word"

    mock_word_manager.get_current_words.side_effect = [
        ["apple", "banana", "orange"],
        ["banana", "orange", "grape"],
    ]
    mock_embedding_client.get_similarities.return_value = [
        TEST_SIMILARITY_HIGH,
        TEST_SIMILARITY_MEDIUM,
        TEST_SIMILARITY_LOW,
    ]
    mock_word_manager.process_guess.return_value = (["apple"], ["grape"], 90)
    mock_word_manager.total_score = 90
    mock_word_manager.is_game_over.return_value = True  # Game is over

    game_state = await game.play_round(user_word)
    assert game_state.game_over


@patch("src.game.main.detect_language")
@pytest.mark.asyncio
async def test_word_game_play_round_invalid_language(
    mock_detect, mock_word_manager, mock_embedding_client
):
    game = WordGame(mock_word_manager, mock_embedding_client, language="en")
    mock_detect.return_value = "de"  # Detected German

    with pytest.raises(InvalidLanguageError, match="Expected EN, but got DE"):
        await game.play_round("Hallo")

    # Ensure no calls to embedding or manager
    mock_embedding_client.get_similarities.assert_not_called()
    mock_word_manager.process_guess.assert_not_called()


@patch("src.game.main.detect_language")
@pytest.mark.asyncio
async def test_word_game_play_round_valid_language(
    mock_detect, mock_word_manager, mock_embedding_client
):
    game = WordGame(mock_word_manager, mock_embedding_client, language="en")
    mock_detect.return_value = "en"
    # Setup necessary mocks for success path
    mock_word_manager.get_current_words.return_value = ["apple"]
    mock_embedding_client.get_similarities.return_value = [0.1]
    mock_word_manager.process_guess.return_value = ([], [], 0)
    mock_word_manager.is_game_over.return_value = False

    await game.play_round("Hello")

    mock_embedding_client.get_similarities.assert_called()


@patch("src.game.main.detect_language")
@pytest.mark.asyncio
async def test_word_game_play_round_unknown_language(
    mock_detect, mock_word_manager, mock_embedding_client
):
    # If detection fails (returns None), we should allow it
    game = WordGame(mock_word_manager, mock_embedding_client, language="en")
    mock_detect.return_value = None

    mock_word_manager.get_current_words.return_value = ["apple"]
    mock_embedding_client.get_similarities.return_value = [0.1]
    mock_word_manager.process_guess.return_value = ([], [], 0)
    mock_word_manager.is_game_over.return_value = False

    await game.play_round("Hmmmm")

    mock_embedding_client.get_similarities.assert_called()
