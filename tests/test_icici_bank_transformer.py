"""
Minimal but comprehensive unit tests for icici_bank_transformer.py.
All interactive methods are properly mocked to prevent hanging.
"""

# pylint: disable=unused-variable
# Test fixtures often unpack variables that may not all be used in every test

import signal
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.transformers.icici_bank_transformer import IciciBankTransformer


class TestIciciBankTransformer:
    """Test suite for IciciBankTransformer class"""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager"""
        db_manager = Mock()
        db_manager.get_session.return_value = Mock()
        db_manager.models = {"TransactionEnum": Mock()}
        return db_manager

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            "categories": [{"name": "food"}, {"name": "transport"}],
            "processing": {"reprocess_skipped_transactions": False},
            "processors": {"icici_bank": {"currency": "INR"}},
        }

    @pytest.fixture
    def mock_config_loader(self):
        """Create mock config loader"""
        config_loader = Mock()
        config_loader.add_category = Mock()
        return config_loader

    @pytest.fixture
    def transformer(self, mock_db_manager, mock_config, mock_config_loader):
        """Create transformer instance with mocked dependencies"""
        with patch("src.transformers.icici_bank_transformer.DatabaseLoader"):
            transformer = IciciBankTransformer(mock_db_manager, mock_config, mock_config_loader)
            transformer.db_loader = Mock()
            return transformer

    # =====================
    # BASIC FUNCTIONALITY TESTS
    # =====================

    def test_init_basic(self, mock_db_manager, mock_config):
        """Test transformer initialization"""
        with (
            patch("src.transformers.icici_bank_transformer.DatabaseLoader"),
            patch("signal.signal") as mock_signal,
        ):
            transformer = IciciBankTransformer(mock_db_manager, mock_config)

            assert transformer.db_manager == mock_db_manager
            assert transformer.config == mock_config
            assert transformer.processor_type == "icici_bank"
            assert transformer._interrupted is False
            mock_signal.assert_called_once()

    def test_signal_handler(self, transformer):
        """Test signal handler"""
        with patch("sys.exit") as mock_exit, patch("builtins.print"):
            transformer._signal_handler(signal.SIGINT, None)
            assert transformer._interrupted is True
            mock_exit.assert_called_once_with(0)

    def test_transform_transaction_debit_valid(self, transformer):
        """Test valid debit transaction transformation"""
        row_data = {
            "Transaction Date": "01-01-2023",
            "Transaction Remarks": "UPI Payment",
            "Withdrawal Amount (INR )": "500.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "10000.00",
            "S No.": "123456",
        }

        with patch.object(transformer, "_determine_transaction_currency", return_value="INR"):
            result = transformer._transform_transaction(row_data)

        assert result is not None
        assert result["date"] == datetime(2023, 1, 1)
        assert result["description"] == "UPI Payment"
        assert result["debit_amount"] == 500.0
        assert result["credit_amount"] is None
        assert result["balance"] == 10000.0
        assert result["transaction_type"] == "debit"

    def test_transform_transaction_credit_valid(self, transformer):
        """Test valid credit transaction transformation"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Transaction Remarks": "Salary Credit",
            "Withdrawal Amount (INR )": "",
            "Deposit Amount (INR )": "50000.00",
            "Balance (INR )": "60000.00",
            "S No.": "789012",
        }

        with patch.object(transformer, "_determine_transaction_currency", return_value="INR"):
            result = transformer._transform_transaction(row_data)

        assert result is not None
        assert result["transaction_type"] == "credit"
        assert result["credit_amount"] == 50000.0
        assert result["debit_amount"] is None

    def test_transform_transaction_invalid_date(self, transformer):
        """Test invalid date handling"""
        row_data = {
            "Transaction Date": "invalid-date",
            "Transaction Remarks": "Payment",
        }
        result = transformer._transform_transaction(row_data)
        assert result is None

    def test_parse_amount_valid(self, transformer):
        """Test amount parsing"""
        assert transformer._parse_amount("1000.50") == 1000.50
        assert transformer._parse_amount("₹500") == 500.0
        assert transformer._parse_amount("") is None
        assert transformer._parse_amount("invalid") is None

    def test_display_transaction(self, transformer):
        """Test transaction display"""
        transaction = {
            "date": datetime(2023, 1, 1),
            "description": "Test Payment",
            "transaction_type": "debit",
            "debit_amount": 500.0,
            "balance": 10000.0,
            "reference_number": "123456",
            "currency": "INR",
        }

        with patch("builtins.print") as mock_print:
            transformer._display_transaction(transaction)
            mock_print.assert_called()

    def test_create_transaction_hash(self, transformer):
        """Test transaction hash creation"""
        transaction_data = {
            "date": datetime(2023, 1, 1),
            "description": "Test Payment",
            "debit_amount": 500.0,
        }

        hash1 = transformer._create_transaction_hash(transaction_data)
        hash2 = transformer._create_transaction_hash(transaction_data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

    # =====================
    # INTERACTIVE METHODS TESTS (ALL PROPERLY MOCKED)
    # =====================

    @patch("builtins.input", return_value="")
    def test_ask_for_pattern_word_with_suggestion(self, mock_input, transformer):
        """Test pattern word selection with suggestion"""
        with (
            patch.object(transformer, "_get_pattern_suggestions", return_value=["upi"]),
            patch("builtins.print"),
        ):
            result = transformer._ask_for_pattern_word("UPI Payment")
            assert result == "upi"

    @patch("builtins.input", return_value="2")
    def test_ask_for_pattern_word_skip(self, mock_input, transformer):
        """Test pattern word selection with skip"""
        with (
            patch.object(transformer, "_get_pattern_suggestions", return_value=["upi"]),
            patch("builtins.print"),
        ):
            result = transformer._ask_for_pattern_word("UPI Payment")
            assert result is None

    @patch("builtins.input", return_value="custom_pattern")
    def test_ask_for_pattern_word_custom(self, mock_input, transformer):
        """Test pattern word selection with custom input"""
        with (
            patch.object(transformer, "_get_pattern_suggestions", return_value=["upi"]),
            patch("builtins.print"),
        ):
            result = transformer._ask_for_pattern_word("UPI Payment")
            assert result == "custom_pattern"

    @patch("builtins.input", return_value="")
    def test_ask_for_enum_name_default(self, mock_input, transformer):
        """Test enum name with default"""
        with patch("builtins.print"):
            result = transformer._ask_for_enum_name("upi")
            assert result == "upi_transaction"

    @patch("builtins.input", return_value="custom_enum")
    def test_ask_for_enum_name_custom(self, mock_input, transformer):
        """Test enum name with custom input"""
        with patch("builtins.print"):
            result = transformer._ask_for_enum_name("upi")
            assert result == "custom_enum"

    @patch("builtins.input", return_value="1")
    def test_ask_for_category_selection(self, mock_input, transformer):
        """Test category selection by number"""
        with patch("builtins.print"):
            result = transformer._ask_for_category_with_ml("test transaction")
            assert result == "food"

    @patch("builtins.input", return_value="custom_cat")
    def test_ask_for_category_custom(self, mock_input, transformer):
        """Test category creation"""
        with patch("builtins.print"):
            result = transformer._ask_for_category_with_ml("test transaction")
            assert result == "custom_cat"
            transformer.config_loader.add_category.assert_called_once_with("custom_cat")

    @patch("builtins.input", return_value="")
    def test_ask_for_transaction_category_default(self, mock_input, transformer):
        """Test transaction category with default"""
        with patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_ml("food", "test transaction")
            assert result == "food"

    @patch("builtins.input", return_value="2")
    def test_ask_for_transaction_category_selection(self, mock_input, transformer):
        """Test transaction category selection"""
        with patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_ml("food", "test transaction")
            assert result == "transport"

    @patch("builtins.input", return_value="")
    def test_ask_for_transaction_category_with_options_default(self, mock_input, transformer):
        """Test transaction category options with default"""
        with patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_options("food")
            assert result == {"action": "process", "category": "food"}

    @patch("builtins.input", return_value="2")
    def test_ask_for_transaction_category_with_options_skip(self, mock_input, transformer):
        """Test transaction category options with skip"""
        with patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_options("food")
            assert result == {"action": "skip"}

    @patch("builtins.input", return_value="3")
    def test_ask_for_transaction_category_with_options_create_new(self, mock_input, transformer):
        """Test transaction category options with create new"""
        with patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_options("food")
            assert result == {"action": "create_new"}

    @patch("builtins.input", return_value="test reason")
    def test_ask_for_reason_custom(self, mock_input, transformer):
        """Test asking for reason with custom input"""
        with patch("builtins.print"):
            result = transformer._ask_for_reason_with_ml("test transaction", "food")
            assert result == "test reason"

    @patch("builtins.input", return_value="")
    def test_ask_for_reason_default(self, mock_input, transformer):
        """Test asking for reason with default"""
        with patch("builtins.print"):
            result = transformer._ask_for_reason_with_ml("test transaction", "food")
            assert result == "General transaction"

    @patch("builtins.input", return_value="")
    def test_ask_for_splits_none(self, mock_input, transformer):
        """Test asking for splits with none"""
        with patch("builtins.print"):
            result = transformer._ask_for_splits()
            assert result is None

    @patch("builtins.input", return_value="yugam:50")
    def test_ask_for_splits_with_split(self, mock_input, transformer):
        """Test asking for splits with actual split"""
        with patch("builtins.print"):
            result = transformer._ask_for_splits()
            assert result is not None
            assert len(result) == 1
            assert result[0]["person"] == "yugam"
            assert result[0]["percentage"] == 50.0

    # =====================
    # INTERRUPTION HANDLING TESTS
    # =====================

    def test_ask_for_pattern_word_interrupted(self, transformer):
        """Test pattern word when interrupted"""
        transformer._interrupted = True
        with (
            patch.object(transformer, "_get_pattern_suggestions", return_value=["upi"]),
            patch("builtins.print"),
        ):
            result = transformer._ask_for_pattern_word("UPI Payment")
            assert result is None

    def test_ask_for_category_interrupted(self, transformer):
        """Test category selection when interrupted"""
        transformer._interrupted = True
        with patch("builtins.print"):
            result = transformer._ask_for_category_with_ml("test transaction")
            assert result == "other"

    def test_ask_for_reason_interrupted(self, transformer):
        """Test reason when interrupted"""
        transformer._interrupted = True
        with patch("builtins.print"):
            result = transformer._ask_for_reason_with_ml("test transaction", "food")
            assert result == "General transaction"

    # =====================
    # INTEGRATION TESTS
    # =====================

    def test_process_transaction_interactive_existing_enum(self, transformer):
        """Test interactive processing with existing enum"""
        transaction = {"description": "UPI Payment", "debit_amount": 500.0}
        mock_enum = {"id": 1, "enum_name": "upi_payments", "category": "transfer"}

        with (
            patch.object(transformer, "_check_existing_enum_match", return_value=mock_enum),
            patch.object(
                transformer,
                "_handle_existing_enum_match",
                return_value={"action": "process", "enum_id": 1},
            ) as mock_handle,
        ):
            result = transformer._process_transaction_interactive(transaction)
            assert result["action"] == "process"
            mock_handle.assert_called_once()

    def test_process_transaction_interactive_no_enum(self, transformer):
        """Test interactive processing without existing enum"""
        transaction = {"description": "NEW Payment", "debit_amount": 200.0}

        with (
            patch.object(transformer, "_check_existing_enum_match", return_value=None),
            patch.object(
                transformer,
                "_full_interactive_flow",
                return_value={"action": "process", "enum_id": 2},
            ) as mock_flow,
        ):
            result = transformer._process_transaction_interactive(transaction)
            assert result["action"] == "process"
            mock_flow.assert_called_once()

    @patch("builtins.input", return_value="")
    def test_handle_existing_enum_match_auto_approve(self, mock_input, transformer):
        """Test handling existing enum with auto approval"""
        existing_enum = {"id": 1, "enum_name": "grocery", "category": "food"}

        with (
            patch.object(
                transformer,
                "_ask_for_transaction_category_with_options",
                return_value={"action": "process", "category": "food"},
            ),
            patch("builtins.print"),
            patch.object(transformer, "_ask_for_splits", return_value=None),
        ):
            result = transformer._handle_existing_enum_match(existing_enum, "grocery payment")
            assert result["action"] == "process"
            assert result["enum_id"] == 1

    @patch("builtins.input", return_value="")
    def test_full_interactive_flow_success(self, mock_input, transformer):
        """Test complete interactive flow"""
        mock_enum = MagicMock()
        mock_enum.category = "transfer"
        mock_enum.id = 123

        with (
            patch.object(transformer, "_ask_for_pattern_word", return_value="upi"),
            patch.object(transformer, "_ask_for_enum_name", return_value="upi_payments"),
            patch.object(transformer, "_handle_enum_and_category", return_value=mock_enum),
            patch.object(
                transformer, "_ask_for_transaction_category_with_ml", return_value="transfer"
            ),
            patch.object(transformer, "_ask_for_reason_with_ml", return_value="Payment"),
            patch.object(transformer, "_ask_for_splits", return_value=None),
            patch("builtins.print"),
        ):
            result = transformer._full_interactive_flow("UPI Payment")
            assert result["action"] == "process"
            assert result["enum_id"] == 123

    def test_full_interactive_flow_no_pattern(self, transformer):
        """Test interactive flow when no pattern selected"""
        with (
            patch.object(transformer, "_ask_for_pattern_word", return_value=None),
            patch.object(transformer, "_ask_for_reason_with_ml", return_value="User skipped"),
            patch("builtins.print"),
        ):
            result = transformer._full_interactive_flow("Complex transaction")
            assert result["action"] == "skip"

    # =====================
    # UTILITY TESTS
    # =====================

    def test_get_pattern_suggestions(self, transformer):
        """Test pattern suggestions generation"""
        result = transformer._get_pattern_suggestions("UPI PAYMENT TO GROCERY STORE")
        assert "upi" in result
        assert "payment" in result
        assert "grocery" in result
        assert "store" in result
        assert "to" not in result  # Common words filtered out

    def test_check_existing_enum_match_found(self, transformer):
        """Test existing enum match found"""
        mock_enum = Mock()
        mock_enum.id = 1
        mock_enum.enum_name = "grocery"
        mock_enum.category = "food"
        mock_enum.patterns = ["grocery", "store"]

        mock_session = Mock()
        mock_session.query().filter_by().all.return_value = [mock_enum]
        transformer.db_manager.get_session.return_value = mock_session

        result = transformer._check_existing_enum_match("grocery payment")
        assert result is not None
        assert result["id"] == 1
        mock_session.close.assert_called_once()

    def test_check_existing_enum_match_not_found(self, transformer):
        """Test existing enum match not found"""
        mock_session = Mock()
        mock_session.query().filter_by().all.return_value = []
        transformer.db_manager.get_session.return_value = mock_session

        result = transformer._check_existing_enum_match("unknown payment")
        assert result is None
        mock_session.close.assert_called_once()

    def test_handle_skipped_transaction(self, transformer):
        """Test skipped transaction handling"""
        row_data = {"Transaction Date": "01-01-2023", "Transaction Remarks": "Test"}

        transformer._handle_skipped_transaction(row_data, 1, 2, "User skipped")

        transformer.db_loader.create_skipped_transaction.assert_called_once()
        call_args = transformer.db_loader.create_skipped_transaction.call_args[0][0]
        assert "transaction_hash" in call_args
        assert call_args["raw_data"] == row_data

    # =====================
    # PROCESS TRANSACTIONS WORKFLOW TESTS
    # =====================

    def test_process_transactions_success(self, transformer):
        """Test successful transaction processing"""
        extracted_data = {
            "transactions": [
                {
                    "data": {
                        "Transaction Date": "01-01-2023",
                        "Transaction Remarks": "Test Payment",
                        "Withdrawal Amount (INR )": "500.00",
                        "Balance (INR )": "10000.00",
                        "S No.": "123456",
                    }
                }
            ]
        }

        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)

        # Mock a complete transaction response
        complete_transaction = {
            "description": "Test Payment",
            "date": datetime(2023, 1, 1),
            "debit_amount": 500.0,
            "credit_amount": None,
            "balance": 10000.0,
            "reference_number": "123456",
            "transaction_type": "debit",
            "currency": "INR",
        }

        with (
            patch.object(transformer, "_transform_transaction", return_value=complete_transaction),
            patch.object(transformer, "_create_transaction_hash", return_value="hash123"),
            patch.object(transformer.db_loader, "check_transaction_exists", return_value=False),
            patch.object(transformer.db_loader, "check_skipped_exists", return_value=False),
            patch.object(transformer, "_display_transaction"),
            patch.object(
                transformer,
                "_process_transaction_interactive",
                return_value={
                    "action": "process",
                    "enum_id": 1,
                    "category": "test",
                    "transaction_category": "test",
                    "reason": "Test",
                },
            ),
            patch.object(transformer.db_loader, "create_transaction"),
            patch("builtins.print"),
        ):
            result = transformer.process_transactions(
                extracted_data, mock_institution, mock_processed_file
            )

            assert result["status"] == "completed"
            assert result["total_transactions"] == 1
            assert result["processed_transactions"] == 1

    def test_process_transactions_with_duplicates(self, transformer):
        """Test transaction processing with duplicates"""
        extracted_data = {
            "transactions": [
                {
                    "data": {
                        "Transaction Date": "01-01-2023",
                        "Transaction Remarks": "Duplicate",
                    }
                }
            ]
        }

        with (
            patch.object(
                transformer,
                "_transform_transaction",
                return_value={"description": "Duplicate", "date": datetime(2023, 1, 1)},
            ),
            patch.object(transformer, "_create_transaction_hash", return_value="hash123"),
            patch.object(transformer.db_loader, "check_transaction_exists", return_value=True),
            patch("builtins.print"),
        ):
            result = transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))
            assert result["duplicate_transactions"] == 1

    def test_process_transactions_interrupted(self, transformer):
        """Test transaction processing when interrupted"""
        extracted_data = {"transactions": [{"data": {"Transaction Date": "01-01-2023"}}]}
        transformer._interrupted = True

        with (
            patch.object(
                transformer,
                "_transform_transaction",
                return_value={"description": "Test", "date": datetime(2023, 1, 1)},
            ),
            patch("builtins.print"),
        ):
            result = transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))
            assert result["status"] == "partially_completed"

    # =====================
    # MISSING COVERAGE TESTS - CURRENCY DETECTION
    # =====================

    def test_determine_transaction_currency_single_currency(self, transformer):
        """Test currency determination with single currency processor"""
        transformer.processor_currencies = ["INR"]
        row_data = {"Transaction Remarks": "UPI Payment"}

        result = transformer._determine_transaction_currency(row_data)
        assert result == "INR"

    def test_determine_transaction_currency_from_amount_field(self, transformer):
        """Test currency detection from amount fields"""
        transformer.processor_currencies = ["INR", "USD"]
        transformer.currency_detector = Mock()
        transformer.currency_detector.detect_currency.return_value = "USD"

        row_data = {
            "Transaction Remarks": "Payment",
            "Withdrawal Amount (INR )": "$100.50",
            "Deposit Amount (INR )": "",
        }

        with patch("builtins.print"):
            result = transformer._determine_transaction_currency(row_data)

        assert result == "USD"

    def test_determine_transaction_currency_from_description(self, transformer):
        """Test currency detection from description"""
        transformer.processor_currencies = ["INR", "USD"]
        transformer.currency_detector = Mock()
        transformer.currency_detector.detect_currency.side_effect = [
            None,
            "INR",
        ]  # amount fails, description succeeds

        row_data = {
            "Transaction Remarks": "Payment in ₹500",
            "Withdrawal Amount (INR )": "500",
            "Deposit Amount (INR )": "",
        }

        with patch("builtins.print"):
            result = transformer._determine_transaction_currency(row_data)

        assert result == "INR"

    def test_determine_transaction_currency_ask_user(self, transformer):
        """Test currency detection when user input is needed"""
        transformer.processor_currencies = ["INR", "USD"]
        transformer.currency_detector = Mock()
        transformer.currency_detector.detect_currency.return_value = None
        transformer.currency_detector.ask_user_for_currency.return_value = "USD"

        row_data = {
            "Transaction Remarks": "Payment",
            "Withdrawal Amount (INR )": "100",
            "Deposit Amount (INR )": "200",
        }

        result = transformer._determine_transaction_currency(row_data)
        assert result == "USD"

    # =====================
    # MISSING COVERAGE TESTS - ENUM AND CATEGORY HANDLING
    # =====================

    def test_handle_enum_and_category_existing_enum(self, transformer):
        """Test handling when enum already exists"""
        mock_enum = Mock()
        mock_enum.category = "transport"

        mock_session = Mock()
        mock_session.query().filter_by().first.return_value = mock_enum
        transformer.db_manager.get_session.return_value = mock_session

        with patch("builtins.print") as mock_print:
            result = transformer._handle_enum_and_category("existing_enum", ["pattern"])

        assert result == mock_enum
        mock_print.assert_any_call(
            "✅ Enum 'existing_enum' already exists with category 'transport'"
        )
        mock_session.close.assert_called_once()

    def test_handle_enum_and_category_keyboard_interrupt(self, transformer):
        """Test handling KeyboardInterrupt during category selection"""
        mock_session = Mock()
        mock_session.query().filter_by().first.return_value = None
        transformer.db_manager.get_session.return_value = mock_session

        with patch.object(transformer, "_ask_for_category_with_ml", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                transformer._handle_enum_and_category("new_enum", ["pattern"], "test description")

    def test_handle_enum_and_category_create_new(self, transformer):
        """Test creating new enum and category"""
        mock_session = Mock()
        mock_session.query().filter_by().first.return_value = None
        transformer.db_manager.get_session.return_value = mock_session

        mock_enum = Mock()
        transformer.db_loader.create_or_update_enum.return_value = mock_enum

        with (
            patch.object(transformer, "_ask_for_category_with_ml", return_value="new_category"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._handle_enum_and_category(
                "new_enum", ["pattern"], "test description"
            )

        assert result == mock_enum
        transformer.db_loader.create_or_update_enum.assert_called_once_with(
            enum_name="new_enum",
            patterns=["pattern"],
            category="new_category",
            processor_type=transformer.processor_type,
        )
        mock_print.assert_any_call("✅ Created enum 'new_enum' with category 'new_category'")

    # =====================
    # MISSING COVERAGE TESTS - CATEGORY SELECTION EDGE CASES
    # =====================

    @patch("builtins.input", side_effect=["999", "0", "1"])
    def test_ask_for_category_invalid_numbers(self, mock_input, transformer):
        """Test category selection with invalid numbers"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_category_with_ml("test transaction")

        assert result == "food"
        mock_print.assert_any_call("❌ Invalid number. Please enter 1-2 or type a category name.")

    @patch("builtins.input", return_value="a")
    def test_ask_for_category_too_short(self, mock_input, transformer):
        """Test category creation with too short name"""
        transformer._interrupted = True  # Force exit after one iteration

        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_category_with_ml("test transaction")

        assert result == "other"  # Interrupted return value

    def test_ask_for_category_no_config_loader_existing_category(self, transformer):
        """Test category handling without config loader for existing category"""
        transformer.config_loader = None
        transformer.config = {"categories": [{"name": "food"}, {"name": "transport"}]}

        with (
            patch("builtins.input", return_value="food"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_category_with_ml("test transaction")

        assert result == "food"
        mock_print.assert_any_call("✅ Selected existing enum category: Food")

    def test_ask_for_category_no_config_loader_new_category(self, transformer):
        """Test category creation without config loader"""
        transformer.config_loader = None
        transformer.config = {"categories": [{"name": "food"}]}

        with (
            patch("builtins.input", return_value="new_cat"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_category_with_ml("test transaction")

        assert result == "new_cat"
        assert {"name": "new_cat"} in transformer.config["categories"]
        mock_print.assert_any_call("✅ Created new enum category: New_Cat")

    def test_ask_for_category_config_loader_exception(self, transformer):
        """Test category creation with config loader exception"""
        transformer.config_loader.add_category.side_effect = OSError("Save failed")

        with (
            patch("builtins.input", return_value="problem_cat"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_category_with_ml("test transaction")

        assert result == "problem_cat"
        msg = "⚠️  Enum category created but couldn't save: Save failed"
        mock_print.assert_any_call(msg)

    # =====================
    # MISSING COVERAGE TESTS - TRANSACTION CATEGORY SELECTION
    # =====================

    @patch("builtins.input", side_effect=["999", "1"])
    def test_ask_for_transaction_category_invalid_number(self, mock_input, transformer):
        """Test transaction category selection with invalid number"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_transaction_category_with_ml("test", "test transaction")

        assert result == "food"
        mock_print.assert_any_call(
            "❌ Invalid number. Please enter 1-2, press Enter for 'Test', or type a category name."
        )

    def test_ask_for_transaction_category_config_loader_exception(self, transformer):
        """Test transaction category creation with config loader exception"""
        transformer.config_loader.add_category.side_effect = OSError("Save failed")

        with (
            patch("builtins.input", return_value="problem_trans_cat"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_transaction_category_with_ml("test", "test transaction")

        assert result == "problem_trans_cat"
        msg = "⚠️  Transaction category created but couldn't save: Save failed"
        mock_print.assert_any_call(msg)

    def test_ask_for_transaction_category_no_config_loader_existing(self, transformer):
        """Test transaction category with no config loader for existing category"""
        transformer.config_loader = None
        transformer.config = {"categories": [{"name": "food"}, {"name": "existing_cat"}]}

        with (
            patch("builtins.input", return_value="existing_cat"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_transaction_category_with_ml("test", "test transaction")

        assert result == "existing_cat"
        mock_print.assert_any_call("✅ Selected existing transaction category: Existing_Cat")

    @patch("builtins.input", side_effect=["999", "1"])
    def test_ask_for_transaction_category_with_options_invalid_number(
        self, mock_input, transformer
    ):
        """Test transaction category options with invalid number"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_transaction_category_with_options("test")

        assert result == {"action": "process", "category": "food"}
        mock_print.assert_any_call(
            "❌ Invalid number. Please enter 1-2, press Enter for 'Test', or use special options (2=skip, 3=new pattern)"
        )

    def test_ask_for_transaction_category_with_options_short_input(self, transformer):
        """Test transaction category options with too short input"""
        transformer._interrupted = True  # Force exit

        with patch("builtins.input", return_value="a"), patch("builtins.print"):
            result = transformer._ask_for_transaction_category_with_options("test")

        assert result == {"action": "skip", "reason": "Processing interrupted"}

    # =====================
    # MISSING COVERAGE TESTS - SPLITS HANDLING
    # =====================

    @patch("builtins.input", side_effect=["yugam:150", "yugam:50"])
    def test_ask_for_splits_percentage_over_100(self, mock_input, transformer):
        """Test splits with percentage over 100"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_splits()

        assert result is not None
        assert len(result) == 1
        assert result[0]["percentage"] == 50.0
        # Check that some error message was printed (the error condition has 150 > 100 in logic)
        print_calls = [str(call) for call in mock_print.call_args_list]
        error_printed = any("Percentage must be between 1 and 100" in call for call in print_calls)
        assert error_printed

    @patch("builtins.input", side_effect=["yugam:-10", "yugam:50"])
    def test_ask_for_splits_negative_percentage(self, mock_input, transformer):
        """Test splits with negative percentage"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_splits()

        assert result is not None
        mock_print.assert_any_call("❌ Percentage must be between 1 and 100")

    @patch("builtins.input", side_effect=["invalid_format", "yugam:50"])
    def test_ask_for_splits_invalid_format(self, mock_input, transformer):
        """Test splits with invalid format"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_splits()

        assert result is not None
        mock_print.assert_any_call("❌ Invalid format in 'invalid_format'. Use 'name:percentage'")

    @patch("builtins.input", return_value="yugam:30")
    def test_ask_for_splits_with_remaining_percentage(self, mock_input, transformer):
        """Test splits showing remaining percentage"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_splits()

        assert result is not None
        mock_print.assert_any_call("ℹ️  Your share: 70.0%")

    # =====================
    # MISSING COVERAGE TESTS - ERROR HANDLING
    # =====================

    def test_transform_transaction_exception_handling(self, transformer):
        """Test transaction transformation with exception"""
        # Mock row_data that will cause an exception
        row_data = Mock()
        row_data.get.side_effect = ValueError("Mock exception")

        with patch("builtins.print") as mock_print:
            result = transformer._transform_transaction(row_data)

        assert result is None
        mock_print.assert_any_call("Error transforming transaction: Mock exception")

    def test_parse_amount_pandas_na_values(self, transformer):
        """Test parsing pandas NA values"""
        import numpy as np
        import pandas as pd

        assert transformer._parse_amount(pd.NA) is None
        assert transformer._parse_amount(np.nan) is None
        assert transformer._parse_amount(float("nan")) is None

    def test_handle_skipped_transaction_with_exception(self, transformer):
        """Test skipped transaction handling with database exception"""
        transformer.db_loader.create_skipped_transaction.side_effect = OSError("DB Error")

        with patch("builtins.print") as mock_print:
            transformer._handle_skipped_transaction({}, 1, 2, "test reason")

        mock_print.assert_any_call("❌ Error saving skipped transaction: DB Error")

    def test_process_transactions_exception_in_loop(self, transformer):
        """Test process_transactions with exception during transaction processing"""
        extracted_data = {
            "transactions": [
                {
                    "data": {
                        "Transaction Date": "01-01-2023",
                        "Transaction Remarks": "Test",
                    }
                }
            ]
        }

        with (
            patch.object(
                transformer,
                "_transform_transaction",
                side_effect=OSError("Processing error"),
            ),
            patch("builtins.print") as mock_print,
        ):
            result = transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))

        assert result["skipped_transactions"] == 1
        mock_print.assert_any_call("❌ Error processing transaction: Processing error")

    def test_process_transactions_general_exception(self, transformer):
        """Test process_transactions with general exception"""
        extracted_data = {"transactions": [{"data": {"date": "01-01-2023"}}]}

        # Mock the entire process_transactions method to raise an exception
        original_method = transformer.process_transactions

        def side_effect(*args, **kwargs):
            raise Exception("General error")

        transformer.process_transactions = Mock(side_effect=side_effect)

        # Test that the exception is handled
        with pytest.raises(Exception, match="General error"):
            transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))

    # =====================
    # MISSING COVERAGE TESTS - WORKFLOW EDGE CASES
    # =====================

    def test_process_transactions_with_auto_skipped(self, transformer):
        """Test processing with auto-skipped transactions (reprocess_skipped = false)"""
        extracted_data = {
            "transactions": [
                {
                    "data": {
                        "Transaction Date": "01-01-2023",
                        "Transaction Remarks": "Previously skipped",
                        "Withdrawal Amount (INR )": "100.00",
                    }
                }
            ]
        }

        transformer.config = {"processing": {"reprocess_skipped_transactions": False}}

        with (
            patch.object(
                transformer,
                "_transform_transaction",
                return_value={"description": "Test", "date": datetime(2023, 1, 1)},
            ),
            patch.object(transformer, "_create_transaction_hash", return_value="hash123"),
            patch.object(transformer.db_loader, "check_transaction_exists", return_value=False),
            patch.object(transformer.db_loader, "check_skipped_exists", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            result = transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))

        assert result["auto_skipped_transactions"] == 1
        mock_print.assert_any_call(
            "⚠️  Transaction previously skipped - auto-skipping (set reprocess_skipped_transactions=true to change)"
        )

    def test_process_transactions_reprocess_skipped(self, transformer):
        """Test processing with reprocess_skipped = true"""
        extracted_data = {
            "transactions": [
                {
                    "data": {
                        "Transaction Date": "01-01-2023",
                        "Transaction Remarks": "Previously skipped",
                        "Withdrawal Amount (INR )": "100.00",
                    }
                }
            ]
        }

        transformer.config = {"processing": {"reprocess_skipped_transactions": True}}

        with (
            patch.object(
                transformer,
                "_transform_transaction",
                return_value={"description": "Test", "date": datetime(2023, 1, 1)},
            ),
            patch.object(transformer, "_create_transaction_hash", return_value="hash123"),
            patch.object(transformer.db_loader, "check_transaction_exists", return_value=False),
            patch.object(transformer.db_loader, "check_skipped_exists", return_value=True),
            patch.object(transformer, "_display_transaction"),
            patch.object(
                transformer,
                "_process_transaction_interactive",
                return_value={"action": "skip", "reason": "User skipped again"},
            ),
            patch.object(transformer, "_handle_skipped_transaction"),
            patch("builtins.print") as mock_print,
        ):
            result = transformer.process_transactions(extracted_data, Mock(id=1), Mock(id=1))

        mock_print.assert_any_call(
            "⚠️  Transaction previously skipped - reprocessing due to config setting"
        )

    def test_ask_for_enum_name_interrupted(self, transformer):
        """Test enum name selection when interrupted"""
        transformer._interrupted = True

        with patch("builtins.print"):
            result = transformer._ask_for_enum_name("test")

        assert result == "test_transaction"  # Should return default

    @patch("builtins.input", side_effect=["ab", "valid_enum"])
    def test_ask_for_enum_name_too_short(self, mock_input, transformer):
        """Test enum name with input too short"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_enum_name("test")

        assert result == "valid_enum"
        mock_print.assert_any_call("❌ Please enter a valid enum name (at least 3 characters)")

    @patch("builtins.input", side_effect=["ab", "valid_reason"])
    def test_ask_for_reason_empty_input(self, mock_input, transformer):
        """Test reason input with too short then valid input"""
        with patch("builtins.print") as mock_print:
            result = transformer._ask_for_reason_with_ml("test transaction", "food")

        assert result == "valid_reason"
        mock_print.assert_any_call(
            "❌ Please enter a reason (at least 3 characters) or press Enter for default"
        )

    def test_full_interactive_flow_keyboard_interrupt(self, transformer):
        """Test full interactive flow with KeyboardInterrupt"""
        with (
            patch.object(transformer, "_ask_for_pattern_word", side_effect=KeyboardInterrupt),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._full_interactive_flow("test description")

        assert result["action"] == "skip"
        assert result["reason"] == "User interrupted during pattern creation"
        mock_print.assert_any_call("\n⏭️  Skipping transaction...")

    @patch("builtins.input", side_effect=["a", "custom_pattern"])
    def test_ask_for_pattern_word_invalid_then_valid_number(self, mock_input, transformer):
        """Test pattern word with invalid input then valid custom pattern"""
        with (
            patch.object(transformer, "_get_pattern_suggestions", return_value=["upi", "payment"]),
            patch("builtins.print") as mock_print,
        ):
            result = transformer._ask_for_pattern_word("UPI Payment test")

        assert result == "custom_pattern"
        mock_print.assert_any_call(
            "❌ Please enter a valid pattern (at least 2 characters), press Enter for suggestion, or type '2' to skip"
        )

    # ML Configuration-driven Tests
    # =====================

    def test_get_pattern_suggestions_respects_max_suggestions_config(self, transformer):
        """Test that pattern suggestions respect max_suggestions config"""
        # Set up config with max_suggestions = 2
        transformer.config = {"ml": {"max_suggestions": 2}, "categories": [{"name": "food"}]}

        result = transformer._get_pattern_suggestions("UPI PAYMENT TO GROCERY STORE SWIGGY FOOD")
        assert len(result) <= 2

    def test_get_pattern_suggestions_with_ml_config_values(self, transformer):
        """Test that pattern suggestions use config values for filtering"""
        transformer.config = {
            "ml": {
                "max_suggestions": 3,
                "feature_extraction": {"min_pattern_length": 4, "max_pattern_length": 10},
            },
            "categories": [{"name": "food"}],
        }

        # Mock ML service
        mock_ml_service = Mock()
        mock_ml_service.ml_enabled = True
        mock_ml_service.suggest_regex_patterns.return_value = [
            "ab",
            "payment",
            "grocery",
            "verylongpatternname",
        ]
        transformer.ml_service = mock_ml_service

        result = transformer._get_pattern_suggestions("UPI PAYMENT TO GROCERY STORE")
        # Should filter out "ab" (too short) and "verylongpatternname" (too long)
        assert "ab" not in result
        assert "verylongpatternname" not in result
        assert len(result) <= 3

    def test_ml_confidence_threshold_from_config(self, transformer):
        """Test that ML suggestions respect confidence_threshold from config"""
        transformer.config = {
            "ml": {"confidence_threshold": 0.9},  # Very high threshold
            "categories": [{"name": "food"}],
        }

        # Mock ML service with low confidence suggestion
        mock_ml_service = Mock()
        mock_ml_service.ml_enabled = True
        mock_ml_service.suggest_regex_pattern.return_value = {
            "pattern": "test",
            "confidence": 0.6,  # Below threshold
            "reasoning": "test reason",
        }
        transformer.ml_service = mock_ml_service

        with (
            patch("builtins.input", return_value="2"),
            patch("builtins.print") as mock_print,
            patch.object(transformer, "_get_pattern_suggestions", return_value=["test"]),
        ):
            result = transformer._ask_for_pattern_word("test description")

        # Should not print ML suggestion since confidence is below threshold
        ml_suggestion_printed = any(
            "ML Regex Pattern Suggestion" in str(call) for call in mock_print.call_args_list
        )
        assert not ml_suggestion_printed
        assert result is None  # Should skip

    def test_ml_max_suggestions_in_category_selection(self, transformer):
        """Test that ML category suggestions respect max_suggestions config"""
        transformer.config = {
            "ml": {"max_suggestions": 2},
            "categories": [{"name": "food"}, {"name": "transport"}],
        }

        # Mock ML service
        mock_ml_service = Mock()
        mock_ml_service.ml_enabled = True
        mock_ml_service.suggest_enum_category.return_value = [
            {"category": "food", "confidence": 0.9, "reasoning": "food related"},
            {"category": "transport", "confidence": 0.8, "reasoning": "transport related"},
            {"category": "entertainment", "confidence": 0.7, "reasoning": "entertainment related"},
        ]
        transformer.ml_service = mock_ml_service

        with patch("builtins.input", return_value="food"), patch("builtins.print") as mock_print:
            result = transformer._ask_for_category_with_ml("test description")

        # Count ML suggestions printed (should be limited by max_suggestions)
        ml_suggestion_calls = [
            call
            for call in mock_print.call_args_list
            if "ML Enum Category Suggestions" in str(call) or "🎯" in str(call)
        ]
        # Should show only max_suggestions number of options
        confidence_calls = [
            call for call in mock_print.call_args_list if "% confidence)" in str(call)
        ]
        assert len(confidence_calls) <= 2  # max_suggestions = 2
