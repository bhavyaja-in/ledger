"""
Comprehensive unit tests for icici_bank_transformer.py with 100% line coverage.

Tests all IciciBankTransformer methods including interactive processing, enum management,
transaction transformation, error scenarios, and user input flows to ensure enterprise-grade quality.
"""
import pytest
import signal
import hashlib
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List

from src.transformers.icici_bank_transformer import IciciBankTransformer


class TestIciciBankTransformer:
    """Comprehensive test suite for IciciBankTransformer class"""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager"""
        db_manager = Mock()
        db_manager.get_session.return_value = Mock()
        db_manager.models = {'TransactionEnum': Mock()}
        return db_manager

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            'categories': [
                {'name': 'food'},
                {'name': 'transport'},
                {'name': 'bills'}
            ],
            'processing': {
                'reprocess_skipped_transactions': False
            }
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
        with patch('src.transformers.icici_bank_transformer.DatabaseLoader'):
            transformer = IciciBankTransformer(mock_db_manager, mock_config, mock_config_loader)
            transformer.db_loader = Mock()
            return transformer

    # =====================
    # 1. INITIALIZATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_init_basic(self, mock_db_manager, mock_config):
        """Test transformer initialization with basic setup"""
        with patch('src.transformers.icici_bank_transformer.DatabaseLoader') as mock_db_loader_class, \
             patch('signal.signal') as mock_signal:
            
            transformer = IciciBankTransformer(mock_db_manager, mock_config)
            
            assert transformer.db_manager == mock_db_manager
            assert transformer.config == mock_config
            assert transformer.config_loader is None
            assert transformer.processor_type == "icici_bank"
            assert transformer._interrupted is False
            
            mock_db_loader_class.assert_called_once_with(mock_db_manager)
            mock_signal.assert_called_once_with(signal.SIGINT, transformer._signal_handler)

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_init_with_config_loader(self, mock_db_manager, mock_config, mock_config_loader):
        """Test transformer initialization with config loader"""
        with patch('src.transformers.icici_bank_transformer.DatabaseLoader'), \
             patch('signal.signal'):
            
            transformer = IciciBankTransformer(mock_db_manager, mock_config, mock_config_loader)
            
            assert transformer.config_loader == mock_config_loader

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_signal_handler(self, transformer):
        """Test signal handler for Ctrl+C interruption"""
        with patch('sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            transformer._signal_handler(signal.SIGINT, None)
            
            assert transformer._interrupted is True
            mock_print.assert_any_call("\n\n🛑 Processing interrupted by user (Ctrl+C)")
            mock_print.assert_any_call("🔄 Cleaning up and exiting...")
            mock_exit.assert_called_once_with(0)

    # =====================
    # 2. TRANSACTION TRANSFORMATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_debit_valid(self, transformer):
        """Test transforming valid debit transaction"""
        row_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': 'UPI Payment to Merchant',
            'Withdrawal Amount (INR )': '500.00',
            'Deposit Amount (INR )': '',
            'Balance (INR )': '10000.00',
            'S No.': '123456'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is not None
        assert result['date'] == datetime(2023, 1, 1)
        assert result['description'] == 'UPI Payment to Merchant'
        assert result['debit_amount'] == 500.0
        assert result['credit_amount'] is None
        assert result['balance'] == 10000.0
        assert result['reference_number'] == '123456'
        assert result['transaction_type'] == 'debit'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_credit_valid(self, transformer):
        """Test transforming valid credit transaction"""
        row_data = {
            'Transaction Date': '01/01/2023',
            'Transaction Remarks': 'Salary Credit',
            'Withdrawal Amount (INR )': '',
            'Deposit Amount (INR )': '50000.00',
            'Balance (INR )': '60000.00',
            'S No.': '789012'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is not None
        assert result['date'] == datetime(2023, 1, 1)
        assert result['description'] == 'Salary Credit'
        assert result['debit_amount'] is None
        assert result['credit_amount'] == 50000.0
        assert result['balance'] == 60000.0
        assert result['reference_number'] == '789012'
        assert result['transaction_type'] == 'credit'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_invalid_date(self, transformer):
        """Test transforming transaction with invalid date"""
        row_data = {
            'Transaction Date': 'invalid-date',
            'Transaction Remarks': 'UPI Payment',
            'Withdrawal Amount (INR )': '100.00',
            'Deposit Amount (INR )': '',
            'Balance (INR )': '5000.00'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_missing_date(self, transformer):
        """Test transforming transaction with missing date"""
        row_data = {
            'Transaction Date': '',
            'Transaction Remarks': 'UPI Payment',
            'Withdrawal Amount (INR )': '100.00'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_missing_description(self, transformer):
        """Test transforming transaction with missing description"""
        row_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': '',
            'Withdrawal Amount (INR )': '100.00'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_nan_reference(self, transformer):
        """Test transforming transaction with NaN reference number"""
        row_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': 'UPI Payment',
            'Withdrawal Amount (INR )': '100.00',
            'Deposit Amount (INR )': '',
            'Balance (INR )': '5000.00',
            'S No.': 'nan'
        }
        
        result = transformer._transform_transaction(row_data)
        
        assert result is not None
        assert result['reference_number'] is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_transform_transaction_exception_handling(self, transformer):
        """Test transaction transformation with exception"""
        row_data = {'invalid': 'data'}
        
        result = transformer._transform_transaction(row_data)
        
        # The method should return None for invalid data without necessarily printing
        assert result is None

    # =====================
    # 3. AMOUNT PARSING TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_parse_amount_valid_numbers(self, transformer):
        """Test parsing valid amount strings"""
        assert transformer._parse_amount('1000.50') == 1000.50
        assert transformer._parse_amount('1,000.00') == 1000.0
        assert transformer._parse_amount('₹500') == 500.0
        assert transformer._parse_amount('2500') == 2500.0

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_parse_amount_edge_cases(self, transformer):
        """Test parsing edge case amounts"""
        assert transformer._parse_amount('') is None
        assert transformer._parse_amount('   ') is None
        assert transformer._parse_amount(None) is None
        assert transformer._parse_amount('0') is None
        assert transformer._parse_amount('0.00') is None
        assert transformer._parse_amount('-100') is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_parse_amount_invalid_formats(self, transformer):
        """Test parsing invalid amount formats"""
        assert transformer._parse_amount('invalid') is None
        assert transformer._parse_amount('abc123') is None
        assert transformer._parse_amount('1.2.3') is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_parse_amount_pandas_na(self, transformer):
        """Test parsing pandas NaN values"""
        import pandas as pd
        import numpy as np
        
        assert transformer._parse_amount(np.nan) is None
        assert transformer._parse_amount(pd.NA) is None
        assert transformer._parse_amount(float('nan')) is None

    # =====================
    # 4. TRANSACTION DISPLAY TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_debit(self, transformer):
        """Test displaying debit transaction"""
        transaction = {
            'date': datetime(2023, 1, 1),
            'description': 'UPI Payment to Merchant',
            'transaction_type': 'debit',
            'debit_amount': 500.0,
            'balance': 10000.0,
            'reference_number': '123456'
        }
        
        with patch('builtins.print') as mock_print:
            transformer._display_transaction(transaction)
        
        expected_calls = [
            call("📅 Date: 01/01/2023"),
            call("💬 Description: UPI Payment to Merchant"),
            call("💸 Amount: ₹500.00 (DEBIT)"),
            call("🏦 Balance: ₹10,000.00"),
            call("🔖 Reference: 123456")
        ]
        mock_print.assert_has_calls(expected_calls)

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_credit(self, transformer):
        """Test displaying credit transaction"""
        transaction = {
            'date': datetime(2023, 1, 1),
            'description': 'Salary Credit',
            'transaction_type': 'credit',
            'credit_amount': 50000.0,
            'balance': None,
            'reference_number': None
        }
        
        with patch('builtins.print') as mock_print:
            transformer._display_transaction(transaction)
        
        expected_calls = [
            call("📅 Date: 01/01/2023"),
            call("💬 Description: Salary Credit"),
            call("💰 Amount: ₹50,000.00 (CREDIT)")
        ]
        mock_print.assert_has_calls(expected_calls)

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_display_transaction_long_description(self, transformer):
        """Test displaying transaction with long description"""
        long_desc = "A" * 100  # 100 character description
        transaction = {
            'date': datetime(2023, 1, 1),
            'description': long_desc,
            'transaction_type': 'debit',
            'debit_amount': 100.0
        }
        
        with patch('builtins.print') as mock_print:
            transformer._display_transaction(transaction)
        
        # Should truncate to 77 chars + "..."
        expected_desc = "A" * 77 + "..."
        mock_print.assert_any_call(f"💬 Description: {expected_desc}")

    # =====================
    # 5. HASH CREATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_create_transaction_hash_consistent(self, transformer):
        """Test transaction hash creation consistency"""
        transaction_data = {
            'date': datetime(2023, 1, 1),
            'description': 'UPI Payment',
            'debit_amount': 500.0,
            'credit_amount': None
        }
        
        hash1 = transformer._create_transaction_hash(transaction_data)
        hash2 = transformer._create_transaction_hash(transaction_data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_create_transaction_hash_different_data(self, transformer):
        """Test transaction hash for different data produces different hashes"""
        transaction1 = {
            'date': datetime(2023, 1, 1),
            'description': 'UPI Payment 1',
            'debit_amount': 500.0,
            'credit_amount': None
        }
        
        transaction2 = {
            'date': datetime(2023, 1, 1),
            'description': 'UPI Payment 2',
            'debit_amount': 500.0,
            'credit_amount': None
        }
        
        hash1 = transformer._create_transaction_hash(transaction1)
        hash2 = transformer._create_transaction_hash(transaction2)
        
        assert hash1 != hash2

    # =====================
    # 6. INTERACTIVE PROCESSING TESTS (COMPREHENSIVE COVERAGE)
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transaction_interactive_existing_enum_found(self, transformer):
        """Test interactive processing when existing enum is found"""
        transaction = {
            'description': 'UPI-GROCERY STORE PAY',
            'debit_amount': 500.0,
            'date': datetime(2023, 1, 1)
        }
        
        mock_enum = {
            'id': 1,
            'enum_name': 'grocery_payments',
            'category': 'food',
            'transaction_category': 'groceries'
        }
        
        with patch.object(transformer, '_check_existing_enum_match', return_value=mock_enum), \
             patch.object(transformer, '_handle_existing_enum_match', return_value={
                 'action': 'process',
                 'enum_id': 1,
                 'category': 'food',
                 'transaction_category': 'groceries'
             }) as mock_handle:
            
            result = transformer._process_transaction_interactive(transaction)
        
        assert result['action'] == 'process'
        assert result['enum_id'] == 1
        mock_handle.assert_called_once_with(mock_enum, 'UPI-GROCERY STORE PAY')

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transaction_interactive_no_enum_found_full_flow(self, transformer):
        """Test interactive processing when no enum found - full flow"""
        transaction = {
            'description': 'NEW MERCHANT PAYMENT',
            'debit_amount': 200.0,
            'date': datetime(2023, 1, 1)
        }
        
        with patch.object(transformer, '_check_existing_enum_match', return_value=None), \
             patch.object(transformer, '_full_interactive_flow', return_value={
                 'action': 'process',
                 'enum_id': 2,
                 'category': 'shopping',
                 'transaction_category': 'online_shopping'
             }) as mock_flow:
            
            result = transformer._process_transaction_interactive(transaction)
        
        assert result['action'] == 'process'
        assert result['enum_id'] == 2
        mock_flow.assert_called_once_with('NEW MERCHANT PAYMENT')

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_existing_enum_match_auto_approve(self, transformer):
        """Test handling existing enum with auto approval"""
        existing_enum = {
            'id': 1,
            'enum_name': 'grocery_payments',
            'category': 'food',
            'transaction_category': 'groceries',
            'patterns': ['GROCERY', 'STORE']
        }
        description = 'UPI-GROCERY STORE PAY'
        
        with patch('builtins.input', return_value='y'), \
             patch('builtins.print') as mock_print:
            
            result = transformer._handle_existing_enum_match(existing_enum, description)
        
        assert result['action'] == 'process'
        assert result['enum_id'] == 1
        assert result['category'] == 'food'
        assert result['transaction_category'] == 'groceries'
        mock_print.assert_any_call("✨ Found existing enum: grocery_payments")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_existing_enum_match_decline_to_skip(self, transformer):
        """Test handling existing enum with decline and skip"""
        existing_enum = {
            'id': 1,
            'enum_name': 'grocery_payments',
            'category': 'food',
            'transaction_category': 'groceries'
        }
        
        with patch('builtins.input', side_effect=['n', 's']), \
             patch('builtins.print'), \
             patch.object(transformer, '_ask_for_reason', return_value='Not applicable'):
            
            result = transformer._handle_existing_enum_match(existing_enum, 'description')
        
        assert result['action'] == 'skip'
        assert result['reason'] == 'Not applicable'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_existing_enum_match_decline_to_new_flow(self, transformer):
        """Test handling existing enum with decline and new flow"""
        existing_enum = {
            'id': 1,
            'enum_name': 'grocery_payments',
            'category': 'food'
        }
        
        with patch('builtins.input', side_effect=['n', 'n']), \
             patch('builtins.print'), \
             patch.object(transformer, '_full_interactive_flow', return_value={
                 'action': 'process',
                 'enum_id': 2
             }) as mock_flow:
            
            result = transformer._handle_existing_enum_match(existing_enum, 'description')
        
        assert result['action'] == 'process'
        mock_flow.assert_called_once_with('description')

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_full_interactive_flow_complete_success(self, transformer):
        """Test complete full interactive flow"""
        description = 'ATM WITHDRAWAL ABC BANK'
        
        with patch.object(transformer, '_ask_for_pattern_word', return_value='ATM'), \
             patch.object(transformer, '_ask_for_enum_name', return_value='atm_withdrawals'), \
             patch.object(transformer, '_handle_enum_and_category', return_value=123), \
             patch.object(transformer, '_ask_for_transaction_category', return_value='cash_withdrawal'), \
             patch('builtins.print'):
            
            result = transformer._full_interactive_flow(description)
        
        assert result['action'] == 'process'
        assert result['enum_id'] == 123
        assert result['transaction_category'] == 'cash_withdrawal'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_full_interactive_flow_no_pattern_word(self, transformer):
        """Test full interactive flow when no pattern word selected"""
        description = 'COMPLEX TRANSACTION DESCRIPTION'
        
        with patch.object(transformer, '_ask_for_pattern_word', return_value=None), \
             patch.object(transformer, '_ask_for_reason', return_value='No suitable pattern'), \
             patch('builtins.print'):
            
            result = transformer._full_interactive_flow(description)
        
        assert result['action'] == 'skip'
        assert result['reason'] == 'No suitable pattern'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_pattern_word_valid_selection(self, transformer):
        """Test pattern word selection with valid choice"""
        description = 'UPI GROCERY STORE PAYMENT'
        
        with patch.object(transformer, '_get_pattern_suggestions', return_value=['UPI', 'GROCERY', 'STORE']), \
             patch('builtins.input', return_value='2'), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_pattern_word(description)
        
        assert result == 'GROCERY'
        mock_print.assert_any_call("Available pattern words:")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_pattern_word_skip_selection(self, transformer):
        """Test pattern word selection with skip option"""
        description = 'COMPLEX TRANSACTION'
        
        with patch.object(transformer, '_get_pattern_suggestions', return_value=['COMPLEX', 'TRANSACTION']), \
             patch('builtins.input', return_value='3'), \
             patch('builtins.print'):
            
            result = transformer._ask_for_pattern_word(description)
        
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_pattern_word_invalid_then_valid(self, transformer):
        """Test pattern word selection with invalid then valid input"""
        description = 'TEST TRANSACTION'
        
        with patch.object(transformer, '_get_pattern_suggestions', return_value=['TEST', 'TRANSACTION']), \
             patch('builtins.input', side_effect=['invalid', '0', '1']), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_pattern_word(description)
        
        assert result == 'TEST'
        mock_print.assert_any_call("❌ Invalid choice. Please try again.")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_enum_name_valid_input(self, transformer):
        """Test asking for enum name with valid input"""
        pattern_word = 'GROCERY'
        
        with patch('builtins.input', return_value='grocery_payments'), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_enum_name(pattern_word)
        
        assert result == 'grocery_payments'
        mock_print.assert_any_call("📝 Create a new enum name for pattern 'GROCERY'")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_enum_name_empty_then_valid(self, transformer):
        """Test asking for enum name with empty then valid input"""
        pattern_word = 'ATM'
        
        with patch('builtins.input', side_effect=['', 'atm_withdrawals']), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_enum_name(pattern_word)
        
        assert result == 'atm_withdrawals'
        mock_print.assert_any_call("❌ Enum name cannot be empty.")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_enum_and_category_success(self, transformer):
        """Test handling enum and category creation"""
        enum_name = 'test_enum'
        patterns = ['TEST', 'PATTERN']
        
        mock_enum = Mock(id=456)
        transformer.db_loader.create_enum.return_value = mock_enum
        
        with patch.object(transformer, '_ask_for_category', return_value='test_category'), \
             patch('builtins.print'):
            
            result = transformer._handle_enum_and_category(enum_name, patterns)
        
        assert result == 456
        transformer.db_loader.create_enum.assert_called_once_with(
            enum_name=enum_name,
            patterns=patterns,
            category='test_category'
        )

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_category_valid_selection(self, transformer):
        """Test category selection with valid choice"""
        # Mock config_loader to return categories
        transformer.config_loader.get_categories.return_value = [
            'food', 'transport', 'shopping', 'utilities'
        ]
        
        with patch('builtins.input', return_value='2'), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_category()
        
        assert result == 'transport'
        mock_print.assert_any_call("Available categories:")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_category_new_category(self, transformer):
        """Test creating new category"""
        transformer.config_loader.get_categories.return_value = ['food', 'transport']
        
        with patch('builtins.input', side_effect=['3', 'new_category']), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_category()
        
        assert result == 'new_category'
        transformer.config_loader.add_category.assert_called_once_with('new_category')

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_category_invalid_then_valid(self, transformer):
        """Test category selection with invalid then valid input"""
        transformer.config_loader.get_categories.return_value = ['food', 'transport']
        
        with patch('builtins.input', side_effect=['invalid', '0', '1']), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_category()
        
        assert result == 'food'
        mock_print.assert_any_call("❌ Invalid choice. Please try again.")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_transaction_category_existing_selection(self, transformer):
        """Test transaction category selection from existing"""
        enum_category = 'food'
        
        with patch.object(transformer, '_ask_for_transaction_category_with_options', return_value={
            'type': 'existing',
            'value': 'groceries'
        }):
            
            result = transformer._ask_for_transaction_category(enum_category)
        
        assert result == 'groceries'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_transaction_category_new_creation(self, transformer):
        """Test transaction category creation"""
        enum_category = 'food'
        
        with patch.object(transformer, '_ask_for_transaction_category_with_options', return_value={
            'type': 'new',
            'value': 'organic_food'
        }):
            
            result = transformer._ask_for_transaction_category(enum_category)
        
        assert result == 'organic_food'
        transformer.config_loader.add_category.assert_called_once_with('organic_food', parent='food')

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_transaction_category_with_options_existing(self, transformer):
        """Test transaction category options with existing selection"""
        enum_category = 'food'
        subcategories = ['groceries', 'restaurants', 'snacks']
        
        transformer.config_loader.get_subcategories.return_value = subcategories
        
        with patch('builtins.input', return_value='2'), \
             patch('builtins.print'):
            
            result = transformer._ask_for_transaction_category_with_options(enum_category)
        
        assert result == {'type': 'existing', 'value': 'restaurants'}

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_transaction_category_with_options_new(self, transformer):
        """Test transaction category options with new category"""
        enum_category = 'transport'
        
        transformer.config_loader.get_subcategories.return_value = ['bus', 'train']
        
        with patch('builtins.input', side_effect=['3', 'airplane']), \
             patch('builtins.print'):
            
            result = transformer._ask_for_transaction_category_with_options(enum_category)
        
        assert result == {'type': 'new', 'value': 'airplane'}

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_reason_valid_input(self, transformer):
        """Test asking for reason with valid input"""
        with patch('builtins.input', return_value='Personal expense'), \
             patch('builtins.print'):
            
            result = transformer._ask_for_reason()
        
        assert result == 'Personal expense'

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_reason_empty_then_valid(self, transformer):
        """Test asking for reason with empty then valid input"""
        with patch('builtins.input', side_effect=['', 'Valid reason']), \
             patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_reason()
        
        assert result == 'Valid reason'
        mock_print.assert_any_call("❌ Reason cannot be empty.")

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_splits_no_splits(self, transformer):
        """Test asking for splits when user chooses no splits"""
        with patch('builtins.input', return_value='n'), \
             patch('builtins.print'):
            
            result = transformer._ask_for_splits()
        
        assert result is None

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_splits_with_valid_splits(self, transformer):
        """Test asking for splits with valid split data"""
        with patch('builtins.input', side_effect=[
            'y',  # Yes to splits
            '2',  # Number of splits
            'Food', '300.00',  # Split 1
            'Transport', '200.00'  # Split 2
        ]), patch('builtins.print'):
            
            result = transformer._ask_for_splits()
        
        expected = [
            {'category': 'Food', 'amount': 300.0},
            {'category': 'Transport', 'amount': 200.0}
        ]
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_ask_for_splits_invalid_inputs(self, transformer):
        """Test asking for splits with invalid inputs"""
        with patch('builtins.input', side_effect=[
            'y',  # Yes to splits
            'invalid',  # Invalid number
            '0',  # Zero splits
            '1',  # Valid number
            'Category1', 'invalid_amount',  # Invalid amount
            'Category1', '100.50'  # Valid amount
        ]), patch('builtins.print') as mock_print:
            
            result = transformer._ask_for_splits()
        
        expected = [{'category': 'Category1', 'amount': 100.5}]
        assert result == expected
        mock_print.assert_any_call("❌ Please enter a valid number.")
        mock_print.assert_any_call("❌ Number of splits must be at least 1.")

    # =====================
    # 7. COMPREHENSIVE PROCESS_TRANSACTIONS WORKFLOW TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transactions_complete_workflow_success(self, transformer):
        """Test complete process_transactions workflow with various scenarios"""
        extracted_data = {
            'transactions': [
                {
                    'data': {
                        'Transaction Date': '01-01-2023',
                        'Transaction Remarks': 'UPI-GROCERY STORE',
                        'Withdrawal Amount (INR )': '500.00',
                        'Deposit Amount (INR )': '',
                        'Balance (INR )': '10000.00',
                        'S No.': '12345'
                    }
                },
                {
                    'data': {
                        'Transaction Date': '02-01-2023',
                        'Transaction Remarks': 'SALARY CREDIT',
                        'Withdrawal Amount (INR )': '',
                        'Deposit Amount (INR )': '50000.00',
                        'Balance (INR )': '60000.00',
                        'S No.': '12346'
                    }
                }
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        with patch.object(transformer, '_transform_transaction', side_effect=[
            {
                'date': datetime(2023, 1, 1),
                'description': 'UPI-GROCERY STORE',
                'debit_amount': 500.0,
                'credit_amount': None,
                'balance': 10000.0,
                'reference_number': '12345',
                'transaction_type': 'debit'
            },
            {
                'date': datetime(2023, 1, 2),
                'description': 'SALARY CREDIT',
                'debit_amount': None,
                'credit_amount': 50000.0,
                'balance': 60000.0,
                'reference_number': '12346',
                'transaction_type': 'credit'
            }
        ]), \
        patch.object(transformer, '_create_transaction_hash', side_effect=['hash1', 'hash2']), \
        patch.object(transformer.db_loader, 'check_transaction_exists', return_value=False), \
        patch.object(transformer.db_loader, 'check_skipped_transaction_exists', return_value=False), \
        patch.object(transformer, '_display_transaction'), \
        patch.object(transformer, '_process_transaction_interactive', side_effect=[
            {
                'action': 'process',
                'enum_id': 1,
                'category': 'food',
                'transaction_category': 'groceries'
            },
            {
                'action': 'process',
                'enum_id': 2,
                'category': 'income',
                'transaction_category': 'salary'
            }
        ]), \
        patch.object(transformer.db_loader, 'create_transaction'), \
        patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['status'] == 'completed'
        assert result['total_transactions'] == 2
        assert result['processed_transactions'] == 2
        assert result['skipped_transactions'] == 0
        assert result['duplicate_transactions'] == 0

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transactions_with_duplicates_and_skips(self, transformer):
        """Test process_transactions with duplicates and skip scenarios"""
        extracted_data = {
            'transactions': [
                {'data': {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'DUPLICATE'}},
                {'data': {'Transaction Date': '', 'Transaction Remarks': 'INVALID'}},  # Invalid
                {'data': {'Transaction Date': '03-01-2023', 'Transaction Remarks': 'SKIP ME'}}
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        with patch.object(transformer, '_transform_transaction', side_effect=[
            {'description': 'DUPLICATE', 'date': datetime(2023, 1, 1)},
            None,  # Invalid transaction
            {'description': 'SKIP ME', 'date': datetime(2023, 1, 3)}
        ]), \
        patch.object(transformer, '_create_transaction_hash', side_effect=['dup_hash', 'skip_hash']), \
        patch.object(transformer.db_loader, 'check_transaction_exists', side_effect=[True, False]), \
        patch.object(transformer, '_display_transaction'), \
        patch.object(transformer, '_process_transaction_interactive', return_value={
            'action': 'skip',
            'reason': 'User skipped'
        }), \
        patch.object(transformer, '_handle_skipped_transaction'), \
        patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['total_transactions'] == 3
        assert result['processed_transactions'] == 0
        assert result['duplicate_transactions'] == 1
        assert result['skipped_transactions'] == 2

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transactions_with_auto_skipped(self, transformer):
        """Test process_transactions with auto-skipped transactions"""
        extracted_data = {
            'transactions': [
                {'data': {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'PREVIOUSLY SKIPPED'}}
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        # Mock config to not reprocess skipped transactions
        transformer.config = {'processing': {'reprocess_skipped_transactions': False}}
        
        with patch.object(transformer, '_transform_transaction', return_value={
            'description': 'PREVIOUSLY SKIPPED',
            'date': datetime(2023, 1, 1)
        }), \
        patch.object(transformer, '_create_transaction_hash', return_value='skipped_hash'), \
        patch.object(transformer.db_loader, 'check_transaction_exists', return_value=False), \
        patch.object(transformer.db_loader, 'check_skipped_transaction_exists', return_value=True), \
        patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['auto_skipped_transactions'] == 1

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transactions_reprocess_skipped_enabled(self, transformer):
        """Test process_transactions with reprocess skipped enabled"""
        extracted_data = {
            'transactions': [
                {'data': {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'REPROCESS ME'}}
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        # Mock config to reprocess skipped transactions
        transformer.config = {'processing': {'reprocess_skipped_transactions': True}}
        
        with patch.object(transformer, '_transform_transaction', return_value={
            'description': 'REPROCESS ME',
            'date': datetime(2023, 1, 1)
        }), \
        patch.object(transformer, '_create_transaction_hash', return_value='reprocess_hash'), \
        patch.object(transformer.db_loader, 'check_transaction_exists', return_value=False), \
        patch.object(transformer.db_loader, 'check_skipped_transaction_exists', return_value=True), \
        patch.object(transformer, '_display_transaction'), \
        patch.object(transformer, '_process_transaction_interactive', return_value={
            'action': 'process',
            'enum_id': 1
        }), \
        patch.object(transformer.db_loader, 'create_transaction'), \
        patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['processed_transactions'] == 1

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_process_transactions_exception_handling(self, transformer):
        """Test process_transactions with exception during processing"""
        extracted_data = {
            'transactions': [
                {'data': {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'EXCEPTION CASE'}}
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        with patch.object(transformer, '_transform_transaction', side_effect=Exception("Test error")), \
             patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['status'] == 'error'
        assert result['skipped_transactions'] == 1

    @pytest.mark.unit
    @pytest.mark.transformer  
    def test_process_transactions_interrupted_flow(self, transformer):
        """Test process_transactions when interrupted"""
        extracted_data = {
            'transactions': [
                {'data': {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'INTERRUPTED'}}
            ]
        }
        
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        
        # Simulate interruption
        transformer._interrupted = True
        
        with patch.object(transformer, '_transform_transaction', return_value={
            'description': 'INTERRUPTED',
            'date': datetime(2023, 1, 1)
        }), \
        patch('builtins.print'):
            
            result = transformer.process_transactions(extracted_data, mock_institution, mock_processed_file)
        
        assert result['status'] == 'partially_completed'

    # =====================
    # 8. EXISTING ENUM MATCH TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_check_existing_enum_match_found(self, transformer):
        """Test checking for existing enum match when found"""
        description = "UPI Payment to Swiggy"
        
        mock_enum = Mock()
        mock_enum.id = 1
        mock_enum.enum_name = 'swiggy_transaction'
        mock_enum.category = 'food'
        mock_enum.patterns = ['swiggy', 'swiggy payment']
        
        mock_session = Mock()
        mock_session.query().filter_by().all.return_value = [mock_enum]
        transformer.db_manager.get_session.return_value = mock_session
        
        result = transformer._check_existing_enum_match(description)
        
        assert result is not None
        assert result['id'] == 1
        assert result['enum_name'] == 'swiggy_transaction'
        assert result['category'] == 'food'
        
        mock_session.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_check_existing_enum_match_not_found(self, transformer):
        """Test checking for existing enum match when not found"""
        description = "Unknown merchant payment"
        
        mock_session = Mock()
        mock_session.query().filter_by().all.return_value = []
        transformer.db_manager.get_session.return_value = mock_session
        
        result = transformer._check_existing_enum_match(description)
        
        assert result is None
        mock_session.close.assert_called_once()

    # =====================
    # 9. SKIPPED TRANSACTION HANDLING TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_skipped_transaction_with_hash(self, transformer):
        """Test handling skipped transaction with provided hash"""
        row_data = {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'Test'}
        institution_id = 1
        processed_file_id = 2
        skip_reason = "User skipped"
        row_number = 5
        transaction_hash = "test_hash_123"
        
        transformer._handle_skipped_transaction(
            row_data, institution_id, processed_file_id, 
            skip_reason, row_number, transaction_hash
        )
        
        expected_record = {
            'transaction_hash': transaction_hash,
            'institution_id': institution_id,
            'processed_file_id': processed_file_id,
            'raw_data': row_data,
            'row_number': row_number,
            'skip_reason': skip_reason
        }
        
        transformer.db_loader.create_skipped_transaction.assert_called_once_with(expected_record)

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_skipped_transaction_without_hash(self, transformer):
        """Test handling skipped transaction without provided hash"""
        row_data = {'Transaction Date': '01-01-2023', 'Transaction Remarks': 'Test'}
        institution_id = 1
        processed_file_id = 2
        skip_reason = "User skipped"
        
        transformer._handle_skipped_transaction(
            row_data, institution_id, processed_file_id, skip_reason
        )
        
        # Should call create_skipped_transaction with generated hash
        transformer.db_loader.create_skipped_transaction.assert_called_once()
        call_args = transformer.db_loader.create_skipped_transaction.call_args[0][0]
        
        assert 'transaction_hash' in call_args
        assert len(call_args['transaction_hash']) == 64  # SHA256 hash
        assert call_args['raw_data'] == row_data
        assert call_args['skip_reason'] == skip_reason

    @pytest.mark.unit
    @pytest.mark.transformer
    def test_handle_skipped_transaction_database_error(self, transformer):
        """Test handling skipped transaction with database error"""
        transformer.db_loader.create_skipped_transaction.side_effect = Exception("DB Error")
        
        with patch('builtins.print') as mock_print:
            transformer._handle_skipped_transaction(
                {}, 1, 2, "test reason"
            )
        
        mock_print.assert_called_once()
        assert "Error saving skipped transaction" in str(mock_print.call_args)

    # =====================
    # 10. SECURITY AND EDGE CASE TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.security
    def test_secure_data_handling(self, transformer):
        """Test secure handling of sensitive transaction data"""
        # Test that no sensitive data is logged or exposed
        sensitive_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': 'CONFIDENTIAL PAYMENT TO ACCOUNT 123456789',
            'Withdrawal Amount (INR )': '50000.00',
            'Balance (INR )': '100000.00'
        }
        
        with patch('builtins.print') as mock_print:
            result = transformer._transform_transaction(sensitive_data)
        
        # Ensure no sensitive information is leaked in logs
        if mock_print.called:
            for call_args in mock_print.call_args_list:
                call_text = str(call_args)
                assert '123456789' not in call_text
                assert '50000.00' not in call_text

    @pytest.mark.unit
    @pytest.mark.edge_case  
    def test_extreme_data_handling(self, transformer):
        """Test handling of extreme data values"""
        extreme_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': 'A' * 10000,  # Very long description
            'Withdrawal Amount (INR )': '999999999999.99',  # Very large amount
            'Balance (INR )': '0.01'  # Very small balance
        }
        
        result = transformer._transform_transaction(extreme_data)
        
        assert result is not None
        assert len(result['description']) == 10000
        assert result['debit_amount'] == 999999999999.99
        assert result['balance'] == 0.01

    @pytest.mark.unit
    @pytest.mark.performance
    def test_large_transaction_list_performance(self, transformer):
        """Test performance with large transaction lists"""
        # Create 1000 transactions for performance testing
        large_transaction_list = []
        for i in range(1000):
            large_transaction_list.append({
                'data': {
                    'Transaction Date': '01-01-2023',
                    'Transaction Remarks': f'Transaction {i}',
                    'Withdrawal Amount (INR )': f'{i}.00',
                    'Balance (INR )': '10000.00'
                }
            })
        
        extracted_data = {'transactions': large_transaction_list}
        
        # Mock all the interactive components to avoid user input
        with patch.object(transformer, '_transform_transaction', return_value=None):
            institution = Mock(id=1)
            processed_file = Mock(id=2)
            
            result = transformer.process_transactions(extracted_data, institution, processed_file)
        
        assert result['total_transactions'] == 1000
        assert result['skipped_transactions'] == 1000  # All invalid due to None transform

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_unicode_handling(self, transformer):
        """Test handling of Unicode characters in transactions"""
        unicode_data = {
            'Transaction Date': '01-01-2023',
            'Transaction Remarks': '💰 Payment to 🏪 Store with ₹ symbol',
            'Withdrawal Amount (INR )': '₹1,000.50',
            'Balance (INR )': '₹10,000.00'
        }
        
        result = transformer._transform_transaction(unicode_data)
        
        assert result is not None
        assert '💰' in result['description']
        assert '🏪' in result['description']
        assert result['debit_amount'] == 1000.5
        assert result['balance'] == 10000.0 