#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.extractors.channel_based_extractors.icici_bank_extractor import IciciBankExtractor
import pandas as pd
import tempfile

def test_extractor():
    print("Testing ICICI Bank Extractor...")
    
    # Create extractor
    config = {"processors": {"icici_bank": {"enabled": True}}}
    extractor = IciciBankExtractor(config)
    
    print(f"Required columns: {extractor.required_columns}")
    
    # Create test data exactly like performance tests
    test_data = []
    for i in range(5):  # Just 5 rows for testing
        # Ensure at least one valid amount per row
        withdrawal = f"{(i * 10) % 5000}.00" if i % 2 == 0 else ""
        deposit = f"{(i * 15) % 3000}.00" if i % 2 == 1 else ""
        if not withdrawal and not deposit:
            withdrawal = "100.00"  # fallback to ensure at least one valid amount
        remarks = f"Transaction {i}"
        
        row = {
            "Transaction Date": f"{(i % 28) + 1:02d}/01/2023",
            "Transaction Remarks": remarks,
            "Withdrawal Amount (INR )": withdrawal,
            "Deposit Amount (INR )": deposit,
            "Balance (INR )": f"{10000 + i * 100}.00",
            "S No.": f"TXN{i:04d}",
        }
        test_data.append(row)
    
    print(f"Test data created: {len(test_data)} rows")
    print("Sample row:", test_data[0])
    
    # Test filtering logic directly
    print("\nTesting filtering logic:")
    for i, row in enumerate(test_data):
        has_essential = extractor._has_essential_fields(row)
        is_header_like = extractor._is_header_like_row(row)
        remarks = str(row.get("Transaction Remarks", "")).strip()
        remarks_valid = remarks and remarks.lower() not in ["nan", "none", ""]
        
        print(f"Row {i}: has_essential={has_essential}, is_header_like={is_header_like}, remarks_valid={remarks_valid}")
        print(f"  Date: '{row.get('Transaction Date', '')}'")
        print(f"  Withdrawal: '{row.get('Withdrawal Amount (INR )', '')}'")
        print(f"  Deposit: '{row.get('Deposit Amount (INR )', '')}'")
        print(f"  Remarks: '{remarks}'")
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    print(f"\nDataFrame columns: {df.columns.tolist()}")
    print(f"DataFrame shape: {df.shape}")
    
    # Save to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        df.to_excel(temp_file.name, index=False)
        temp_file_path = temp_file.name
    
    try:
        print(f"Excel file created: {temp_file_path}")
        
        # Extract data
        result = extractor.extract(temp_file_path)
        
        print(f"Extraction result keys: {result.keys()}")
        print(f"Total rows: {result.get('total_rows', 'N/A')}")
        print(f"Valid transactions: {result.get('valid_transactions', 'N/A')}")
        print(f"Transactions list length: {len(result.get('transactions', []))}")
        
        if result.get('transactions'):
            print("First transaction:", result['transactions'][0])
        
    finally:
        os.unlink(temp_file_path)

if __name__ == "__main__":
    test_extractor() 