"""Word similarity game using embedding model."""

import asyncio
import random
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel

from src.shared.embedding_client import EmbeddingClient
from src.utils.logger import get_logger
from src.data.loader import load_words, load_config

logger = get_logger(__name__)


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
        self.target_words_count = target_words_count
        self.total_score = 0
        self.deck: List[int] = []
        self.rng = random.Random()
        logger.info(
            f"WordManager initialized with {len(all_words)} words, target count: {target_words_count}"
        )

    def get_available_words(self) -> Dict[int, str]:
        """Get words that haven't been seen yet."""
        available = {k: v for k, v in self.all_words.items() if k not in self.seen_words}
        logger.debug(f"Found {len(available)} available words.")
        return available

    def init_game(self, seed: str | int | None = None) -> None:
        """Initialize the game with random words using optional seed."""
        # Setup RNG
        self.rng = random.Random(seed)

        # Create a deterministic deck
        # 1. Get all IDs
        all_ids = sorted(list(self.all_words.keys()))
        # 2. Shuffle deterministically
        self.rng.shuffle(all_ids)
        # 3. Store as deck
        self.deck = all_ids

        if not self.deck:
            logger.error("No words available to start the game. Please check the word list.")
            raise ValueError("No words available to start the game!")

        # Draw initial words
        num_initial = min(self.target_words_count, len(self.deck))
        self.current_words = set(self.deck[:num_initial])
        self.deck = self.deck[num_initial:]

        self.seen_words = set(self.current_words)

        logger.info(
            f"Game initialized with seed={seed}, words: {self.get_current_words()} (IDs: {list(self.current_words)})"
        )

    def get_current_words(self) -> List[str]:
        """Get list of current words in play."""
        words = [self.all_words[k] for k in self.current_words]
        logger.debug(f"Current words in play: {words}")
        return words

    def process_guess(
        self, similarities: List[float], threshold: float = 0.5, max_remove: int = 3
    ) -> Tuple[List[str], List[str], int]:
        """Process user's guess and update game state.

        Args:
            similarities: List of similarity scores for current words
            threshold: Minimum similarity score to consider a match
            max_remove: Maximum number of words to remove

        Returns:
            tuple: (removed_words, added_words, round_score)
        """
        logger.debug(
            f"Processing guess with similarities: {similarities}, threshold: {threshold}, max_remove: {max_remove}"
        )
        # Sort words by similarity
        word_scores = list(zip(self.current_words, similarities))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        logger.debug(
            f"Sorted word scores: {[(self.all_words[w_id], score) for w_id, score in word_scores]}"
        )

        # Remove most similar words
        removed_ids = set()
        # Re-apply similarity check in main.py
        for word_id, score in word_scores:
            if score > 0.98:
                logger.info(
                    f"Guess too similar (score: {score}) to '{self.all_words[word_id]}'. Rejected."
                )
                raise ValueError(
                    f"Word is already on screen or too similar to '{self.all_words[word_id]}'."
                )

            if len(removed_ids) >= max_remove:
                logger.debug(
                    f"Max removal limit ({max_remove}) reached. Stopping further removals."
                )
                break
            if score < threshold:
                logger.debug(
                    f"Word '{self.all_words[word_id]}' (score: {score}) below threshold ({threshold}). Stopping further removals."
                )
                break
            removed_ids.add(word_id)
            logger.debug(f"Word '{self.all_words[word_id]}' (score: {score}) marked for removal.")

        # Update current words
        self.current_words -= removed_ids

        # Calculate score
        round_score = 0
        for word_id, score in word_scores:
            if word_id in removed_ids:
                round_score += int(score * 100)

        self.total_score += round_score

        # Add new random words
        removed_words = [self.all_words[k] for k in removed_ids]
        new_words = self._add_random_words()
        logger.info(
            f"Processed guess. Removed words: {removed_words}, Added words: {new_words}, Round score: {round_score}, Total score: {self.total_score}"
        )

        return removed_words, new_words, round_score

    def _add_random_words(self) -> List[str]:
        """Add random words from the deck to maintain target count."""
        needed = self.target_words_count - len(self.current_words)
        logger.debug(f"Need to add {needed} words.")
        if needed <= 0:
            logger.debug("No new words needed to maintain target count.")
            return []

        if not self.deck:
            logger.warning("No more words in the deck to add.")
            return []

        num_to_add = min(needed, len(self.deck))
        new_ids = set(self.deck[:num_to_add])
        self.deck = self.deck[num_to_add:]

        self.current_words.update(new_ids)
        self.seen_words.update(new_ids)

        added_words = [self.all_words[k] for k in new_ids]
        logger.info(
            f"Added {len(added_words)} new words: {added_words} (IDs: {list(new_ids)}) to maintain target count."
        )
        return added_words

    def is_game_over(self) -> bool:
        """Check if all words have been seen."""
        # Game is over if deck is empty AND we have cleared current words (or purely if deck is empty? User logic seems to imply clearing everything)
        # Original logic: len(get_available_words()) == 0.
        # With deck: available words are just those in the deck.
        game_over = len(self.deck) == 0 and len(self.current_words) == 0
        # Start logic used available=0 -> game over.
        # But if deck is empty but we still have words on screen, we play until screen is clear?
        # Let's match original intent: "No available words to add" -> Eventually clear screen.
        # Actually the original code strictly checked available words (hidden words).
        # Let's say game over if deck is empty.
        # Wait, if deck is empty, you can still match words on screen!
        # Original: `game_over = len(self.get_available_words()) == 0`
        # `get_available_words` was all_words - seen_words.
        # If I have 5 words on screen, seen=5. total=100. available=95.
        # If I match all 100, then seen=100. available=0.
        # So yes, game over is when deck is empty AND current_words is empty?
        # Or just when we can't add more?
        # Usually Solitaire ends when you can't make moves, but here we can make moves if words are on screen.
        # So game over should be when deck is empty AND current words are gone (or unmatchable, but we don't check unmatchable yet).
        # Let's stick to: Deck empty means no new words.

        # Re-reading original: `game_over = len(self.get_available_words()) == 0`.
        # `available` means "in the bag".
        # If bag is empty, `is_game_over` returns True immediately?
        # That would mean you can't finish the last 5 words. That seems like a bug in original or I misunderstood.
        # In main loop: `while not word_manager.is_game_over():`.
        # If bag is empty, loop breaks. You never play the last 5 words.
        # I should probably fix this to be "Deck empty AND current words empty".

        return len(self.deck) == 0 and len(self.current_words) == 0


