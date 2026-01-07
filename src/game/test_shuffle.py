import unittest
from src.game.main import WordManager

class TestShuffle(unittest.TestCase):
    def setUp(self):
        # minimal mock words
        self.words = {i: f"word{i}" for i in range(20)}
        self.manager = WordManager(self.words, target_words_count=5)
        self.manager.init_game(seed="test")  # Deterministic

    def test_shuffle_insufficient_score(self):
        self.manager.total_score = 100
        with self.assertRaises(ValueError) as cm:
            self.manager.shuffle_active_words()
        self.assertIn("Not enough score", str(cm.exception))

    def test_shuffle_success(self):
        self.manager.total_score = 300
        initial_words = self.manager.get_current_words()
        
        self.manager.shuffle_active_words()
        
        # Check score deduction
        self.assertEqual(self.manager.total_score, 100)
        
        # Check words changed
        new_words = self.manager.get_current_words()
        self.assertNotEqual(set(initial_words), set(new_words))
        
        # Check still has target count
        self.assertEqual(len(new_words), 5)

if __name__ == '__main__':
    unittest.main()
