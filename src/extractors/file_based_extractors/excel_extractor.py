"""
Generic Excel Extractor - Handles basic Excel file operations
"""

import os
from typing import Any, Dict, List, Optional

import pandas as pd

__all__ = ["ExcelExtractor"]  # pylint: disable=unused-variable


class ExcelExtractionError(Exception):
    """Custom exception for Excel extraction errors."""


class ExcelExtractor:
    """Generic Excel extractor for basic Excel operations"""

    def __init__(self, config):
        self.config = config

    def read_excel_file(self, file_path: str, sheet_name: int = 0) -> pd.DataFrame:
        """Read Excel file and return DataFrame. Raises ValueError on path traversal attempt."""
        # Path traversal prevention - more precise detection
        if not file_path:
            raise ValueError("File path cannot be empty")

        # Check for actual path traversal patterns
        dangerous_patterns = [
            "..",  # Directory traversal
            "~",  # Home directory expansion
            "%2e%2e",  # URL encoded ..
        ]

        for pattern in dangerous_patterns:
            if pattern in file_path:
                raise ValueError(f"Path traversal attempt detected: {file_path}")

        # Block access to system directories but allow temporary directories
        system_dirs = ["/etc/", "/var/log/", "/var/lib/", "/usr/", "/bin/", "/sbin/"]
        temp_dirs = ["/tmp/", "/var/tmp/", "/var/folders/", "/private/var/folders/"]

        # Allow temporary directories for testing
        is_temp_file = any(temp_dir in file_path for temp_dir in temp_dirs)

        if not is_temp_file:
            for sys_dir in system_dirs:
                if file_path.startswith(sys_dir):
                    raise ValueError(f"Access to system directory blocked: {file_path}")

        try:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as exception:
            raise ExcelExtractionError(
                f"Error reading Excel file: {exception}"
            ) from exception

    def detect_header_row(
        self, df: pd.DataFrame, required_columns: List[str], max_search_rows: int = 20
    ) -> Optional[int]:
        """Detect header row by looking for required columns"""
        for row_idx in range(min(max_search_rows, len(df))):
            row = df.iloc[row_idx]

            # Convert row to lowercase strings for comparison
            row_values = [str(val).lower().strip() for val in row if not pd.isna(val)]

            # Check if all required columns are present
            matches = 0
            for required_col in required_columns:
                if any(required_col.lower() in val for val in row_values):
                    matches += 1

            # If most required columns are found, consider this the header row
            if matches >= len(required_columns) * 0.7:  # 70% match threshold
                return row_idx

        return None

    def extract_data_from_row(
        self, df: pd.DataFrame, header_row: int
    ) -> List[Dict[str, Any]]:
        """Extract data starting from the row after header"""
        # Use header row as column names
        header_values = df.iloc[header_row].values

        # Start from the row after header
        data_rows = []
        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]

            # Create dictionary with header as keys
            row_data = {}
            for col_idx, header in enumerate(header_values):
                if col_idx < len(row):
                    row_data[str(header)] = row.iloc[col_idx]

            # Skip completely empty rows
            if self._is_empty_row(row_data):
                continue

            data_rows.append(row_data)

        return data_rows

    def _is_empty_row(self, row_data: Dict[str, Any]) -> bool:
        """Check if row is completely empty"""
        for value in row_data.values():
            if not pd.isna(value) and str(value).strip() != "":
                return False
        return True

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information, robustly checking for read permissions"""
        # Path traversal prevention - same as read_excel_file
        if not file_path:
            raise ValueError("File path cannot be empty")

        # Check for actual path traversal patterns
        dangerous_patterns = [
            "..",  # Directory traversal
            "~",  # Home directory expansion
            "%2e%2e",  # URL encoded ..
        ]

        for pattern in dangerous_patterns:
            if pattern in file_path:
                raise ValueError(f"Path traversal attempt detected: {file_path}")

        # Block access to system directories but allow temporary directories
        system_dirs = ["/etc/", "/var/log/", "/var/lib/", "/usr/", "/bin/", "/sbin/"]
        temp_dirs = ["/tmp/", "/var/tmp/", "/var/folders/", "/private/var/folders/"]

        # Allow temporary directories for testing
        is_temp_file = any(temp_dir in file_path for temp_dir in temp_dirs)

        if not is_temp_file:
            for sys_dir in system_dirs:
                if file_path.startswith(sys_dir):
                    raise ValueError(f"Access to system directory blocked: {file_path}")

        # Explicitly check for read permission
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")

        # Attempt to open the file for reading to trigger permission errors
        with open(file_path, "rb") as file_handle:
            file_handle.read(
                1
            )  # Read a single byte (or nothing, just to check permissions)

        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
        }
