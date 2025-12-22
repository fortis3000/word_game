import pytest
from src.game.main import WordManager


def test_pvp_determinism():
    # Setup a word list
    words = {i: f"word_{i}" for i in range(100)}
    target_count = 5

    # Run 1: Seed "pvp_match_1"
    manager1 = WordManager(words, target_count)
    manager1.init_game(seed="pvp_match_1")
    initial_1 = manager1.get_current_words()
    deck_1_start = list(manager1.deck)

    # Run 2: Seed "pvp_match_1" (Same)
    manager2 = WordManager(words, target_count)
    manager2.init_game(seed="pvp_match_1")
    initial_2 = manager2.get_current_words()
    deck_2_start = list(manager2.deck)

    # Assert initial states identical
    assert initial_1 == initial_2
    assert deck_1_start == deck_2_start

    # Simulate play - remove 1st word
    # Manager 1
    # To simulate removal, we remove from current_words and call _add_random_words
    word_to_remove_1 = initial_1[0]
    # Find ID
    id_to_remove_1 = [k for k, v in words.items() if v == word_to_remove_1][0]
    manager1.current_words.remove(id_to_remove_1)
    added_1 = manager1._add_random_words()

    # Manager 2 - remove SAME word
    word_to_remove_2 = initial_2[0]
    id_to_remove_2 = [k for k, v in words.items() if v == word_to_remove_2][0]
    manager2.current_words.remove(id_to_remove_2)
    added_2 = manager2._add_random_words()

    # Assert refills identical
    assert added_1 == added_2
    assert manager1.get_current_words() == manager2.get_current_words()


def test_pvp_determinism_different_seeds():
    words = {i: f"word_{i}" for i in range(100)}
    target_count = 5

    manager1 = WordManager(words, target_count)
    manager1.init_game(seed="seed_A")
    initial_1 = set(manager1.get_current_words())

    manager2 = WordManager(words, target_count)
    manager2.init_game(seed="seed_B")
    initial_2 = set(manager2.get_current_words())

    # Extremely unlikely to be identical with 100 words
    assert initial_1 != initial_2
