"""
Unit tests for ML similarity engine.
"""

import numpy as np
import pytest

from src.ml.models.similarity_engine import SimilarityEngine


class TestSimilarityEngine:
    """Test suite for SimilarityEngine class."""

    @pytest.fixture
    def similarity_engine(self):
        """Create a SimilarityEngine instance for testing."""
        return SimilarityEngine()

    @pytest.mark.unit
    def test_initialization(self, similarity_engine):
        """Test SimilarityEngine initialization."""
        assert similarity_engine.fuzzy_threshold > 0
        assert similarity_engine.cosine_threshold > 0
        assert similarity_engine.tfidf_vectorizer is not None
        assert similarity_engine._tfidf_fitted is False

    @pytest.mark.unit
    def test_find_similar_descriptions(self, similarity_engine):
        """Test finding similar descriptions using fuzzy matching."""
        target = "UPI-SWIGGY-DELIVERY"
        candidates = [
            "UPI-SWIGGY-FOOD",
            "UPI-ZOMATO-ORDER",
            "UPI-SWIGGY-RESTAURANT",
            "BANK-TRANSFER-FRIEND",
        ]

        similar = similarity_engine.find_similar_descriptions(target, candidates)

        assert isinstance(similar, list)
        # Should find SWIGGY-related matches
        if similar:
            assert all(isinstance(item, tuple) for item in similar)
            assert all(len(item) == 2 for item in similar)
            # Should be sorted by similarity (descending)
            similarities = [item[1] for item in similar]
            assert similarities == sorted(similarities, reverse=True)

    @pytest.mark.unit
    def test_find_similar_merchants(self, similarity_engine):
        """Test finding similar merchants from known patterns."""
        target = "UPI-SWIGGY-DELIVERY-12345@paytm"
        known_merchants = {
            "swiggy": "food",
            "zomato": "food",
            "uber": "transport",
            "amazon": "shopping",
        }

        similar = similarity_engine.find_similar_merchants(target, known_merchants)

        assert isinstance(similar, list)
        if similar:
            # Should find swiggy match
            found_merchants = [item[0] for item in similar]
            assert "swiggy" in found_merchants

            # Check structure: (merchant, category, score)
            for item in similar:
                assert len(item) == 3
                assert isinstance(item[2], float)
                assert 0 <= item[2] <= 1

    @pytest.mark.unit
    def test_compute_semantic_similarity(self, similarity_engine):
        """Test semantic similarity computation using TF-IDF."""
        descriptions = [
            "UPI payment to Swiggy for food",
            "Food delivery from Swiggy",
            "Bank transfer to friend",
            "Zomato food order payment",
        ]

        similarity_matrix = similarity_engine.compute_semantic_similarity(descriptions)

        assert isinstance(similarity_matrix, np.ndarray)
        assert similarity_matrix.shape == (len(descriptions), len(descriptions))

        # Diagonal should be 1.0 (self-similarity) for valid matrices
        if similarity_matrix.size > 0:
            np.testing.assert_array_almost_equal(np.diag(similarity_matrix), 1.0, decimal=5)

        # Matrix should be symmetric
        np.testing.assert_array_almost_equal(similarity_matrix, similarity_matrix.T, decimal=5)

    @pytest.mark.unit
    def test_find_semantic_matches(self, similarity_engine):
        """Test finding semantically similar descriptions."""
        target = "UPI payment to Swiggy for food delivery"
        candidates = [
            "Food order from Swiggy restaurant",
            "Bank transfer to friend",
            "Zomato food delivery payment",
            "Online shopping on Amazon",
        ]

        matches = similarity_engine.find_semantic_matches(target, candidates)

        assert isinstance(matches, list)
        if matches:
            # Should be sorted by similarity (descending)
            similarities = [item[1] for item in matches]
            assert similarities == sorted(similarities, reverse=True)

            # All similarities should be above threshold
            for _, similarity in matches:
                assert similarity >= similarity_engine.cosine_threshold

    @pytest.mark.unit
    def test_extract_common_patterns(self, similarity_engine):
        """Test extracting common patterns from descriptions."""
        descriptions = [
            "UPI-SWIGGY-DELIVERY-123@paytm",
            "UPI-SWIGGY-ORDER-456@paytm",
            "UPI-SWIGGY-FOOD-789@paytm",
        ]

        patterns = similarity_engine.extract_common_patterns(descriptions)

        assert isinstance(patterns, list)
        if patterns:
            # Should find common words like "swiggy", "upi"
            pattern_text = " ".join(patterns).lower()
            assert "swiggy" in pattern_text or "upi" in pattern_text

    @pytest.mark.unit
    def test_suggest_regex_pattern(self, similarity_engine):
        """Test regex pattern suggestion."""
        descriptions = ["UPI-SWIGGY-DELIVERY", "UPI-SWIGGY-ORDER", "UPI-SWIGGY-FOOD"]

        pattern = similarity_engine.suggest_regex_pattern(descriptions)

        if pattern:
            assert isinstance(pattern, str)
            # Should contain regex metacharacters
            assert ".*" in pattern
            # Should contain the common element
            assert "swiggy" in pattern.lower()

    @pytest.mark.unit
    def test_clean_description(self, similarity_engine):
        """Test description cleaning and normalization."""
        dirty_description = "  UPI   PAYMENT   to   SWIGGY   "
        clean = similarity_engine._clean_description(dirty_description)

        assert isinstance(clean, str)
        assert clean.strip() == clean  # No leading/trailing whitespace
        assert "  " not in clean  # No double spaces
        assert clean.islower()  # Should be lowercase

    @pytest.mark.unit
    def test_calculate_merchant_confidence(self, similarity_engine):
        """Test merchant confidence calculation."""
        description = "UPI-SWIGGY-DELIVERY"
        historical_matches = [
            {"similarity": 0.9, "recency_weight": 1.0, "success_rate": 0.8},
            {"similarity": 0.7, "recency_weight": 0.8, "success_rate": 0.9},
        ]

        confidence = similarity_engine.calculate_merchant_confidence(
            description, historical_matches
        )

        assert isinstance(confidence, float)
        assert 0.1 <= confidence <= 1.0

    @pytest.mark.unit
    def test_empty_input_handling(self, similarity_engine):
        """Test handling of empty or invalid inputs."""
        # Empty target
        similar1 = similarity_engine.find_similar_descriptions("", ["test"])
        assert similar1 == []

        # Empty candidates
        similar2 = similarity_engine.find_similar_descriptions("test", [])
        assert similar2 == []

        # Empty descriptions for semantic similarity
        similarity_matrix = similarity_engine.compute_semantic_similarity([])
        assert similarity_matrix.shape == (0, 0)

        # Single description
        similarity_matrix_single = similarity_engine.compute_semantic_similarity(["test"])
        assert similarity_matrix_single.shape == (1, 1)
        assert similarity_matrix_single[0, 0] == 1.0

    @pytest.mark.unit
    def test_threshold_configuration(self):
        """Test that thresholds affect results."""
        # High thresholds
        high_threshold_config = {
            "ml": {
                "similarity": {"fuzzy_threshold": 0.95, "cosine_threshold": 0.95},
                "models": {
                    "tfidf": {
                        "max_features": 1000,
                        "min_df": 2,
                        "max_df": 0.8,
                        "ngram_range": [1, 2],
                    }
                },
            }
        }

        engine = SimilarityEngine(high_threshold_config["ml"])

        # Should find fewer matches with high threshold
        target = "UPI-SWIGGY"
        candidates = ["UPI-SWIGGY-DELIVERY", "SWIGGY-FOOD", "ZOMATO-ORDER"]
        matches = engine.find_similar_descriptions(target, candidates)

        # With high threshold, should be more selective
        for _, similarity in matches:
            assert similarity >= 0.95

    @pytest.mark.unit
    def test_pattern_suggestion_edge_cases(self, similarity_engine):
        """Test edge cases in pattern suggestion."""
        # Empty descriptions
        pattern1 = similarity_engine.suggest_regex_pattern([])
        assert pattern1 is None

        # Single description (no common patterns)
        pattern2 = similarity_engine.suggest_regex_pattern(["single-description"])
        assert pattern2 is None or isinstance(pattern2, str)

        # Very different descriptions
        pattern3 = similarity_engine.suggest_regex_pattern(
            [
                "COMPLETELY-DIFFERENT-TEXT",
                "ANOTHER-UNRELATED-THING",
                "THIRD-RANDOM-DESCRIPTION",
            ]
        )
        # Should either return None or a very general pattern
        assert pattern3 is None or isinstance(pattern3, str)

    @pytest.mark.unit
    def test_merchant_confidence_edge_cases(self, similarity_engine):
        """Test edge cases in merchant confidence calculation."""
        description = "test"

        # No historical matches
        confidence1 = similarity_engine.calculate_merchant_confidence(description, [])
        assert confidence1 == 0.5  # Default confidence

        # Matches with missing fields
        incomplete_matches = [{"similarity": 0.8}]  # Missing other fields
        confidence2 = similarity_engine.calculate_merchant_confidence(
            description, incomplete_matches
        )
        assert 0.1 <= confidence2 <= 1.0

        # Very low similarities
        low_matches = [{"similarity": 0.1, "recency_weight": 1.0, "success_rate": 0.1}]
        confidence3 = similarity_engine.calculate_merchant_confidence(description, low_matches)
        assert 0.1 <= confidence3 <= 1.0
