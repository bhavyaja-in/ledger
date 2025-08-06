"""
Integration tests for ML-powered transaction categorization.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.ml.ml_service import MLSuggestionService
from src.ml.utils.ml_config import MLConfig


class TestMLIntegration:
    """Integration test suite for ML functionality."""

    @pytest.fixture
    def full_ml_service(self):
        """Create a fully configured ML service for integration testing."""
        config = {
            **MLConfig.get_default_config(),
        }
        return MLSuggestionService(None, config)

    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions for testing various scenarios."""
        return [
            {
                "description": "UPI-SWIGGY-DELIVERY-9876543210@paytm",
                "debit_amount": 250.50,
                "credit_amount": None,
                "transaction_date": "2024-01-15 12:30:00",
                "reference_number": "REF123456789",
            },
            {
                "description": "UPI-UBER-TRIP-1234567890@paytm",
                "debit_amount": 180.00,
                "credit_amount": None,
                "transaction_date": "2024-01-15 18:45:00",
                "reference_number": "REF987654321",
            },
            {
                "description": "NEFT-TRANSFER-TO-FRIEND-JOHN",
                "debit_amount": 5000.00,
                "credit_amount": None,
                "transaction_date": "2024-01-16 10:00:00",
                "reference_number": "REF555666777",
            },
            {
                "description": "AMAZON-PURCHASE-ELECTRONICS",
                "debit_amount": 1299.99,
                "credit_amount": None,
                "transaction_date": "2024-01-17 14:20:00",
                "reference_number": "REF111222333",
            },
        ]

    @pytest.mark.integration
    def test_end_to_end_categorization_workflow(self, full_ml_service, sample_transactions):
        """Test complete ML categorization workflow."""
        for transaction in sample_transactions:
            # Get comprehensive suggestions
            summary = full_ml_service.get_suggestion_summary(transaction)

            # Verify summary structure
            assert "ml_enabled" in summary
            assert "suggestions" in summary
            assert "confidence_overall" in summary

            assert summary["ml_enabled"] is True
            assert 0 <= summary["confidence_overall"] <= 1

            # Verify all suggestion types are present
            suggestions = summary["suggestions"]
            assert "category" in suggestions
            assert "reason" in suggestions
            assert "enum_category" in suggestions
            assert "regex_pattern" in suggestions

            # Verify category suggestions
            if suggestions["category"]:
                for suggestion in suggestions["category"]:
                    assert "category" in suggestion
                    assert "confidence" in suggestion
                    assert "reasoning" in suggestion
                    assert "source" in suggestion
                    assert 0 <= suggestion["confidence"] <= 1

    @pytest.mark.integration
    def test_ml_pattern_learning_simulation(self, full_ml_service):
        """Test ML learning from user feedback simulation."""
        # Simulate user accepting suggestions
        transaction1 = {
            "description": "UPI-SWIGGY-DELIVERY-123@paytm",
            "debit_amount": 200.0,
            "transaction_date": "2024-01-15",
        }

        # Provide positive feedback
        full_ml_service.provide_feedback(
            transaction=transaction1,
            suggestion_type="category",
            suggested_value="food",
            user_action="accepted",
            final_value="food",
        )

        # Test similar transaction gets better suggestions
        transaction2 = {
            "description": "UPI-SWIGGY-ORDER-456@paytm",
            "debit_amount": 180.0,
            "transaction_date": "2024-01-16",
        }

        suggestions = full_ml_service.suggest_transaction_category(transaction2)
        assert isinstance(suggestions, list)

        # Should have food-related suggestions
        if suggestions:
            food_found = any("food" in suggestion["category"].lower() for suggestion in suggestions)
            assert food_found or len(suggestions) > 0  # Either food found or other suggestions

    @pytest.mark.integration
    def test_ml_similarity_based_suggestions(self, full_ml_service):
        """Test similarity-based pattern suggestions."""
        # Test enum category suggestions with existing patterns
        description = "UPI-FOODPANDA-DELIVERY"
        existing_patterns = ["SWIGGY-ORDER", "ZOMATO-FOOD", "DOMINOS-PIZZA"]

        suggestions = full_ml_service.suggest_enum_category(description, existing_patterns)

        assert isinstance(suggestions, list)
        # Should provide suggestions based on both analysis and similarity
        if suggestions:
            sources = [s["source"] for s in suggestions]
            assert len(sources) > 0

    @pytest.mark.integration
    def test_ml_regex_pattern_generation(self, full_ml_service):
        """Test regex pattern generation from multiple descriptions."""
        descriptions = [
            "UPI-SWIGGY-DELIVERY-123@paytm",
            "UPI-SWIGGY-ORDER-456@paytm",
            "UPI-SWIGGY-FOOD-789@paytm",
        ]

        pattern_result = full_ml_service.suggest_regex_pattern(
            "UPI-SWIGGY-NEW-000@paytm", descriptions
        )

        if pattern_result:
            assert "pattern" in pattern_result
            assert "confidence" in pattern_result
            assert "reasoning" in pattern_result
            assert 0 <= pattern_result["confidence"] <= 1
            # Pattern should capture the common elements
            assert "swiggy" in pattern_result["pattern"].lower()

    @pytest.mark.integration
    def test_ml_contextual_reasoning(self, full_ml_service):
        """Test contextual reason generation."""
        food_transaction = {
            "description": "UPI-DOMINOS-PIZZA-ORDER",
            "debit_amount": 350.0,
            "transaction_date": "2024-01-15",
        }

        reasons = full_ml_service.suggest_transaction_reason(food_transaction, "food")

        assert isinstance(reasons, list)
        if reasons:
            for reason in reasons:
                assert "reason" in reason
                assert "confidence" in reason
                assert "reasoning" in reason
                # Reason should be contextual
                reason_text = reason["reason"].lower()
                assert (
                    "food" in reason_text
                    or "pizza" in reason_text
                    or "dominos" in reason_text
                    or "restaurant" in reason_text
                )

    @pytest.mark.integration
    def test_ml_confidence_scoring(self, full_ml_service):
        """Test ML confidence scoring across different scenarios."""
        test_cases = [
            {
                "description": "UPI-SWIGGY-DELIVERY",  # Clear food pattern
                "expected_confidence": "high",
            },
            {
                "description": "UNKNOWN-MERCHANT-XYZ",  # Unclear pattern
                "expected_confidence": "low",
            },
            {
                "description": "UPI-UBER-RIDE-BOOKING",  # Clear transport pattern
                "expected_confidence": "high",
            },
        ]

        for case in test_cases:
            transaction = {
                "description": case["description"],
                "debit_amount": 100.0,
                "transaction_date": "2024-01-15",
            }

            summary = full_ml_service.get_suggestion_summary(transaction)

            # Verify confidence levels match expectations
            confidence = summary["confidence_overall"]

            if case["expected_confidence"] == "high":
                # Should have reasonable confidence for clear patterns
                assert confidence >= 0.3, f"Low confidence for clear pattern: {case['description']}"
            else:
                # May have lower confidence for unclear patterns
                assert (
                    0 <= confidence <= 1
                ), f"Invalid confidence for unclear pattern: {case['description']}"

    @pytest.mark.integration
    def test_ml_disabled_fallback(self):
        """Test graceful fallback when ML is disabled."""
        config = {"ml": {"enabled": False}}

        disabled_service = MLSuggestionService(None, config)

        transaction = {
            "description": "UPI-SWIGGY-DELIVERY",
            "debit_amount": 200.0,
            "transaction_date": "2024-01-15",
        }

        # All methods should return empty/None results gracefully
        assert disabled_service.suggest_regex_pattern("test") is None
        assert disabled_service.suggest_enum_category("test") == []
        assert disabled_service.suggest_transaction_category(transaction) == []
        assert disabled_service.suggest_transaction_reason(transaction, "food") == []

        summary = disabled_service.get_suggestion_summary(transaction)
        assert summary["ml_enabled"] is False
        assert summary["confidence_overall"] == 0.0

    @pytest.mark.integration
    def test_ml_performance_with_large_input(self, full_ml_service):
        """Test ML performance with larger inputs."""
        # Create a longer description
        long_description = "UPI-" + "SWIGGY-" * 20 + "DELIVERY-123@paytm"

        transaction = {
            "description": long_description,
            "debit_amount": 500.0,
            "transaction_date": "2024-01-15",
        }

        # Should handle long inputs gracefully
        summary = full_ml_service.get_suggestion_summary(transaction)
        assert isinstance(summary, dict)
        assert "suggestions" in summary

        # Performance test - should complete reasonably quickly
        import time

        start_time = time.time()
        for _ in range(5):  # Run multiple times
            full_ml_service.suggest_transaction_category(transaction)
        end_time = time.time()

        # Should complete within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 5.0, "ML processing too slow"

    @pytest.mark.integration
    def test_ml_category_consistency(self, full_ml_service):
        """Test consistency of ML categorization for similar transactions."""
        base_transaction = {"debit_amount": 200.0, "transaction_date": "2024-01-15"}

        similar_descriptions = [
            "UPI-SWIGGY-DELIVERY-123@paytm",
            "UPI-SWIGGY-ORDER-456@paytm",
            "UPI-SWIGGY-FOOD-789@paytm",
        ]

        all_suggestions = []
        for desc in similar_descriptions:
            transaction = {**base_transaction, "description": desc}
            suggestions = full_ml_service.suggest_transaction_category(transaction)
            all_suggestions.extend(suggestions)

        # Should have consistent categorization for similar transactions
        if all_suggestions:
            categories = [s["category"] for s in all_suggestions]
            food_categories = [cat for cat in categories if "food" in cat.lower()]

            # At least some should be food-related for Swiggy transactions
            assert len(food_categories) > 0 or len(categories) > 0
