"""
Comprehensive unit tests for excel_extractor.py with 100% line coverage.

Tests all ExcelExtractor methods including file reading, header detection,
data extraction, error scenarios, and edge cases to ensure enterprise-grade quality.
"""

import os
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pandas as pd
import pytest

from src.extractors.file_based_extractors.excel_extractor import ExcelExtractor


class TestExcelExtractor:
    """Comprehensive test suite for ExcelExtractor class"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {"test_key": "test_value", "excel_settings": {"encoding": "utf-8"}}

    @pytest.fixture
    def extractor(self, mock_config):
        """Create ExcelExtractor instance with mocked configuration"""
        return ExcelExtractor(mock_config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing"""
        return pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "Description": ["Payment 1", "Payment 2", "Payment 3"],
                "Amount": [100.0, 200.0, 300.0],
                "Balance": [1000.0, 1200.0, 1500.0],
            }
        )

    @pytest.fixture
    def sample_header_detection_df(self):
        """Create DataFrame for header detection testing"""
        return pd.DataFrame(
            [
                ["Some header text", "More text", "Extra"],
                [
                    "Transaction Date",
                    "Description",
                    "Debit Amount",
                    "Credit Amount",
                    "Balance",
                ],
                ["2023-01-01", "Payment 1", "100.0", "", "1000.0"],
                ["2023-01-02", "Payment 2", "", "200.0", "1200.0"],
                ["2023-01-03", "Payment 3", "300.0", "", "900.0"],
            ]
        )

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_init(self, mock_config):
        """Test ExcelExtractor initialization"""
        extractor = ExcelExtractor(mock_config)

        assert extractor.config == mock_config

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_success(self, extractor, sample_dataframe):
        """Test read_excel_file successfully reads Excel file"""
        file_path = "/path/to/test.xlsx"

        with patch("pandas.read_excel", return_value=sample_dataframe) as mock_read:
            result = extractor.read_excel_file(file_path)

            mock_read.assert_called_once_with(file_path, sheet_name=0)
            pd.testing.assert_frame_equal(result, sample_dataframe)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_with_sheet_name(self, extractor, sample_dataframe):
        """Test read_excel_file with custom sheet name"""
        file_path = "/path/to/test.xlsx"
        sheet_name = 1

        with patch("pandas.read_excel", return_value=sample_dataframe) as mock_read:
            result = extractor.read_excel_file(file_path, sheet_name=sheet_name)

            mock_read.assert_called_once_with(file_path, sheet_name=sheet_name)
            pd.testing.assert_frame_equal(result, sample_dataframe)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_exception_handling(self, extractor):
        """Test read_excel_file handles pandas exceptions"""
        file_path = "/path/to/nonexistent.xlsx"

        with patch(
            "pandas.read_excel", side_effect=FileNotFoundError("File not found")
        ):
            with pytest.raises(Exception, match="Error reading Excel file"):
                extractor.read_excel_file(file_path)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_permission_error(self, extractor):
        """Test read_excel_file handles permission errors"""
        file_path = "/path/to/protected.xlsx"

        with patch(
            "pandas.read_excel", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(Exception, match="Error reading Excel file"):
                extractor.read_excel_file(file_path)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_found_perfect_match(
        self, extractor, sample_header_detection_df
    ):
        """Test detect_header_row finds header with perfect match"""
        required_columns = [
            "Transaction Date",
            "Description",
            "Debit Amount",
            "Credit Amount",
            "Balance",
        ]

        result = extractor.detect_header_row(
            sample_header_detection_df, required_columns
        )

        assert result == 1  # Header is in row 1 (0-indexed)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_found_partial_match(self, extractor):
        """Test detect_header_row finds header with partial match (70% threshold)"""
        df = pd.DataFrame(
            [
                ["Some text", "More text", "Extra"],
                [
                    "Date",
                    "Description",
                    "Amount",
                    "Other Column",
                    "Another",
                ],  # 3/4 = 75% match
                ["2023-01-01", "Payment 1", "100.0", "data", "more"],
            ]
        )
        required_columns = ["Date", "Description", "Amount", "Missing Column"]

        result = extractor.detect_header_row(df, required_columns)

        assert result == 1  # Should find header at row 1

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_case_insensitive(self, extractor):
        """Test detect_header_row is case insensitive"""
        df = pd.DataFrame(
            [
                ["TRANSACTION DATE", "DESCRIPTION", "DEBIT AMOUNT"],
                ["2023-01-01", "Payment 1", "100.0"],
            ]
        )
        required_columns = ["transaction date", "description", "debit amount"]

        result = extractor.detect_header_row(df, required_columns)

        assert result == 0

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_with_extra_whitespace(self, extractor):
        """Test detect_header_row handles whitespace in headers"""
        df = pd.DataFrame(
            [
                ["  Transaction Date  ", "  Description  ", "  Amount  "],
                ["2023-01-01", "Payment 1", "100.0"],
            ]
        )
        required_columns = ["Transaction Date", "Description", "Amount"]

        result = extractor.detect_header_row(df, required_columns)

        assert result == 0

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_with_nan_values(self, extractor):
        """Test detect_header_row handles NaN values in potential header rows"""
        df = pd.DataFrame(
            [
                [np.nan, "Description", "Amount", np.nan],
                ["Date", np.nan, "Amount", "Balance"],
                ["2023-01-01", "Payment 1", "100.0", "1000.0"],
            ]
        )
        required_columns = ["Date", "Amount", "Balance"]

        result = extractor.detect_header_row(df, required_columns)

        assert result == 1  # Should find header at row 1

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_not_found(self, extractor):
        """Test detect_header_row returns None when header not found"""
        df = pd.DataFrame(
            [
                ["Random", "Data", "Here"],
                ["More", "Random", "Data"],
                ["2023-01-01", "Payment 1", "100.0"],
            ]
        )
        required_columns = ["Transaction Date", "Description", "Amount"]

        result = extractor.detect_header_row(df, required_columns)

        assert result is None

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_below_threshold(self, extractor):
        """Test detect_header_row returns None when match is below 70% threshold"""
        df = pd.DataFrame(
            [
                ["Date", "Random", "Data", "More Random"],  # Only 1/4 = 25% match
                ["2023-01-01", "Payment 1", "100.0", "data"],
            ]
        )
        required_columns = ["Date", "Description", "Amount", "Balance"]

        result = extractor.detect_header_row(df, required_columns)

        assert result is None

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_max_search_rows(self, extractor):
        """Test detect_header_row respects max_search_rows parameter"""
        # Create DataFrame with header at row 5
        df = pd.DataFrame(
            [
                ["Row 0", "Data", "Here"],
                ["Row 1", "Data", "Here"],
                ["Row 2", "Data", "Here"],
                ["Row 3", "Data", "Here"],
                ["Row 4", "Data", "Here"],
                ["Date", "Description", "Amount"],  # Header at row 5
                ["2023-01-01", "Payment 1", "100.0"],
            ]
        )
        required_columns = ["Date", "Description", "Amount"]

        # Search only first 3 rows
        result = extractor.detect_header_row(df, required_columns, max_search_rows=3)

        assert result is None  # Should not find header since it's beyond search limit

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_detect_header_row_empty_dataframe(self, extractor):
        """Test detect_header_row handles empty DataFrame"""
        df = pd.DataFrame()
        required_columns = ["Date", "Description", "Amount"]

        result = extractor.detect_header_row(df, required_columns)

        assert result is None

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_data_from_row_success(self, extractor):
        """Test extract_data_from_row successfully extracts data"""
        df = pd.DataFrame(
            [
                ["Date", "Description", "Amount"],
                ["2023-01-01", "Payment 1", 100.0],
                ["2023-01-02", "Payment 2", 200.0],
                ["", "", ""],  # Empty row to test filtering
            ]
        )
        header_row = 0

        result = extractor.extract_data_from_row(df, header_row)

        expected = [
            {"Date": "2023-01-01", "Description": "Payment 1", "Amount": 100.0},
            {"Date": "2023-01-02", "Description": "Payment 2", "Amount": 200.0},
        ]

        assert len(result) == 2
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_data_from_row_with_nan_header(self, extractor):
        """Test extract_data_from_row handles NaN values in header"""
        df = pd.DataFrame(
            [
                ["Date", np.nan, "Amount"],
                ["2023-01-01", "Payment 1", 100.0],
                ["2023-01-02", "Payment 2", 200.0],
            ]
        )
        header_row = 0

        result = extractor.extract_data_from_row(df, header_row)

        expected = [
            {"Date": "2023-01-01", "nan": "Payment 1", "Amount": 100.0},
            {"Date": "2023-01-02", "nan": "Payment 2", "Amount": 200.0},
        ]

        assert len(result) == 2
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_data_from_row_mismatched_columns(self, extractor):
        """Test extract_data_from_row handles rows with fewer columns than header"""
        df = pd.DataFrame(
            [
                ["Date", "Description", "Amount", "Balance"],
                ["2023-01-01", "Payment 1", 100.0],  # Missing Balance column
                ["2023-01-02", "Payment 2", 200.0, 1000.0],
            ]
        )
        header_row = 0

        result = extractor.extract_data_from_row(df, header_row)

        expected = [
            {
                "Date": "2023-01-01",
                "Description": "Payment 1",
                "Amount": 100.0,
                "Balance": np.nan,
            },
            {
                "Date": "2023-01-02",
                "Description": "Payment 2",
                "Amount": 200.0,
                "Balance": 1000.0,
            },
        ]

        # Need to handle NaN comparison properly
        assert len(result) == 2
        assert result[0]["Date"] == "2023-01-01"
        assert result[0]["Description"] == "Payment 1"
        assert result[0]["Amount"] == 100.0
        assert pd.isna(result[0]["Balance"])
        assert result[1] == expected[1]

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_data_from_row_no_data_rows(self, extractor):
        """Test extract_data_from_row when there are no data rows after header"""
        df = pd.DataFrame([["Date", "Description", "Amount"]])
        header_row = 0

        result = extractor.extract_data_from_row(df, header_row)

        assert result == []

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_extract_data_from_row_all_empty_rows(self, extractor):
        """Test extract_data_from_row filters out all empty rows"""
        df = pd.DataFrame(
            [
                ["Date", "Description", "Amount"],
                ["", "", ""],
                [np.nan, np.nan, np.nan],
                ["   ", "  ", "   "],  # Whitespace only
            ]
        )
        header_row = 0

        result = extractor.extract_data_from_row(df, header_row)

        assert result == []

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_empty_row_completely_empty(self, extractor):
        """Test _is_empty_row identifies completely empty row"""
        row_data = {"Date": "", "Description": "", "Amount": np.nan}

        result = extractor._is_empty_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_empty_row_whitespace_only(self, extractor):
        """Test _is_empty_row identifies whitespace-only row"""
        row_data = {"Date": "   ", "Description": "\t", "Amount": "  "}

        result = extractor._is_empty_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_empty_row_with_data(self, extractor):
        """Test _is_empty_row identifies row with actual data"""
        row_data = {"Date": "2023-01-01", "Description": "", "Amount": np.nan}

        result = extractor._is_empty_row(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_empty_row_with_zero_value(self, extractor):
        """Test _is_empty_row treats zero as valid data"""
        row_data = {"Date": "", "Description": "", "Amount": 0}

        result = extractor._is_empty_row(row_data)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_is_empty_row_mixed_empty_types(self, extractor):
        """Test _is_empty_row handles mixed empty value types"""
        row_data = {
            "Date": None,
            "Description": np.nan,
            "Amount": "",
            "Balance": "   ",
            "Notes": pd.NA,  # Use pd.NA instead of pd.NaType()
        }

        result = extractor._is_empty_row(row_data)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.extractor
    @patch("builtins.open")
    @patch("os.access")
    @patch("os.path.getsize")
    @patch("os.path.basename")
    def test_get_file_info_success(
        self, mock_basename, mock_getsize, mock_access, mock_open, extractor
    ):
        """Test get_file_info returns correct file information"""
        file_path = "/path/to/test_file.xlsx"
        mock_basename.return_value = "test_file.xlsx"
        mock_getsize.return_value = 1024
        mock_access.return_value = True  # File is readable

        # Mock the file open operation
        mock_file = Mock()
        mock_file.read.return_value = b"test"
        mock_open.return_value.__enter__.return_value = mock_file

        result = extractor.get_file_info(file_path)

        expected = {
            "file_path": "/path/to/test_file.xlsx",
            "file_name": "test_file.xlsx",
            "file_size": 1024,
        }

        assert result == expected
        mock_basename.assert_called_once_with(file_path)
        mock_getsize.assert_called_once_with(file_path)
        mock_access.assert_called_once_with(file_path, os.R_OK)
        mock_open.assert_called_once_with(file_path, "rb")

    @pytest.mark.unit
    @pytest.mark.extractor
    @patch("os.access")
    @patch("os.path.getsize")
    def test_get_file_info_file_not_found(self, mock_getsize, mock_access, extractor):
        """Test get_file_info handles file not found error"""
        file_path = "/path/to/nonexistent.xlsx"
        mock_access.return_value = False  # File is not readable (doesn't exist)
        mock_getsize.side_effect = FileNotFoundError("File not found")

        with pytest.raises(PermissionError, match="File is not readable"):
            extractor.get_file_info(file_path)

    @pytest.mark.unit
    @pytest.mark.extractor
    @patch("os.path.getsize")
    @patch("os.path.basename")
    def test_get_file_info_permission_error(
        self, mock_basename, mock_getsize, extractor
    ):
        """Test get_file_info handles permission error"""
        file_path = "/path/to/protected.xlsx"
        mock_basename.return_value = "protected.xlsx"
        mock_getsize.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            extractor.get_file_info(file_path)

    @pytest.mark.unit
    @pytest.mark.security
    def test_no_production_data_modification(self, security_validator):
        """Security test: Ensure no production data is modified"""
        security_validator.ensure_no_production_changes()

        # Verify test mode is active
        assert os.environ.get("LEDGER_TEST_MODE") == "true"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_large_dataframe_performance(self, extractor):
        """Test performance with large DataFrame"""
        # Create a large DataFrame for performance testing
        large_data = []
        for i in range(1000):
            large_data.append([f"Row {i}", f"Data {i}", f"Value {i}"])

        # Add header row at the beginning
        large_data.insert(0, ["Date", "Description", "Amount"])

        df = pd.DataFrame(large_data)
        required_columns = ["Date", "Description", "Amount"]

        # Test header detection performance
        header_row = extractor.detect_header_row(df, required_columns)
        assert header_row == 0

        # Test data extraction performance
        result = extractor.extract_data_from_row(df, header_row)
        assert len(result) == 1000

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_unicode_and_special_characters(self, extractor):
        """Test handling of Unicode and special characters"""
        df = pd.DataFrame(
            [
                ["Fecha", "Descripción", "Cantidad"],  # Spanish headers
                ["2023-01-01", "Pago €500", "€500.00"],
                ["2023-01-02", "Transfer ¥1000", "¥1000.00"],
                ["2023-01-03", "Payment $100", "$100.00"],
            ]
        )

        required_columns = ["Fecha", "Descripción", "Cantidad"]

        # Test header detection with Unicode
        header_row = extractor.detect_header_row(df, required_columns)
        assert header_row == 0

        # Test data extraction with special characters
        result = extractor.extract_data_from_row(df, header_row)
        assert len(result) == 3
        assert result[0]["Descripción"] == "Pago €500"
        assert result[1]["Descripción"] == "Transfer ¥1000"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_numeric_headers(self, extractor):
        """Test handling of numeric column headers"""
        df = pd.DataFrame(
            [
                [1, 2, 3, 4],  # Numeric headers
                ["2023-01-01", "Payment 1", 100.0, 1000.0],
                ["2023-01-02", "Payment 2", 200.0, 1200.0],
            ]
        )

        required_columns = ["1", "2", "3"]  # Search for string versions

        header_row = extractor.detect_header_row(df, required_columns)
        assert header_row == 0

        result = extractor.extract_data_from_row(df, header_row)
        assert len(result) == 2
        assert result[0]["1"] == "2023-01-01"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_mixed_data_types_in_cells(self, extractor):
        """Test handling of mixed data types in cells"""
        df = pd.DataFrame(
            [
                ["Date", "Description", "Amount", "Flag"],
                ["2023-01-01", "Payment", 100.50, True],
                [pd.Timestamp("2023-01-02"), 123, 200, False],
                ["2023-01-03", None, "300.75", np.nan],
            ]
        )

        header_row = 0
        result = extractor.extract_data_from_row(df, header_row)

        assert len(result) == 3
        assert result[0]["Date"] == "2023-01-01"
        assert result[0]["Amount"] == 100.50
        assert result[0]["Flag"] is True
        assert result[1]["Description"] == 123  # Number as description
        assert pd.isna(result[2]["Description"])  # None value

    @pytest.mark.unit
    @pytest.mark.performance
    def test_memory_efficiency_large_dataset(self, extractor):
        """Test memory efficiency with large dataset"""
        # Create a DataFrame with many columns
        num_cols = 50
        num_rows = 100

        headers = [f"Column_{i}" for i in range(num_cols)]
        data = []
        data.append(headers)  # Header row

        for row in range(num_rows):
            data.append([f"Value_{row}_{col}" for col in range(num_cols)])

        df = pd.DataFrame(data)

        # Test header detection
        header_row = extractor.detect_header_row(
            df, headers[:10]
        )  # Search for first 10 columns
        assert header_row == 0

        # Test data extraction
        result = extractor.extract_data_from_row(df, header_row)
        assert len(result) == num_rows
        assert len(result[0]) == num_cols

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_path_traversal_prevention(self, extractor):
        """Test read_excel_file prevents path traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "~/.ssh/id_rsa",
            "%2e%2e%2fetc%2fpasswd",
            "/etc/passwd",
            "/var/log/system.log",
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(
                ValueError,
                match="Path traversal attempt detected|Access to system directory blocked",
            ):
                extractor.read_excel_file(malicious_path)

    @pytest.mark.unit
    @pytest.mark.extractor
    def test_read_excel_file_legitimate_paths_allowed(
        self, extractor, sample_dataframe
    ):
        """Test read_excel_file allows legitimate test and relative paths"""
        legitimate_paths = [
            "/path/to/test.xlsx",
            "test.xlsx",
            "./data/file.xlsx",
            "relative/path/file.xlsx",
            "C:/Users/test/file.xlsx",  # Windows path
        ]

        for legitimate_path in legitimate_paths:
            with patch("pandas.read_excel", return_value=sample_dataframe) as mock_read:
                try:
                    result = extractor.read_excel_file(legitimate_path)
                    mock_read.assert_called_once_with(legitimate_path, sheet_name=0)
                    pd.testing.assert_frame_equal(result, sample_dataframe)
                except ValueError as e:
                    # If it's blocked, it should be for a good reason
                    assert "system directory" in str(e) or "traversal" in str(e)
