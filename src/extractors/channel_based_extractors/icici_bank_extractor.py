"""
ICICI Bank Extractor - Handles ICICI Bank specific Excel extraction logic
"""

import os
import sys
from typing import Any, Dict, List

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.extractors.file_based_extractors.excel_extractor import ExcelExtractor


class IciciBankExtractor:
    """ICICI Bank specific extractor"""

    def __init__(self, config):
        self.config = config
        self.excel_extractor = ExcelExtractor(config)

        # ICICI Bank specific column requirements
        self.required_columns = [
            "transaction date",
            "transaction remarks",
            "withdrawal amount (inr )",
            "deposit amount (inr )",
            "balance (inr )",
            "s no.",
        ]

    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract transactions from ICICI Bank Excel file"""
        try:
            # Step 1: Read Excel file using generic extractor
            df = self.excel_extractor.read_excel_file(file_path)

            # Normalize columns for comparison
            df_columns_normalized = [str(col).strip().lower() for col in df.columns]
            required_columns_normalized = [
                col.strip().lower() for col in self.required_columns
            ]

            # Step 2: Detect header row
            # If columns match required columns, treat as header_row=0
            if all(
                any(req in col for col in df_columns_normalized)
                for req in required_columns_normalized
            ):
                header_row = 0
            else:
                header_row = self.excel_extractor.detect_header_row(
                    df, self.required_columns
                )
                if header_row is None:
                    header_row = 0

            # Step 3: Extract data
            transactions = self.excel_extractor.extract_data_from_row(df, header_row)

            # Step 4: Filter valid transactions (ICICI specific logic)
            transactions = self._filter_valid_transactions(transactions)

            # Step 5: Get file info
            file_info = self.excel_extractor.get_file_info(file_path)

            return {
                "file_info": file_info,
                "header_row": header_row,
                "total_rows": len(transactions),
                "valid_transactions": len(transactions),
                "transactions": [{"data": trans} for trans in transactions],
            }

        except Exception as e:
            raise Exception(f"Error extracting ICICI Bank data: {e}")

    def _filter_valid_transactions(
        self, raw_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter valid transactions specific to ICICI Bank format"""
        valid_transactions = []

        for row_data in raw_data:
            # Skip if essential fields are missing
            if not self._has_essential_fields(row_data):
                continue

            # Skip header-like rows that might appear in data
            if self._is_header_like_row(row_data):
                continue

            # Skip completely empty transaction remarks
            remarks = str(row_data.get("Transaction Remarks", "")).strip()
            if not remarks or remarks.lower() in ["nan", "none", ""]:
                continue

            valid_transactions.append(row_data)

        return valid_transactions

    def _has_essential_fields(self, row_data: Dict[str, Any]) -> bool:
        """Check if row has essential fields for a transaction"""
        # Must have transaction date
        date_field = None
        for k, v in row_data.items():
            if k.strip().lower() == "transaction date":
                date_field = v
                break
        if not date_field or str(date_field).strip() in ["", "nan", "None"]:
            return False

        # Must have either debit or credit amount
        debit = None
        credit = None
        for k, v in row_data.items():
            key_norm = k.strip().lower()
            if "withdrawal amount" in key_norm:
                debit = v
            if "deposit amount" in key_norm:
                credit = v

        has_amount = False
        if debit is not None and str(debit).strip() not in ["", "nan", "None"]:
            try:
                float(debit)
                has_amount = True
            except (ValueError, TypeError):
                pass

        if credit is not None and str(credit).strip() not in ["", "nan", "None"]:
            try:
                float(credit)
                has_amount = True
            except (ValueError, TypeError):
                pass

        return has_amount

    def _is_header_like_row(self, row_data: Dict[str, Any]) -> bool:
        """Check if row looks like a header row that appeared in data"""
        remarks = str(row_data.get("Transaction Remarks", "")).lower()

        header_indicators = [
            "transaction remarks",
            "transaction date",
            "withdrawal amount",
            "deposit amount",
            "balance",
            "cheque number",
        ]

        return any(indicator in remarks for indicator in header_indicators)
