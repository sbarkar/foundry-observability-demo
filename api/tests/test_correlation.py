"""
Unit tests for correlation module.
"""
import unittest
from correlation import generate_correlation_id


class TestCorrelation(unittest.TestCase):
    """Test cases for correlation ID generation."""
    
    def test_generate_correlation_id_format(self):
        """Test that correlation ID is a valid UUID."""
        correlation_id = generate_correlation_id()
        
        # UUID format: 8-4-4-4-12 characters
        parts = correlation_id.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)
    
    def test_generate_correlation_id_uniqueness(self):
        """Test that generated IDs are unique."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()
        
        self.assertNotEqual(id1, id2)


if __name__ == '__main__':
    unittest.main()
