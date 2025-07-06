"""
Test ICICI Bank Transformer with currency support
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.transformers.icici_bank_transformer import IciciBankTransformer
from src.utils.currency_detector import CurrencyDetector


class TestIciciBankTransformerCurrency:
    """Test currency functionality in ICICI Bank Transformer"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        mock_manager = Mock()
        mock_manager.get_session.return_value = Mock()
        return mock_manager

    @pytest.fixture
    def mock_config_loader(self):
        """Mock config loader"""
        mock_loader = Mock()
        return mock_loader

    @pytest.fixture
    def single_currency_config(self):
        """Configuration for single currency processor"""
        return {"processors": {"icici_bank": {"currency": "INR"}}}

    @pytest.fixture
    def multi_currency_config(self):
        """Configuration for multi-currency processor"""
        return {
            "processors": {"icici_bank": {"currency": ["USD", "EUR", "GBP", "INR"]}}
        }

    @pytest.fixture
    def transformer_single_currency(
        self, mock_db_manager, single_currency_config, mock_config_loader
    ):
        """Create transformer with single currency configuration"""
        return IciciBankTransformer(
            mock_db_manager, single_currency_config, mock_config_loader
        )

    @pytest.fixture
    def transformer_multi_currency(
        self, mock_db_manager, multi_currency_config, mock_config_loader
    ):
        """Create transformer with multi-currency configuration"""
        return IciciBankTransformer(
            mock_db_manager, multi_currency_config, mock_config_loader
        )

    # =====================
    # INITIALIZATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transformer_currency_detector_initialization(
        self, transformer_single_currency
    ):
        """Test currency detector is initialized"""
        assert hasattr(transformer_single_currency, "currency_detector")
        assert isinstance(
            transformer_single_currency.currency_detector, CurrencyDetector
        )

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transformer_single_currency_initialization(
        self, transformer_single_currency
    ):
        """Test single currency processor initialization"""
        assert transformer_single_currency.processor_currencies == ["INR"]

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transformer_multi_currency_initialization(
        self, transformer_multi_currency
    ):
        """Test multi-currency processor initialization"""
        expected_currencies = ["USD", "EUR", "GBP", "INR"]
        assert transformer_multi_currency.processor_currencies == expected_currencies

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transformer_invalid_currency_config(
        self, mock_db_manager, mock_config_loader
    ):
        """Test transformer with invalid currency configuration defaults to INR"""
        invalid_config = {
            "processors": {
                "icici_bank": {"currency": ["XX", "123", "AB"]}
            }  # All invalid
        }

        transformer = IciciBankTransformer(
            mock_db_manager, invalid_config, mock_config_loader
        )
        assert transformer.processor_currencies == ["INR"]  # Should default to INR

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transformer_missing_currency_config(
        self, mock_db_manager, mock_config_loader
    ):
        """Test transformer without currency config defaults to INR"""
        minimal_config = {"processors": {"icici_bank": {}}}  # No currency config

        transformer = IciciBankTransformer(
            mock_db_manager, minimal_config, mock_config_loader
        )
        assert transformer.processor_currencies == ["INR"]  # Should default to INR

    # =====================
    # CURRENCY DETERMINATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_determine_currency_single_currency_processor(
        self, transformer_single_currency
    ):
        """Test currency determination for single currency processor"""
        # Should always return INR regardless of description or amounts
        row_data1 = {
            "Transaction Remarks": "Payment $100 USD",
            "Withdrawal Amount (INR )": "$100",
            "Deposit Amount (INR )": "",
        }
        result = transformer_single_currency._determine_transaction_currency(row_data1)
        assert result == "INR"

        row_data2 = {
            "Transaction Remarks": "Payment ₹500",
            "Withdrawal Amount (INR )": "₹500",
            "Deposit Amount (INR )": "",
        }
        result = transformer_single_currency._determine_transaction_currency(row_data2)
        assert result == "INR"

        row_data3 = {
            "Transaction Remarks": "Regular payment",
            "Withdrawal Amount (INR )": "100",
            "Deposit Amount (INR )": "",
        }
        result = transformer_single_currency._determine_transaction_currency(row_data3)
        assert result == "INR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_determine_currency_multi_currency_auto_detection(
        self, transformer_multi_currency
    ):
        """Test automatic currency detection for multi-currency processor"""
        # USD detection from amount (priority 1)
        with patch("builtins.print"):  # Suppress detection print
            row_data = {
                "Transaction Remarks": "Payment to store",
                "Withdrawal Amount (INR )": "$100",
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "USD"

        # EUR detection from amount
        with patch("builtins.print"):
            row_data = {
                "Transaction Remarks": "Payment for service",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "€50",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "EUR"

        # GBP detection from description (when not in amount)
        with patch("builtins.print"):
            row_data = {
                "Transaction Remarks": "Payment £75 for goods",
                "Withdrawal Amount (INR )": "75",
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "GBP"

        # INR detection from description
        with patch("builtins.print"):
            row_data = {
                "Transaction Remarks": "Payment ₹2000 for shopping",
                "Withdrawal Amount (INR )": "2000",
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "INR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_determine_currency_multi_currency_user_interaction(
        self, transformer_multi_currency
    ):
        """Test user interaction when auto-detection fails"""
        # Mock currency detector's ask_user_for_currency method
        with patch.object(
            transformer_multi_currency.currency_detector,
            "ask_user_for_currency",
            return_value="EUR",
        ):
            row_data = {
                "Transaction Remarks": "Regular payment",
                "Withdrawal Amount (INR )": "100",
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "EUR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_determine_currency_multi_currency_ambiguous(
        self, transformer_multi_currency
    ):
        """Test currency determination when multiple currencies detected"""
        # Mock detect_currency to return None (ambiguous)
        with (
            patch.object(
                transformer_multi_currency.currency_detector,
                "detect_currency",
                return_value=None,
            ),
            patch.object(
                transformer_multi_currency.currency_detector,
                "ask_user_for_currency",
                return_value="USD",
            ),
        ):
            row_data = {
                "Transaction Remarks": "Payment with mixed currencies",
                "Withdrawal Amount (INR )": "$50 and €25",
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert result == "USD"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_determine_currency_priority_amount_over_description(
        self, transformer_multi_currency
    ):
        """Test that amount fields take priority over description for currency detection"""
        # Amount field has USD, description has EUR - should detect USD from amount
        with patch("builtins.print"):  # Suppress detection print
            row_data = {
                "Transaction Remarks": "Payment €50 for international service",
                "Withdrawal Amount (INR )": "$100",  # USD in amount (priority)
                "Deposit Amount (INR )": "",
            }
            result = transformer_multi_currency._determine_transaction_currency(
                row_data
            )
            assert (
                result == "USD"
            )  # Should pick USD from amount, not EUR from description

    # =====================
    # TRANSACTION DISPLAY TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_with_currency_usd(self, transformer_multi_currency):
        """Test transaction display with USD currency"""
        transaction = {
            "date": datetime(2024, 1, 15),
            "description": "Test USD transaction",
            "transaction_type": "debit",
            "debit_amount": 100.0,
            "balance": 500.0,
            "reference_number": "REF123",
            "currency": "USD",
        }

        with patch("builtins.print") as mock_print:
            transformer_multi_currency._display_transaction(transaction)

            # Verify USD symbol is used
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            amount_line = [line for line in print_calls if "Amount:" in line][0]
            balance_line = [line for line in print_calls if "Balance:" in line][0]
            currency_line = [line for line in print_calls if "Currency:" in line][0]

            assert "$100.00" in amount_line
            assert "$500.00" in balance_line
            assert "Currency: USD" in currency_line

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_with_currency_eur(self, transformer_multi_currency):
        """Test transaction display with EUR currency"""
        transaction = {
            "date": datetime(2024, 1, 15),
            "description": "Test EUR transaction",
            "transaction_type": "credit",
            "credit_amount": 85.0,
            "balance": 300.0,
            "reference_number": "REF456",
            "currency": "EUR",
        }

        with patch("builtins.print") as mock_print:
            transformer_multi_currency._display_transaction(transaction)

            # Verify EUR symbol is used
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            amount_line = [line for line in print_calls if "Amount:" in line][0]
            balance_line = [line for line in print_calls if "Balance:" in line][0]
            currency_line = [line for line in print_calls if "Currency:" in line][0]

            assert "€85.00" in amount_line
            assert "€300.00" in balance_line
            assert "Currency: EUR" in currency_line

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_with_currency_inr(self, transformer_single_currency):
        """Test transaction display with INR currency"""
        transaction = {
            "date": datetime(2024, 1, 15),
            "description": "Test INR transaction",
            "transaction_type": "debit",
            "debit_amount": 1500.0,
            "balance": 5000.0,
            "reference_number": "REF789",
            "currency": "INR",
        }

        with patch("builtins.print") as mock_print:
            transformer_single_currency._display_transaction(transaction)

            # Verify INR symbol is used
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            amount_line = [line for line in print_calls if "Amount:" in line][0]
            balance_line = [line for line in print_calls if "Balance:" in line][0]
            currency_line = [line for line in print_calls if "Currency:" in line][0]

            assert "₹1,500.00" in amount_line
            assert "₹5,000.00" in balance_line
            assert "Currency: INR" in currency_line

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_default_currency_fallback(
        self, transformer_single_currency
    ):
        """Test transaction display falls back to INR when currency missing"""
        transaction = {
            "date": datetime(2024, 1, 15),
            "description": "Transaction without currency",
            "transaction_type": "credit",
            "credit_amount": 2000.0,
            "balance": 7000.0,
            "reference_number": "REF000",
            # No currency field
        }

        with patch("builtins.print") as mock_print:
            transformer_single_currency._display_transaction(transaction)

            # Should default to INR
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            amount_line = [line for line in print_calls if "Amount:" in line][0]
            balance_line = [line for line in print_calls if "Balance:" in line][0]
            currency_line = [line for line in print_calls if "Currency:" in line][0]

            assert "₹2,000.00" in amount_line
            assert "₹7,000.00" in balance_line
            assert "Currency: INR" in currency_line

    # =====================
    # TRANSACTION TRANSFORMATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_includes_currency(self, transformer_multi_currency):
        """Test transaction transformation includes currency field"""
        # Mock the currency determination to return USD
        with patch.object(
            transformer_multi_currency,
            "_determine_transaction_currency",
            return_value="USD",
        ):
            # Sample transaction row data
            row_data = {
                "Transaction Date": "15/01/2024",
                "Transaction Remarks": "Test transaction",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "100",
                "Balance (INR )": "500",
                "S No.": "REF123",
            }

            result = transformer_multi_currency._transform_transaction(row_data)

            # Verify currency is included in result
            assert "currency" in result
            assert result["currency"] == "USD"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_currency_determination_called(
        self, transformer_multi_currency
    ):
        """Test that currency determination is called during transformation"""
        with patch.object(
            transformer_multi_currency,
            "_determine_transaction_currency",
            return_value="EUR",
        ) as mock_determine:
            row_data = {
                "Transaction Date": "15/01/2024",
                "Transaction Remarks": "EUR payment",
                "Withdrawal Amount (INR )": "85",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "415",
                "S No.": "REF456",
            }

            result = transformer_multi_currency._transform_transaction(row_data)

            # Verify currency determination was called with row data
            mock_determine.assert_called_once_with(row_data)
            assert result["currency"] == "EUR"

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_single_currency_consistent(
        self, transformer_single_currency
    ):
        """Test single currency transformer consistently returns INR"""
        row_data = {
            "Transaction Date": "15/01/2024",
            "Transaction Remarks": "Payment with $100 USD mentioned",
            "Withdrawal Amount (INR )": "",
            "Deposit Amount (INR )": "100",
            "Balance (INR )": "500",
            "S No.": "REF789",
        }

        result = transformer_single_currency._transform_transaction(row_data)

        # Should always be INR for single currency processor
        assert result["currency"] == "INR"

    # =====================
    # INTEGRATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_end_to_end_currency_workflow_single_currency(
        self, transformer_single_currency
    ):
        """Test complete currency workflow for single currency processor"""
        row_data = {
            "Transaction Date": "15/01/2024",
            "Transaction Remarks": "Payment to store",
            "Withdrawal Amount (INR )": "1500",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "8500",
            "S No.": "REF001",
        }

        # Transform transaction
        transformed = transformer_single_currency._transform_transaction(row_data)

        # Verify currency is INR
        assert transformed["currency"] == "INR"

        # Test display
        with patch("builtins.print") as mock_print:
            transformer_single_currency._display_transaction(transformed)

            print_calls = [call.args[0] for call in mock_print.call_args_list]
            currency_line = [line for line in print_calls if "Currency:" in line][0]
            amount_line = [line for line in print_calls if "Amount:" in line][0]

            assert "Currency: INR" in currency_line
            assert "₹1,500.00" in amount_line

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_end_to_end_currency_workflow_multi_currency(
        self, transformer_multi_currency
    ):
        """Test complete currency workflow for multi-currency processor"""
        row_data = {
            "Transaction Date": "15/01/2024",
            "Transaction Remarks": "Payment $100 to international store",
            "Withdrawal Amount (INR )": "100",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "400",
            "S No.": "REF002",
        }

        # Should auto-detect USD
        with patch("builtins.print"):  # Suppress detection messages
            transformed = transformer_multi_currency._transform_transaction(row_data)

        # Verify currency is USD
        assert transformed["currency"] == "USD"

        # Test display
        with patch("builtins.print") as mock_print:
            transformer_multi_currency._display_transaction(transformed)

            print_calls = [call.args[0] for call in mock_print.call_args_list]
            currency_line = [line for line in print_calls if "Currency:" in line][0]
            amount_line = [line for line in print_calls if "Amount:" in line][0]

            assert "Currency: USD" in currency_line
            assert "$100.00" in amount_line
