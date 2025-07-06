"""
Unit tests for ML transaction features.
"""

import pytest
from datetime import datetime
import pandas as pd
import numpy as np

from src.ml.features.transaction_features import TransactionFeatures


class TestTransactionFeatures:
    """Test suite for TransactionFeatures class."""

    @pytest.fixture
    def feature_extractor(self):
        """Create a TransactionFeatures instance for testing."""
        return TransactionFeatures()

    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction for testing."""
        return {
            "description": "UPI-SWIGGY-DELIVERY-9876543210@paytm",
            "debit_amount": 250.50,
            "credit_amount": None,
            "transaction_date": datetime(2024, 1, 15, 12, 30),
            "reference_number": "REF123456789",
            "currency": "INR"
        }

    @pytest.mark.unit
    def test_extract_basic_features(self, feature_extractor, sample_transaction):
        """Test basic feature extraction."""
        features = feature_extractor.extract_basic_features(sample_transaction)
        
        # Check required features exist
        assert "description_length" in features
        assert "word_count" in features
        assert "amount" in features
        assert "is_debit" in features
        assert "is_credit" in features
        assert "has_numbers" in features
        
        # Check specific values
        assert features["description_length"] > 0
        assert features["amount"] == 250.50
        assert features["is_debit"] is True
        assert features["is_credit"] is False
        assert features["has_numbers"] is True
        assert features["has_reference"] is True

    @pytest.mark.unit
    def test_extract_text_patterns(self, feature_extractor):
        """Test text pattern extraction."""
        description = "UPI-SWIGGY-DELIVERY-9876543210@paytm"
        patterns = feature_extractor.extract_text_patterns(description)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Should extract meaningful patterns
        pattern_text = " ".join(patterns).lower()
        assert "swiggy" in pattern_text or "9876543210" in pattern_text

    @pytest.mark.unit
    def test_extract_temporal_features(self, feature_extractor):
        """Test temporal feature extraction."""
        test_date = datetime(2024, 1, 15, 12, 30)  # Monday
        features = feature_extractor.extract_temporal_features(test_date)
        
        assert "day_of_week" in features
        assert "month" in features
        assert "quarter" in features
        assert "is_weekend" in features
        
        # Check specific values
        assert features["day_of_week"] == 0  # Monday
        assert features["month"] == 1
        assert features["quarter"] == 1
        assert features["is_weekend"] is False

    @pytest.mark.unit
    def test_extract_merchant_features(self, feature_extractor):
        """Test merchant feature extraction."""
        food_description = "UPI-SWIGGY-DELIVERY"
        features = feature_extractor.extract_merchant_features(food_description)
        
        assert "is_food" in features
        assert "is_transport" in features
        assert "is_shopping" in features
        
        # Should detect food merchant
        assert features["is_food"] is True
        assert features["is_transport"] is False

    @pytest.mark.unit
    def test_combine_features(self, feature_extractor, sample_transaction):
        """Test combining all feature types."""
        all_features = feature_extractor.combine_features(sample_transaction)
        
        # Should include features from all extraction methods
        assert "description_length" in all_features  # Basic
        assert "day_of_week" in all_features  # Temporal
        assert "is_food" in all_features  # Merchant
        assert "text_patterns" in all_features  # Patterns
        
        # Text patterns should be a list
        assert isinstance(all_features["text_patterns"], list)

    @pytest.mark.unit
    def test_extract_meaningful_words(self, feature_extractor):
        """Test meaningful word extraction."""
        text = "UPI payment to Swiggy for food delivery"
        words = feature_extractor._extract_meaningful_words(text)
        
        assert isinstance(words, list)
        assert "swiggy" in words
        assert "food" in words
        assert "delivery" in words
        # Stop words should be filtered out
        assert "to" not in words
        assert "for" not in words

    @pytest.mark.unit
    def test_get_uppercase_ratio(self, feature_extractor):
        """Test uppercase ratio calculation."""
        # All uppercase
        ratio1 = feature_extractor._get_uppercase_ratio("HELLO")
        assert ratio1 == 1.0
        
        # All lowercase
        ratio2 = feature_extractor._get_uppercase_ratio("hello")
        assert ratio2 == 0.0
        
        # Mixed case
        ratio3 = feature_extractor._get_uppercase_ratio("Hello")
        assert 0.0 < ratio3 < 1.0
        
        # No letters
        ratio4 = feature_extractor._get_uppercase_ratio("12345")
        assert ratio4 == 0.0

    @pytest.mark.unit
    def test_empty_description_handling(self, feature_extractor):
        """Test handling of empty or invalid descriptions."""
        # Empty description
        patterns1 = feature_extractor.extract_text_patterns("")
        assert patterns1 == []
        
        # Very short description
        patterns2 = feature_extractor.extract_text_patterns("hi")
        assert patterns2 == []
        
        # None description
        patterns3 = feature_extractor.extract_text_patterns(None)
        assert patterns3 == []

    @pytest.mark.unit
    def test_amount_features_edge_cases(self, feature_extractor):
        """Test amount feature extraction edge cases."""
        # Zero amount
        transaction1 = {"debit_amount": None, "credit_amount": None}
        features1 = feature_extractor.extract_basic_features(transaction1)
        assert features1["amount"] == 0
        assert features1["amount_log"] == 0
        
        # Negative amount (should handle gracefully)
        transaction2 = {"debit_amount": -100, "credit_amount": None}
        features2 = feature_extractor.extract_basic_features(transaction2)
        assert features2["amount"] == -100

    @pytest.mark.unit
    def test_configuration_impact(self):
        """Test that configuration affects feature extraction."""
        custom_config = {
            "ml": {
                "feature_extraction": {
                    "min_pattern_length": 10,
                    "max_pattern_length": 15,
                    "min_description_length": 20
                }
            }
        }
        
        extractor = TransactionFeatures(custom_config["ml"])
        
        # Short description should return no patterns due to config
        short_desc = "UPI-SWIGGY"  # Less than min_description_length
        patterns = extractor.extract_text_patterns(short_desc)
        assert patterns == []

    @pytest.mark.unit
    def test_pattern_filtering(self, feature_extractor):
        """Test pattern length filtering."""
        # Description with patterns of various lengths
        description = "UPI-A-VERYLONGMERCHANTNAME-123@paytm"
        patterns = feature_extractor.extract_text_patterns(description)
        
        # Should filter by min and max length
        for pattern in patterns:
            assert len(pattern) >= feature_extractor.config["feature_extraction"]["min_pattern_length"]
            assert len(pattern) <= feature_extractor.config["feature_extraction"]["max_pattern_length"]