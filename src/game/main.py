"""Word similarity game using embedding model."""

import asyncio
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel

from src.shared.embedding_client import EmbeddingClient


class WordManager:
    """Manages the game state and word selection."""

    def __init__(self, all_words: Dict[int, str], target_words_count: int = 5):
        """Initialize the game manager.

        Args:
            all_words: Dictionary of {id: word} pairs to play with
            target_words_count: Number of words to maintain in the current set
        """
        self.all_words = all_words
        self.current_words: Set[int] = set()
        self.seen_words: Set[int] = set()
        self.target_words_count = target_words_count

    def get_available_words(self) -> Dict[int, str]:
        """Get words that haven't been seen yet."""
        return {k: v for k, v in self.all_words.items() if k not in self.seen_words}

    def init_game(self) -> None:
        """Initialize the game with random words."""
        available = self.get_available_words()
        if not available:
            raise ValueError("No words available to start the game!")

        self.current_words = set(
            random.sample(list(available.keys()), min(self.target_words_count, len(available)))
        )
        self.seen_words.update(self.current_words)

    def get_current_words(self) -> List[str]:
        """Get list of current words in play."""
        return [self.all_words[k] for k in self.current_words]

    def process_guess(
        self, similarities: List[float], threshold: float = 0.5, max_remove: int = 3
    ) -> Tuple[List[str], List[str]]:
        """Process user's guess and update game state.

        Args:
            similarities: List of similarity scores for current words
            threshold: Minimum similarity score to consider a match
            max_remove: Maximum number of words to remove

        Returns:
            tuple: (removed_words, added_words)
        """
        # Sort words by similarity
        word_scores = list(zip(self.current_words, similarities))
        word_scores.sort(key=lambda x: x[1], reverse=True)

        # Remove most similar words
        removed_ids = set()
        for word_id, score in word_scores:
            if len(removed_ids) >= max_remove or score < threshold:
                break
            removed_ids.add(word_id)

        # Update current words
        self.current_words -= removed_ids

        # Add new random words
        removed_words = [self.all_words[k] for k in removed_ids]
        new_words = self._add_random_words()

        return removed_words, new_words

    def _add_random_words(self) -> List[str]:
        """Add random words to maintain target count."""
        needed = self.target_words_count - len(self.current_words)
        if needed <= 0:
            return []

        available = self.get_available_words()
        if not available:
            return []

        new_ids = set(random.sample(list(available.keys()), min(needed, len(available))))
        self.current_words.update(new_ids)
        self.seen_words.update(new_ids)

        return [self.all_words[k] for k in new_ids]

    def is_game_over(self) -> bool:
        """Check if all words have been seen."""
        return len(self.get_available_words()) == 0


class GameState(BaseModel):
    """Game state response model."""

    current_words: List[str]
    removed_words: List[str]
    added_words: List[str]
    similarities: Dict[str, float]
    game_over: bool


class WordGame:
    """Main game logic controller."""

    def __init__(
        self,
        word_manager: WordManager,
        embedding_client: EmbeddingClient,
        similarity_threshold: float = 0.6,
    ):
        self.manager = word_manager
        self.embedding_client = embedding_client
        self.threshold = similarity_threshold

    async def calculate_similarities(self, user_word: str, target_words: List[str]) -> List[float]:
        """Calculate similarities between user's word and target words."""
        return await self.embedding_client.get_similarities(user_word, target_words)

    async def play_round(self, user_word: str) -> GameState:
        """Play one round of the game."""
        current_words = self.manager.get_current_words()
        similarities = await self.calculate_similarities(user_word, current_words)

        removed_words, added_words = self.manager.process_guess(
            similarities, threshold=self.threshold
        )

        return GameState(
            current_words=self.manager.get_current_words(),
            removed_words=removed_words,
            added_words=added_words,
            similarities=dict(zip(current_words, similarities)),
            game_over=self.manager.is_game_over(),
        )


def load_words(filepath: str | Path) -> Dict[int, str]:
    """Load words from a CSV file."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return {i: line.split(",")[1] for i, line in enumerate(lines[1:])}


async def main():
    """Run an example game."""
    # Load words
    words = load_words("dicts/german/top1000.csv")

    # Initialize game components
    async with EmbeddingClient() as client:
        word_manager = WordManager(words, target_words_count=5)
        game = WordGame(word_manager, client)

        # Start game
        word_manager.init_game()
        print("Starting words:", word_manager.get_current_words())

        # Game loop
        while not word_manager.is_game_over():
            word = input("\nEnter an English word (or 'quit' to exit): ")
            if word.lower() == "quit":
                break

            result = await game.play_round(word)

            print("\nYour word:", word)
            print("\nSimilarities:")
            for word, sim in result.similarities.items():
                print(f"{word}: {sim:.3f}")
            print("\nRemoved words:", result.removed_words)
            print("Added words:", result.added_words)
            print("\nCurrent words:", result.current_words)

            if result.game_over:
                print("\nGame Over! All words have been seen!")
                break


if __name__ == "__main__":
    asyncio.run(main())
