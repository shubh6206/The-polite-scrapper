"""
Unit Tests for Price Normalization (Test 1 of Required 5)
"""

import unittest
from src.normalizer import normalize_price


class TestPriceNormalization(unittest.TestCase):
    def test_standard_gbp_price(self):
        """Verify standard £51.77 format normalizes to numeric float 51.77."""
        self.assertEqual(normalize_price("£51.77"), 51.77)
        self.assertIsInstance(normalize_price("£51.77"), float)

    def test_zero_and_integer_prices(self):
        """Verify £0.00 and integer values normalize correctly."""
        self.assertEqual(normalize_price("£0.00"), 0.0)
        self.assertEqual(normalize_price("£25"), 25.0)

    def test_price_with_extra_whitespace(self):
        """Verify prices with irregular spacing or line breaks normalize cleanly."""
        self.assertEqual(normalize_price("   £ 19.95 \n "), 19.95)

    def test_invalid_price_raises_error(self):
        """Verify non-numeric or empty price strings raise ValueError."""
        with self.assertRaises(ValueError):
            normalize_price("")
        with self.assertRaises(ValueError):
            normalize_price("Free")
        with self.assertRaises(ValueError):
            normalize_price("£None")
        with self.assertRaises(ValueError):
            normalize_price("Price on Request")


if __name__ == "__main__":
    unittest.main()
