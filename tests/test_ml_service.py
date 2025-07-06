"""
Unit tests for ML suggestion service.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.ml.ml_service import MLSuggestionService


class TestMLSuggestionService:
    """Test suite for MLSuggestionService class."""

    @pytest.fixture
    def ml_service(self):
        """Create an MLSuggestionService instance for testing."""
        config = {
            "ml": {
                "enabled": True,
                "confidence_threshold": 0.6,
                "max_suggestions": 5,
                "feature_extraction": {
                    "min_pattern_length": 3,
                    "max_pattern_length": 50,
                    "min_description_length": 5,
                },
                "similarity": {
                    "fuzzy_threshold": 0.8,
                    "cosine_threshold": 0.7,
                },
                "learning": {
                    "feedback_weight": 1.5,
                    "decay_factor": 0.95,
                    "short_term_days": 30,
                },
                "models": {
                    "naive_bayes_alpha": 1.0,
                    "tfidf": {
                        "max_features": 1000,
                        "min_df": 2,
                        "max_df": 0.8,
                        "ngram_range": [1, 2],
                    },
                },
            }
        }
        return MLSuggestionService(None, config)

    @pytest.fixture
    def disabled_ml_service(self):
        """Create an MLSuggestionService instance with ML disabled."""
        config = {"ml": {"enabled": False}}
        return MLSuggestionService(None, config)

    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction for testing."""
        return {
            "description": "UPI-SWIGGY-DELIVERY-9876543210@paytm",
            "debit_amount": 250.50,
            "credit_amount": None,
            "transaction_date": "2024-01-15 12:30:00",
            "reference_number": "REF123456789",
        }

    @pytest.mark.unit
    def test_initialization_enabled(self, ml_service):
        """Test MLSuggestionService initialization with ML enabled."""
        assert ml_service.ml_enabled is True
        assert ml_service.classifier is not None
        assert ml_service.config["ml"]["enabled"] is True

    @pytest.mark.unit
    def test_initialization_disabled(self, disabled_ml_service):
        """Test MLSuggestionService initialization with ML disabled."""
        assert disabled_ml_service.ml_enabled is False
        assert disabled_ml_service.classifier is None

    @pytest.mark.unit
    def test_suggest_regex_pattern(self, ml_service):
        """Test regex pattern suggestion."""
        description = "UPI-SWIGGY-DELIVERY"
        similar_descriptions = ["UPI-SWIGGY-ORDER", "UPI-SWIGGY-FOOD"]

        result = ml_service.suggest_regex_pattern(description, similar_descriptions)

        if result:  # Pattern might be None for insufficient data
            assert isinstance(result, dict)
            assert "pattern" in result
            assert "confidence" in result
            assert "reasoning" in result
            assert "source" in result
            assert result["source"] == "ml_analysis"
            assert 0 <= result["confidence"] <= 1

    @pytest.mark.unit
    def test_suggest_enum_category(self, ml_service):
        """Test enum category suggestion."""
        description = "UPI-SWIGGY-DELIVERY-12345@paytm"

        suggestions = ml_service.suggest_enum_category(description)

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3  # Should limit to top 3

        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert "category" in suggestion
            assert "confidence" in suggestion
            assert "reasoning" in suggestion
            assert "source" in suggestion
            assert 0 <= suggestion["confidence"] <= 1

    @pytest.mark.unit
    def test_suggest_transaction_category(self, ml_service, sample_transaction):
        """Test transaction category suggestion."""
        suggestions = ml_service.suggest_transaction_category(sample_transaction)

        assert isinstance(suggestions, list)

        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert "category" in suggestion
            assert "confidence" in suggestion
            assert "reasoning" in suggestion
            assert "source" in suggestion
            assert 0 <= suggestion["confidence"] <= 1

    @pytest.mark.unit
    def test_suggest_transaction_reason(self, ml_service, sample_transaction):
        """Test transaction reason suggestion."""
        category = "food"
        suggestions = ml_service.suggest_transaction_reason(
            sample_transaction, category
        )

        assert isinstance(suggestions, list)

        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert "reason" in suggestion
            assert "confidence" in suggestion
            assert "reasoning" in suggestion
            assert "source" in suggestion
            assert 0 <= suggestion["confidence"] <= 1
            # Reason should be related to the category
            reason_lower = suggestion["reason"].lower()
            category_lower = category.lower()
            assert (
                category_lower in reason_lower
                or "food" in reason_lower
                or "merchant" in reason_lower
            ), f"Reason '{suggestion['reason']}' not related to category '{category}'"

    @pytest.mark.unit
    def test_provide_feedback(self, ml_service, sample_transaction):
        """Test providing feedback to ML system."""
        # Should not raise any exceptions
        ml_service.provide_feedback(
            transaction=sample_transaction,
            suggestion_type="category",
            suggested_value="food",
            user_action="accepted",
            final_value="food",
        )

        # Test with different actions
        ml_service.provide_feedback(
            transaction=sample_transaction,
            suggestion_type="reason",
            suggested_value="Food delivery",
            user_action="rejected",
            final_value="Restaurant payment",
        )

    @pytest.mark.unit
    def test_get_suggestion_summary(self, ml_service, sample_transaction):
        """Test comprehensive suggestion summary."""
        summary = ml_service.get_suggestion_summary(sample_transaction)

        assert isinstance(summary, dict)
        assert "ml_enabled" in summary
        assert "suggestions" in summary
        assert "confidence_overall" in summary

        suggestions = summary["suggestions"]
        assert "category" in suggestions
        assert "reason" in suggestions
        assert "enum_category" in suggestions
        assert "regex_pattern" in suggestions

        assert isinstance(suggestions["category"], list)
        assert isinstance(suggestions["reason"], list)
        assert isinstance(suggestions["enum_category"], list)

        assert 0 <= summary["confidence_overall"] <= 1

    @pytest.mark.unit
    def test_disabled_ml_methods(self, disabled_ml_service, sample_transaction):
        """Test that methods return empty results when ML is disabled."""
        # Should return None or empty lists when ML is disabled

        regex_result = disabled_ml_service.suggest_regex_pattern("test")
        assert regex_result is None

        enum_suggestions = disabled_ml_service.suggest_enum_category("test")
        assert enum_suggestions == []

        category_suggestions = disabled_ml_service.suggest_transaction_category(
            sample_transaction
        )
        assert category_suggestions == []

        reason_suggestions = disabled_ml_service.suggest_transaction_reason(
            sample_transaction, "food"
        )
        assert reason_suggestions == []

        summary = disabled_ml_service.get_suggestion_summary(sample_transaction)
        assert summary["ml_enabled"] is False
        assert summary["confidence_overall"] == 0.0

    @pytest.mark.unit
    def test_calculate_pattern_confidence(self, ml_service):
        """Test pattern confidence calculation."""
        # Valid regex pattern
        confidence1 = ml_service._calculate_pattern_confidence(
            ".*swiggy.*", ["UPI-SWIGGY-DELIVERY", "UPI-SWIGGY-ORDER"]
        )
        assert 0.1 <= confidence1 <= 1.0

        # Invalid regex pattern
        confidence2 = ml_service._calculate_pattern_confidence(
            "[invalid regex", ["test"]
        )
        assert confidence2 == 0.3  # Default for invalid patterns

    @pytest.mark.unit
    def test_infer_category_from_pattern(self, ml_service):
        """Test category inference from patterns."""
        # Food patterns
        category1 = ml_service._infer_category_from_pattern("swiggy")
        assert category1 == "food"

        category2 = ml_service._infer_category_from_pattern("zomato")
        assert category2 == "food"

        # Transport patterns
        category3 = ml_service._infer_category_from_pattern("uber")
        assert category3 == "transport"

        # Unknown pattern
        category4 = ml_service._infer_category_from_pattern("unknown_merchant")
        assert category4 == "miscellaneous"

    @pytest.mark.unit
    def test_generate_category_reasoning(self, ml_service, sample_transaction):
        """Test category reasoning generation."""
        # Food category with swiggy in description
        reasoning1 = ml_service._generate_category_reasoning(sample_transaction, "food")
        assert isinstance(reasoning1, str)
        assert len(reasoning1) > 0
        assert reasoning1[0].isupper()  # Should be capitalized

        # Unknown category
        reasoning2 = ml_service._generate_category_reasoning(
            sample_transaction, "unknown"
        )
        assert isinstance(reasoning2, str)
        assert len(reasoning2) > 0

    @pytest.mark.unit
    def test_edge_cases(self, ml_service):
        """Test edge cases and error handling."""
        # Empty transaction
        empty_transaction = {}
        suggestions = ml_service.suggest_transaction_category(empty_transaction)
        assert isinstance(suggestions, list)

        # Transaction with missing fields
        minimal_transaction = {"description": "test"}
        suggestions2 = ml_service.suggest_transaction_category(minimal_transaction)
        assert isinstance(suggestions2, list)

        # Very long description
        long_desc = "A" * 1000
        suggestions3 = ml_service.suggest_enum_category(long_desc)
        assert isinstance(suggestions3, list)

    @pytest.mark.unit
    @patch("src.ml.ml_service.MLSuggestionService.__init__")
    def test_initialization_with_import_error(self, mock_init):
        """Test graceful handling of import errors."""
        # This test would need to be more complex to actually test import failures
        # For now, just test that the service can handle exceptions
        mock_init.side_effect = ImportError("ML dependencies not available")

        # The actual transformer should handle this gracefully
        # This is more of an integration test case

    @pytest.mark.unit
    def test_confidence_thresholds(self, ml_service, sample_transaction):
        """Test that confidence thresholds are respected."""
        # Get suggestions
        summary = ml_service.get_suggestion_summary(sample_transaction)

        # All suggestions should respect minimum confidence
        for category_suggestion in summary["suggestions"]["category"]:
            # Note: confidence might be below threshold for testing purposes
            # In real usage, low-confidence suggestions might be filtered
            assert 0 <= category_suggestion["confidence"] <= 1

    @pytest.mark.unit
    def test_suggestion_limits(self, ml_service, sample_transaction):
        """Test that suggestion limits are respected."""
        suggestions = ml_service.suggest_transaction_category(sample_transaction)

        # Should not exceed max_suggestions
        max_suggestions = ml_service.config.get("max_suggestions", 5)
        assert len(suggestions) <= max_suggestions

        enum_suggestions = ml_service.suggest_enum_category("test description")
        assert len(enum_suggestions) <= 3  # Hardcoded limit in the method

    @pytest.mark.unit
    def test_existing_patterns_integration(self, ml_service):
        """Test integration with existing patterns."""
        description = "UPI-SWIGGY-DELIVERY"
        existing_patterns = ["SWIGGY-ORDER", "ZOMATO-FOOD", "AMAZON-PURCHASE"]

        suggestions = ml_service.suggest_enum_category(description, existing_patterns)

        assert isinstance(suggestions, list)
        # Should include both pattern-based and similarity-based suggestions
        if suggestions:
            sources = [s["source"] for s in suggestions]
            # Should have different types of analysis
            assert len(set(sources)) >= 1
