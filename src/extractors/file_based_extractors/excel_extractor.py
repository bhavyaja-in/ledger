"""
Generic Excel Extractor - Handles basic Excel file operations
"""
from typing import Any, Dict, List, Optional

import pandas as pd


class ExcelExtractor:
    """Generic Excel extractor for basic Excel operations"""

    def __init__(self, config):
        self.config = config

    def read_excel_file(self, file_path: str, sheet_name: int = 0) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}")

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

    def extract_data_from_row(self, df: pd.DataFrame, header_row: int) -> List[Dict[str, Any]]:
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
        """Get basic file information"""
        import os

        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
        }