class GameState(BaseModel):
    """Game state response model."""

    current_words: List[str]
    removed_words: List[str]
    added_words: List[str]
    similarities: Dict[str, float]
    round_score: int
    total_score: int
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
        logger.info(f"WordGame initialized with similarity threshold: {similarity_threshold}")

    async def calculate_similarities(self, user_word: str, target_words: List[str]) -> List[float]:
        """Calculate similarities between user's word and target words."""
        logger.info(
            f"Calculating similarities for user word '{user_word}' against target words: {target_words}"
        )
        similarities = await self.embedding_client.get_similarities(user_word, target_words)
        logger.info(f"Similarities calculated for '{user_word}': {similarities}")
        return similarities

    async def play_round(self, user_word: str) -> GameState:
        """Play one round of the game."""
        logger.info(f"Starting game round with user word: '{user_word}'")
        current_words = self.manager.get_current_words()
        logger.debug(f"Current words in play for similarity calculation: {current_words}")
        similarities = await self.calculate_similarities(user_word, current_words)

        removed_words, added_words, round_score = self.manager.process_guess(
            similarities, threshold=self.threshold
        )
        logger.info(
            f"Round finished. Words removed: {removed_words}, Words added: {added_words}, Score: {round_score}"
        )

        return GameState(
            current_words=self.manager.get_current_words(),
            removed_words=removed_words,
            added_words=added_words,
            similarities=dict(zip(current_words, similarities)),
            round_score=round_score,
            total_score=self.manager.total_score,
            game_over=self.manager.is_game_over(),
        )


async def main():
    """Run an example game."""
    logger.info("Starting word game example.")
    # Load words
    config = load_config()
    words = load_words(config["data"]["default_dict"])

    # Initialize game components
    async with EmbeddingClient() as client:
        word_manager = WordManager(words, target_words_count=5)
        game = WordGame(word_manager, client)

        # Start game
        word_manager.init_game()
        initial_words = word_manager.get_current_words()
        logger.info(f"Game started with initial words: {initial_words}")
        print("Starting words:", initial_words)

        # Game loop
        while not word_manager.is_game_over():
            user_input = input("\nEnter an English word (or 'quit' to exit): ")
            logger.debug(f"User input: '{user_input}'")
            if user_input.lower() == "quit":
                logger.info("User quit the game.")
                break

            result = await game.play_round(user_input)

            print("\nYour word:", user_input)
            print("\nSimilarities:")
            for word, sim in result.similarities.items():
                print(f"{word}: {sim:.3f}")
            print("\nRemoved words:", result.removed_words)
            print("Added words:", result.added_words)
            print(f"Round Score: {result.round_score}")
            print(f"Total Score: {result.total_score}")
            print("\nCurrent words:", result.current_words)

            if result.game_over:
                logger.info("Game Over! All available words have been seen!")
                print("\nGame Over! All words have been seen!")
                break


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Word game example finished.")
