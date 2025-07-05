"""
Comprehensive tests for currency detection and management
"""

from unittest.mock import Mock, call, patch

import pytest

from src.utils.currency_detector import CurrencyDetector


class TestCurrencyDetector:
    """Test suite for CurrencyDetector class"""

    @pytest.fixture
    def detector(self):
        """Create currency detector instance"""
        return CurrencyDetector()

    # =====================
    # CURRENCY DETECTION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_single_currency_usd(self, detector):
        """Test USD detection from transaction description"""
        available = ["USD", "EUR", "INR"]

        # Test dollar sign
        assert detector.detect_currency("Payment to Store $50", available) == "USD"

        # Test USD text
        assert detector.detect_currency("Transfer in USD currency", available) == "USD"

        # Test dollar word
        assert detector.detect_currency("Received 100 dollars", available) == "USD"

        # Test united states
        assert detector.detect_currency("Transaction from United States", available) == "USD"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_single_currency_eur(self, detector):
        """Test EUR detection from transaction description"""
        available = ["USD", "EUR", "INR"]

        # Test euro sign
        assert detector.detect_currency("Payment €25 for service", available) == "EUR"

        # Test EUR text
        assert detector.detect_currency("Exchange to EUR", available) == "EUR"

        # Test euro word
        assert detector.detect_currency("Received 50 euros", available) == "EUR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_single_currency_gbp(self, detector):
        """Test GBP detection from transaction description"""
        available = ["GBP", "USD", "INR"]

        # Test pound sign
        assert detector.detect_currency("Payment £100 for goods", available) == "GBP"

        # Test GBP text
        assert detector.detect_currency("Convert to GBP", available) == "GBP"

        # Test pound word
        assert detector.detect_currency("Received 75 pounds", available) == "GBP"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_single_currency_inr(self, detector):
        """Test INR detection from transaction description"""
        available = ["USD", "EUR", "INR"]

        # Test rupee sign
        assert detector.detect_currency("Payment ₹1500 for shopping", available) == "INR"

        # Test INR text
        assert detector.detect_currency("Exchange to INR", available) == "INR"

        # Test rupee word
        assert detector.detect_currency("Received 2000 rupees", available) == "INR"

        # Test Rs. abbreviation
        assert detector.detect_currency("Payment Rs. 500", available) == "INR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_single_currency_jpy(self, detector):
        """Test JPY detection from transaction description"""
        available = ["JPY", "USD", "INR"]

        # Test yen sign
        assert detector.detect_currency("Payment ¥1000 for goods", available) == "JPY"

        # Test JPY text
        assert detector.detect_currency("Exchange to JPY", available) == "JPY"

        # Test yen word
        assert detector.detect_currency("Received 5000 yen", available) == "JPY"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_no_currency_patterns(self, detector):
        """Test when no currency patterns are found"""
        available = ["USD", "EUR", "INR"]

        # Generic transaction without currency indicators
        assert detector.detect_currency("Regular transaction", available) is None

        # Empty description
        assert detector.detect_currency("", available) is None

        # Numbers without currency
        assert detector.detect_currency("Transaction 1000", available) is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_multiple_currencies_ambiguous(self, detector):
        """Test when multiple currencies detected (should return None)"""
        available = ["USD", "EUR", "INR"]

        # Multiple currency symbols
        result = detector.detect_currency("Payment $50 and €25 and ₹1000", available)
        assert result is None

        # Multiple currency words
        result = detector.detect_currency("Convert dollars to euros", available)
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_currency_not_in_available_list(self, detector):
        """Test detection when currency not in available list"""
        available = ["USD", "EUR"]  # INR not available

        # INR pattern but not in available list
        assert detector.detect_currency("Payment ₹1500", available) is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_detect_currency_case_insensitive(self, detector):
        """Test detection is case insensitive"""
        available = ["USD", "EUR", "INR"]

        assert detector.detect_currency("Payment in usd", available) == "USD"
        assert detector.detect_currency("Exchange to EUR", available) == "EUR"
        assert detector.detect_currency("Amount in INR", available) == "INR"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_detect_currency_empty_inputs(self, detector):
        """Test detection with empty inputs"""
        # Empty description
        assert detector.detect_currency("", ["USD", "EUR"]) is None

        # None description
        assert detector.detect_currency(None, ["USD", "EUR"]) is None

        # Empty available currencies
        assert detector.detect_currency("Payment $50", []) is None

        # None available currencies
        assert detector.detect_currency("Payment $50", None) is None

    # =====================
    # CURRENCY SYMBOL TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_get_currency_symbols(self, detector):
        """Test currency symbol mapping"""
        assert detector.get_currency_symbol("USD") == "$"
        assert detector.get_currency_symbol("EUR") == "€"
        assert detector.get_currency_symbol("GBP") == "£"
        assert detector.get_currency_symbol("INR") == "₹"
        assert detector.get_currency_symbol("JPY") == "¥"
        assert detector.get_currency_symbol("CNY") == "¥"
        assert detector.get_currency_symbol("AUD") == "A$"
        assert detector.get_currency_symbol("CAD") == "C$"
        assert detector.get_currency_symbol("CHF") == "CHF"
        assert detector.get_currency_symbol("SGD") == "S$"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_get_currency_symbol_unknown(self, detector):
        """Test currency symbol for unknown currency"""
        # Should return the currency code itself
        assert detector.get_currency_symbol("XYZ") == "XYZ"
        assert detector.get_currency_symbol("") == ""

    # =====================
    # CURRENCY VALIDATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_is_valid_currency_code(self, detector):
        """Test currency code validation"""
        # Valid 3-letter codes
        assert detector.is_valid_currency_code("USD") is True
        assert detector.is_valid_currency_code("EUR") is True
        assert detector.is_valid_currency_code("INR") is True

        # Invalid codes
        assert detector.is_valid_currency_code("US") is False  # Too short
        assert detector.is_valid_currency_code("USDD") is False  # Too long
        assert detector.is_valid_currency_code("123") is False  # Numbers
        assert detector.is_valid_currency_code("US1") is False  # Mixed
        assert detector.is_valid_currency_code("") is False  # Empty
        assert detector.is_valid_currency_code(None) is False  # None

    # =====================
    # CURRENCY NORMALIZATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_normalize_currency_list_single_string(self, detector):
        """Test normalization of single currency string"""
        assert detector.normalize_currency_list("USD") == ["USD"]
        assert detector.normalize_currency_list("inr") == ["INR"]  # Case conversion
        assert detector.normalize_currency_list("eur") == ["EUR"]

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_normalize_currency_list_multiple_list(self, detector):
        """Test normalization of multiple currencies list"""
        result = detector.normalize_currency_list(["USD", "EUR", "INR"])
        assert result == ["USD", "EUR", "INR"]

        # Case conversion
        result = detector.normalize_currency_list(["usd", "eur", "inr"])
        assert result == ["USD", "EUR", "INR"]

        # Mixed case
        result = detector.normalize_currency_list(["USD", "eur", "Inr"])
        assert result == ["USD", "EUR", "INR"]

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_normalize_currency_list_invalid_inputs(self, detector):
        """Test normalization with invalid inputs"""
        # Invalid single currency
        assert detector.normalize_currency_list("US") == ["INR"]  # Too short
        assert detector.normalize_currency_list("USDD") == ["INR"]  # Too long
        assert detector.normalize_currency_list("123") == ["INR"]  # Numbers

        # Invalid list with some valid currencies
        result = detector.normalize_currency_list(["USD", "XX", "EUR", "123"])
        assert result == ["USD", "EUR"]  # Only valid ones

        # Completely invalid list
        assert detector.normalize_currency_list(["XX", "12", "YZ"]) == ["INR"]

        # Empty list
        assert detector.normalize_currency_list([]) == ["INR"]

        # None input
        assert detector.normalize_currency_list(None) == ["INR"]

    # =====================
    # USER INTERACTION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_user_for_currency_valid_selection(self, detector):
        """Test user currency selection with valid input"""
        available = ["USD", "EUR", "INR"]
        description = "Test transaction"

        with patch("builtins.input", return_value="2"), patch("builtins.print"):
            result = detector.ask_user_for_currency(available, description)
            assert result == "EUR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_user_for_currency_invalid_then_valid(self, detector):
        """Test user currency selection with invalid then valid input"""
        available = ["USD", "EUR", "INR"]
        description = "Test transaction"

        with patch("builtins.input", side_effect=["5", "abc", "1"]), patch("builtins.print"):
            result = detector.ask_user_for_currency(available, description)
            assert result == "USD"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_user_for_currency_keyboard_interrupt(self, detector):
        """Test user currency selection with keyboard interrupt"""
        available = ["USD", "EUR", "INR"]
        description = "Test transaction"

        with patch("builtins.input", side_effect=KeyboardInterrupt), patch("builtins.print"):
            result = detector.ask_user_for_currency(available, description)
            assert result == "USD"  # Should return first currency

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_user_for_currency_interrupted_flag(self, detector):
        """Test user currency selection when interrupted flag is set"""
        detector._interrupted = True
        available = ["USD", "EUR", "INR"]
        description = "Test transaction"

        result = detector.ask_user_for_currency(available, description)
        assert result == "USD"  # Should return first currency immediately

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_user_for_currency_long_description(self, detector):
        """Test user currency selection with long description (truncation)"""
        available = ["USD", "EUR"]
        long_description = "A" * 100  # Very long description

        with patch("builtins.input", return_value="1"), patch("builtins.print") as mock_print:
            result = detector.ask_user_for_currency(available, long_description)
            assert result == "USD"

            # Verify description was truncated
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            description_line = [line for line in print_calls if "Transaction:" in line][0]
            assert "..." in description_line
            assert len(description_line) < len(long_description) + 20

    # =====================
    # INTEGRATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_currency_detection_workflow_single_currency(self, detector):
        """Test complete workflow for single currency processor"""
        available = ["INR"]  # Single currency

        # Should return INR regardless of description
        assert detector.detect_currency("Payment $50", available) is None
        assert detector.detect_currency("Payment ₹500", available) == "INR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_currency_detection_workflow_multi_currency_success(self, detector):
        """Test complete workflow for multi-currency with successful detection"""
        available = ["USD", "EUR", "INR"]

        # Should detect USD
        result = detector.detect_currency("Payment $50 to store", available)
        assert result == "USD"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_currency_detection_workflow_multi_currency_failure(self, detector):
        """Test complete workflow for multi-currency with detection failure"""
        available = ["USD", "EUR", "INR"]
        description = "Regular payment to store"

        # Detection should fail (no currency patterns)
        detected = detector.detect_currency(description, available)
        assert detected is None

        # Would need user interaction
        with patch("builtins.input", return_value="3"), patch("builtins.print"):
            user_selected = detector.ask_user_for_currency(available, description)
            assert user_selected == "INR"
