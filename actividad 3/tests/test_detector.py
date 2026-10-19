import unittest
from src.aiops import evaluate


class CorrelationTests(unittest.TestCase):
    def test_needs_both_signals(self):
        self.assertFalse(evaluate(0.1, 0.05, 0.01, 0.01))
        self.assertFalse(evaluate(0.01, 0.3, 0.01, 0.01))
        self.assertTrue(evaluate(0.1, 0.3, 0.01, 0.01))

    def test_strict_boundary(self):
        self.assertFalse(evaluate(0.03, 0.3, 0.01, 0.01))
        self.assertFalse(evaluate(0.1, 0.2, 0, 0))

    def test_zero_variance_and_no_errors(self):
        self.assertFalse(evaluate(0, 0.3, 0, 0))
        self.assertTrue(evaluate(0.1, 0.3, 0, 0))


if __name__ == '__main__':
    unittest.main()
