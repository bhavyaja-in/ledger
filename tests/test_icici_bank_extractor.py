"""
Comprehensive unit tests for icici_bank_extractor.py with 100% line coverage.

Tests all IciciBankExtractor methods including transaction extraction, filtering,
validation, error scenarios, and ICICI Bank specific business logic to ensure enterprise-grade quality.
"""

import os
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.extractors.channel_based_extractors.icici_bank_extractor import (
    IciciBankExtractor,
)


class TestIciciBankExtractor:
    """Comprehensive test suite for IciciBankExtractor class"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            "icici_bank": {"date_format": "%d/%m/%Y", "currency": "INR"},
            "file_settings": {"max_rows": 10000},
        }

    @pytest.fixture
    def extractor(self, mock_config):
        """Create IciciBankExtractor instance with mocked configuration"""
        return IciciBankExtractor(mock_config)

    @pytest.fixture
    def sample_transaction_data(self):
        """Create sample transaction data for testing"""
        return [
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "UPI-Payment to Merchant",
                "Withdrawal Amount (INR )": "500.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            {
                "Transaction Date": "02/01/2023",
                "Transaction Remarks": "Salary Credit",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "50000.00",
                "Balance (INR )": "60000.00",
            },
            {
                "Transaction Date": "03/01/2023",
                "Transaction Remarks": "ATM Withdrawal",
                "Withdrawal Amount (INR )": "2000.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "58000.00",
            },
        ]

    @pytest.fixture
    def sample_file_info(self):
        """Create sample file information"""
        return {
            "file_path": "/test/path/icici_statement.xlsx",
            "file_name": "icici_statement.xlsx",
            "file_size": 2048,
        }

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_init(self, mock_config):
        """Test IciciBankExtractor initialization"""
        extractor = IciciBankExtractor(mock_config)

        assert extractor.config == mock_config
        assert extractor.excel_extractor is not None
        assert extractor.required_columns == [
            "transaction date",
            "transaction remarks",
            "withdrawal amount (inr )",
            "deposit amount (inr )",
            "balance (inr )",
            "s no.",
        ]

    @pytest.mark.unit
    @pytest.mark.extractor
    @patch("src.extractors.channel_based_extractors.icici_bank_extractor.ExcelExtractor")
    def test_init_creates_excel_extractor(self, mock_excel_extractor, mock_config):
        """Test that initialization creates ExcelExtractor with correct config"""
        extractor = IciciBankExtractor(mock_config)

        mock_excel_extractor.assert_called_once_with(mock_config)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_success(self, extractor, sample_transaction_data, sample_file_info):
        """Test successful extraction of ICICI Bank data"""
        file_path = "/test/path/icici_statement.xlsx"

        # Mock the excel_extractor methods
        mock_df = pd.DataFrame(sample_transaction_data)
        extractor.excel_extractor.read_excel_file = Mock(return_value=mock_df)
        extractor.excel_extractor.detect_header_row = Mock(return_value=0)
        extractor.excel_extractor.extract_data_from_row = Mock(return_value=sample_transaction_data)
        extractor.excel_extractor.get_file_info = Mock(return_value=sample_file_info)

        result = extractor.extract(file_path)

        # Verify calls were made
        extractor.excel_extractor.read_excel_file.assert_called_once_with(file_path)
        extractor.excel_extractor.detect_header_row.assert_called_once_with(
            mock_df, extractor.required_columns
        )
        extractor.excel_extractor.extract_data_from_row.assert_called_once_with(mock_df, 0)
        extractor.excel_extractor.get_file_info.assert_called_once_with(file_path)

        # Verify result structure
        assert "file_info" in result
        assert "header_row" in result
        assert "total_rows" in result
        assert "valid_transactions" in result
        assert "transactions" in result

        assert result["file_info"] == sample_file_info
        assert result["header_row"] == 0
        assert result["total_rows"] == 3
        assert result["valid_transactions"] == 3
        assert len(result["transactions"]) == 3

        # Verify transaction format
        for transaction in result["transactions"]:
            assert "data" in transaction

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_header_not_found(self, extractor):
        """Test extraction when header row is not found - now defaults to row 0"""
        file_path = "/test/path/icici_statement.xlsx"

        mock_df = pd.DataFrame([["Random", "Data", "Here"]])
        extractor.excel_extractor.read_excel_file = Mock(return_value=mock_df)
        extractor.excel_extractor.detect_header_row = Mock(return_value=None)
        extractor.excel_extractor.extract_data_from_row = Mock(return_value=[])
        extractor.excel_extractor.get_file_info = Mock(return_value={"file_path": file_path})

        result = extractor.extract(file_path)

        # Should default to header_row = 0 when detection fails
        assert result["header_row"] == 0

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_excel_read_error(self, extractor):
        """Test extraction when Excel reading fails"""
        file_path = "/test/path/nonexistent.xlsx"

        extractor.excel_extractor.read_excel_file = Mock(side_effect=Exception("File read error"))

        with pytest.raises(Exception, match="Error extracting ICICI Bank data: File read error"):
            extractor.extract(file_path)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_with_print_output(
        self, extractor, sample_transaction_data, sample_file_info, capsys
    ):
        """Test that extract method works without print output"""
        file_path = "/test/path/icici_statement.xlsx"

        mock_df = pd.DataFrame(sample_transaction_data)
        extractor.excel_extractor.read_excel_file = Mock(return_value=mock_df)
        extractor.excel_extractor.detect_header_row = Mock(return_value=2)
        extractor.excel_extractor.extract_data_from_row = Mock(return_value=[])
        extractor.excel_extractor.get_file_info = Mock(return_value=sample_file_info)

        result = extractor.extract(file_path)

        # Verify the method works without requiring print output
        assert result["header_row"] == 2
        assert "file_info" in result

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_filter_valid_transactions_all_valid(self, extractor, sample_transaction_data):
        """Test filtering with all valid transactions"""
        result = extractor._filter_valid_transactions(sample_transaction_data)

        assert len(result) == 3
        assert result == sample_transaction_data

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_filter_valid_transactions_mixed_validity(self, extractor):
        """Test filtering with mixed valid and invalid transactions"""
        mixed_data = [
            # Valid transaction
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "UPI Payment",
                "Withdrawal Amount (INR )": "500.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            # Invalid - no essential fields
            {
                "Transaction Date": "",
                "Transaction Remarks": "Invalid Transaction",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            # Invalid - header-like row
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "Transaction Remarks",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            # Invalid - empty remarks
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "",
                "Withdrawal Amount (INR )": "100.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            # Valid transaction
            {
                "Transaction Date": "02/01/2023",
                "Transaction Remarks": "Salary Credit",
                "Withdrawal Amount (INR )": "",
                "Deposit Amount (INR )": "50000.00",
                "Balance (INR )": "60000.00",
            },
        ]

        result = extractor._filter_valid_transactions(mixed_data)

        assert len(result) == 2  # Only 2 valid transactions
        assert result[0]["Transaction Remarks"] == "UPI Payment"
        assert result[1]["Transaction Remarks"] == "Salary Credit"

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_filter_valid_transactions_empty_list(self, extractor):
        """Test filtering with empty transaction list"""
        result = extractor._filter_valid_transactions([])

        assert result == []

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_filter_valid_transactions_nan_remarks(self, extractor):
        """Test filtering transactions with NaN or None remarks"""
        data_with_nan_remarks = [
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "nan",
                "Withdrawal Amount (INR )": "500.00",
                "Deposit Amount (INR )": "",
            },
            {
                "Transaction Date": "02/01/2023",
                "Transaction Remarks": "none",
                "Withdrawal Amount (INR )": "300.00",
                "Deposit Amount (INR )": "",
            },
            {
                "Transaction Date": "03/01/2023",
                "Transaction Remarks": np.nan,
                "Withdrawal Amount (INR )": "200.00",
                "Deposit Amount (INR )": "",
            },
        ]

        result = extractor._filter_valid_transactions(data_with_nan_remarks)

        assert len(result) == 0  # All should be filtered out

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_valid_debit(self, extractor):
        """Test has_essential_fields with valid debit transaction"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "500.00",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_valid_credit(self, extractor):
        """Test has_essential_fields with valid credit transaction"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "",
            "Deposit Amount (INR )": "1000.00",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_both_amounts(self, extractor):
        """Test has_essential_fields with both debit and credit amounts"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "200.00",
            "Deposit Amount (INR )": "300.00",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_missing_date(self, extractor):
        """Test has_essential_fields with missing transaction date"""
        row_data = {
            "Transaction Date": "",
            "Withdrawal Amount (INR )": "500.00",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_nan_date(self, extractor):
        """Test has_essential_fields with NaN transaction date"""
        row_data = {
            "Transaction Date": "nan",
            "Withdrawal Amount (INR )": "500.00",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_none_date(self, extractor):
        """Test has_essential_fields with None transaction date"""
        row_data = {
            "Transaction Date": None,
            "Withdrawal Amount (INR )": "500.00",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_missing_amounts(self, extractor):
        """Test has_essential_fields with missing both amounts"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_nan_amounts(self, extractor):
        """Test has_essential_fields with NaN amounts"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "nan",
            "Deposit Amount (INR )": "None",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_invalid_amount_format(self, extractor):
        """Test has_essential_fields with invalid amount format"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "invalid_amount",
            "Deposit Amount (INR )": "also_invalid",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_zero_amounts(self, extractor):
        """Test has_essential_fields with zero amounts (should be valid)"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "0.00",
            "Deposit Amount (INR )": "",
        }

        result = extractor._has_essential_fields(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_numeric_amounts(self, extractor):
        """Test has_essential_fields with numeric (not string) amounts"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": 500.0,
            "Deposit Amount (INR )": None,
        }

        result = extractor._has_essential_fields(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_has_essential_fields_none_amounts(self, extractor):
        """Test has_essential_fields with None amounts"""
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": None,
            "Deposit Amount (INR )": None,
        }

        result = extractor._has_essential_fields(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_transaction_remarks(self, extractor):
        """Test is_header_like_row with transaction remarks header"""
        row_data = {
            "Transaction Remarks": "Transaction Remarks",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_transaction_date(self, extractor):
        """Test is_header_like_row with transaction date header"""
        row_data = {
            "Transaction Remarks": "Transaction Date Column",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_withdrawal_amount(self, extractor):
        """Test is_header_like_row with withdrawal amount header"""
        row_data = {
            "Transaction Remarks": "Withdrawal Amount (INR)",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_deposit_amount(self, extractor):
        """Test is_header_like_row with deposit amount header"""
        row_data = {
            "Transaction Remarks": "Contains Deposit Amount info",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_balance(self, extractor):
        """Test is_header_like_row with balance header"""
        row_data = {
            "Transaction Remarks": "Balance Information",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_cheque_number(self, extractor):
        """Test is_header_like_row with cheque number header"""
        row_data = {
            "Transaction Remarks": "Cheque Number: 123456",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_case_insensitive(self, extractor):
        """Test is_header_like_row is case insensitive"""
        row_data = {
            "Transaction Remarks": "TRANSACTION REMARKS HEADER",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_normal_transaction(self, extractor):
        """Test is_header_like_row with normal transaction"""
        row_data = {
            "Transaction Remarks": "UPI Payment to Merchant XYZ",
            "Transaction Date": "01/01/2023",
        }

        result = extractor._is_header_like_row(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_missing_remarks(self, extractor):
        """Test is_header_like_row with missing transaction remarks"""
        row_data = {"Transaction Date": "01/01/2023"}

        result = extractor._is_header_like_row(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_header_like_row_none_remarks(self, extractor):
        """Test is_header_like_row with None transaction remarks"""
        row_data = {"Transaction Remarks": None, "Transaction Date": "01/01/2023"}

        result = extractor._is_header_like_row(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.security
    def test_no_production_data_modification(self, security_validator):
        """Security test: Ensure no production data is modified"""
        security_validator.ensure_no_production_changes()

        # Verify test mode is active
        assert os.environ.get("LEDGER_TEST_MODE") == "true"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_extract_large_dataset(self, extractor):
        """Test extraction with large dataset"""
        file_path = "/test/path/large_icici_statement.xlsx"

        # Create large dataset
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "Transaction Date": f"{(i % 28) + 1:02d}/01/2023",
                    "Transaction Remarks": f"Transaction {i}",
                    "Withdrawal Amount (INR )": (f"{(i * 10) % 5000}.00" if i % 2 == 0 else ""),
                    "Deposit Amount (INR )": (f"{(i * 15) % 3000}.00" if i % 2 == 1 else ""),
                    "Balance (INR )": f"{10000 + i * 100}.00",
                }
            )

        sample_file_info = {
            "file_path": file_path,
            "file_name": "large_icici_statement.xlsx",
            "file_size": 1024000,
        }

        mock_df = pd.DataFrame(large_data)
        extractor.excel_extractor.read_excel_file = Mock(return_value=mock_df)
        extractor.excel_extractor.detect_header_row = Mock(return_value=0)
        extractor.excel_extractor.extract_data_from_row = Mock(return_value=large_data)
        extractor.excel_extractor.get_file_info = Mock(return_value=sample_file_info)

        result = extractor.extract(file_path)

        assert result["total_rows"] == 1000
        assert result["valid_transactions"] == 1000
        assert len(result["transactions"]) == 1000

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_extract_unicode_transactions(self, extractor):
        """Test extraction with Unicode characters in transaction data"""
        unicode_data = [
            {
                "Transaction Date": "01/01/2023",
                "Transaction Remarks": "Payment to café Mumbai ₹500",
                "Withdrawal Amount (INR )": "500.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "10000.00",
            },
            {
                "Transaction Date": "02/01/2023",
                "Transaction Remarks": "UPI-डॉक्टर को भुगतान",
                "Withdrawal Amount (INR )": "300.00",
                "Deposit Amount (INR )": "",
                "Balance (INR )": "9700.00",
            },
        ]

        file_path = "/test/path/unicode_icici_statement.xlsx"
        sample_file_info = {
            "file_path": file_path,
            "file_name": "unicode_icici_statement.xlsx",
            "file_size": 2048,
        }

        mock_df = pd.DataFrame(unicode_data)
        extractor.excel_extractor.read_excel_file = Mock(return_value=mock_df)
        extractor.excel_extractor.detect_header_row = Mock(return_value=0)
        extractor.excel_extractor.extract_data_from_row = Mock(return_value=unicode_data)
        extractor.excel_extractor.get_file_info = Mock(return_value=sample_file_info)

        result = extractor.extract(file_path)

        assert result["valid_transactions"] == 2
        assert "café Mumbai ₹500" in result["transactions"][0]["data"]["Transaction Remarks"]
        assert "डॉक्टर को भुगतान" in result["transactions"][1]["data"]["Transaction Remarks"]

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_has_essential_fields_edge_cases(self, extractor):
        """Test has_essential_fields with various edge case amounts"""
        # Negative amounts (should be valid)
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "-500.00",
            "Deposit Amount (INR )": "",
        }
        assert extractor._has_essential_fields(row_data) is True

        # Very large amounts
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "999999999.99",
            "Deposit Amount (INR )": "",
        }
        assert extractor._has_essential_fields(row_data) is True

        # Scientific notation
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "1.5e3",
            "Deposit Amount (INR )": "",
        }
        assert extractor._has_essential_fields(row_data) is True

        # Decimal with many places
        row_data = {
            "Transaction Date": "01/01/2023",
            "Withdrawal Amount (INR )": "100.123456789",
            "Deposit Amount (INR )": "",
        }
        assert extractor._has_essential_fields(row_data) is True

    @pytest.mark.unit
    @pytest.mark.performance
    def test_filter_performance_large_dataset(self, extractor):
        """Test filtering performance with large dataset"""
        # Create dataset with mix of valid and invalid transactions
        large_mixed_data = []
        for i in range(5000):
            if i % 5 == 0:  # Every 5th transaction is invalid (no amount)
                large_mixed_data.append(
                    {
                        "Transaction Date": f"{(i % 28) + 1:02d}/01/2023",
                        "Transaction Remarks": f"Transaction {i}",
                        "Withdrawal Amount (INR )": "",
                        "Deposit Amount (INR )": "",
                        "Balance (INR )": f"{10000 + i}.00",
                    }
                )
            else:
                large_mixed_data.append(
                    {
                        "Transaction Date": f"{(i % 28) + 1:02d}/01/2023",
                        "Transaction Remarks": f"Valid Transaction {i}",
                        "Withdrawal Amount (INR )": (f"{i % 1000}.00" if i % 2 == 0 else ""),
                        "Deposit Amount (INR )": f"{i % 800}.00" if i % 2 == 1 else "",
                        "Balance (INR )": f"{10000 + i}.00",
                    }
                )

        result = extractor._filter_valid_transactions(large_mixed_data)

        # Should filter out every 5th transaction (1000 invalid out of 5000)
        assert len(result) == 4000

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_extract_error_propagation(self, extractor):
        """Test that extract method properly propagates different types of errors"""
        file_path = "/test/path/error_file.xlsx"

        # Test ValueError propagation
        extractor.excel_extractor.read_excel_file = Mock(
            side_effect=ValueError("Invalid file format")
        )

        with pytest.raises(
            Exception, match="Error extracting ICICI Bank data: Invalid file format"
        ):
            extractor.extract(file_path)

        # Test custom exception propagation
        extractor.excel_extractor.read_excel_file = Mock(
            side_effect=Exception("Custom error message")
        )

        with pytest.raises(
            Exception, match="Error extracting ICICI Bank data: Custom error message"
        ):
            extractor.extract(file_path)

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_required_columns_completeness(self, extractor):
        """Test that all required columns are properly defined"""
        expected_columns = [
            "transaction date",
            "transaction remarks",
            "withdrawal amount (inr )",
            "deposit amount (inr )",
            "balance (inr )",
            "s no.",
        ]

        assert extractor.required_columns == expected_columns
        assert len(extractor.required_columns) == 6

        # Verify all columns are lowercase for case-insensitive matching
        assert all(col.islower() for col in extractor.required_columns)
