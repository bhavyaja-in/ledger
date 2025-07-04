#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.extractors.channel_based_extractors.icici_bank_extractor import IciciBankExtractor
import pandas as pd
import tempfile

def test_performance_logic():
    print("Testing performance test logic...")
    
    # Create extractor
    config = {"processors": {"icici_bank": {"enabled": True}}}
    extractor = IciciBankExtractor(config)
    
    print(f"Required columns: {extractor.required_columns}")
    
    # Create test data exactly like performance test
    transactions = []
    for i in range(5):  # Just 5 rows for testing
        transactions.append({
            "date": f"{(i % 28) + 1:02d}/01/2023",
            "description": f"Transaction {i}",
            "debit_amount": f"{(i * 10) % 5000}.00" if i % 2 == 0 else "",
            "credit_amount": f"{(i * 15) % 3000}.00" if i % 2 == 1 else "",
            "balance": f"{10000 + i * 100}.00",
        })
    
    # Use exact ICICI Bank Excel column names and order (only required columns)
    icici_transactions = []
    for i, trans in enumerate(transactions):
        withdrawal = f"{(i * 10) % 5000}.00" if i % 2 == 0 else ""
        deposit = f"{(i * 15) % 3000}.00" if i % 2 == 1 else ""
        if not withdrawal and not deposit:
            withdrawal = "100.00"
        remarks = trans.get("description", f"Transaction {i}") or f"Transaction {i}"
        icici_trans = {
            "S No.": f"{i+1}",
            "Transaction Date": trans.get("date", f"{(i % 28) + 1:02d}/01/2023"),
            "Transaction Remarks": remarks,
            "Withdrawal Amount (INR )": withdrawal,
            "Deposit Amount (INR )": deposit,
            "Balance (INR )": trans.get("balance", f"{10000 + i * 100}.00"),
        }
        icici_transactions.append(icici_trans)
    
    print(f"Created {len(icici_transactions)} rows")
    print("Sample row:", icici_transactions[0])
    
    df = pd.DataFrame(icici_transactions)
    print(f"Final DataFrame shape: {df.shape}")
    print(f"Final DataFrame columns: {df.columns.tolist()}")
    
    # Check if columns match required_columns
    df_columns_lower = [col.lower().strip() for col in df.columns]
    required_lower = [col.lower().strip() for col in extractor.required_columns]
    print(f"DataFrame columns (lowercase): {df_columns_lower}")
    print(f"Required columns (lowercase): {required_lower}")
    print(f"Columns match: {df_columns_lower == required_lower}")
    
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
    test_performance_logic() 