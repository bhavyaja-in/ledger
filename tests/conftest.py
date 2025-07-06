"""
Enterprise-grade pytest configuration and fixtures.

This module provides comprehensive test fixtures for isolated, secure testing
of the financial data processing system.
"""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import yaml


# Test Environment Setup
@pytest.fixture(scope="session", autouse=True)
def test_environment():  # pylint: disable=unused-variable
    """Ensure test environment is properly configured"""
    os.environ["LEDGER_TEST_MODE"] = "true"
    yield
    # Cleanup after all tests
    if "LEDGER_TEST_MODE" in os.environ:
        del os.environ["LEDGER_TEST_MODE"]


# Integration Test Environment Fixture
@pytest.fixture
def integration_test_environment():  # pylint: disable=unused-variable
    """Create complete isolated test environment with realistic data"""
    # Create temporary directory structure
    test_dir = tempfile.mkdtemp(prefix="ledger_integration_test_")

    test_env = {
        "test_dir": test_dir,
        "data_dir": Path(test_dir) / "data",
        "config_dir": Path(test_dir) / "config",
        "backup_dir": Path(test_dir) / "backup",
        "temp_files": [],
    }

    # Create directory structure
    for dir_path in [
        test_env["data_dir"],
        test_env["config_dir"],
        test_env["backup_dir"],
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create bank-specific data directories
    icici_dir = test_env["data_dir"] / "icici_bank"
    icici_dir.mkdir(exist_ok=True)

    yield test_env

    # Cleanup
    try:
        shutil.rmtree(test_dir)
    except Exception:  # pylint: disable=broad-except
        pass  # Best effort cleanup


@pytest.fixture
def test_configurations(integration_test_environment):  # pylint: disable=redefined-outer-name
    """Create test configuration files"""
    test_env = integration_test_environment
    config_dir = test_env["config_dir"]

    # Test config.yaml
    integration_test_config = {
        "database": {"url": "sqlite:///:memory:", "test_prefix": "test_"},
        "processors": {"icici_bank": {"currency": "INR", "date_format": "%d-%m-%Y"}},
        "backup": {
            "enabled": False,
            "git_repo": None,
        },  # Disable for integration tests
    }

    config_file = config_dir / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(integration_test_config, f)

    # Test categories.yaml
    test_categories = {
        "categories": [
            {"name": "income"},
            {"name": "food"},
            {"name": "transport"},
            {"name": "shopping"},
            {"name": "entertainment"},
            {"name": "transfer"},
            {"name": "other"},
        ]
    }

    categories_file = config_dir / "categories.yaml"
    with open(categories_file, "w", encoding="utf-8") as f:
        yaml.dump(test_categories, f)

    test_env["config_files"] = {
        "config": str(config_file),
        "categories": str(categories_file),
    }

    return test_env["config_files"]


@pytest.fixture
def realistic_transaction_files(
    integration_test_environment,
):  # pylint: disable=redefined-outer-name
    """Create realistic bank statement files for testing"""
    test_env = integration_test_environment
    icici_dir = test_env["data_dir"] / "icici_bank"

    # Create realistic ICICI Bank statement data
    realistic_test_files = {}

    # File 1: Mixed transaction types with currency detection scenarios
    transactions_mixed = [
        {
            "Transaction Date": "01-01-2024",
            "Transaction Remarks": "UPI-SWIGGY-BANGALORE-9876543210@paytm",
            "Withdrawal Amount (INR )": "250.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "15750.00",
            "S No.": "1",
        },
        {
            "Transaction Date": "02-01-2024",
            "Transaction Remarks": "SALARY CREDIT FROM COMPANY XYZ",
            "Withdrawal Amount (INR )": "",
            "Deposit Amount (INR )": "50000.00",
            "Balance (INR )": "65750.00",
            "S No.": "2",
        },
        {
            "Transaction Date": "03-01-2024",
            "Transaction Remarks": "UPI-AMAZON-PAYMENT-8765432109@okaxis",
            "Withdrawal Amount (INR )": "1299.99",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "64450.01",
            "S No.": "3",
        },
        {
            "Transaction Date": "04-01-2024",
            "Transaction Remarks": "INTERNATIONAL TXN - USD 45.50 - NETFLIX",
            "Withdrawal Amount (INR )": "3787.25",  # Converted amount
            "Deposit Amount (INR )": "",
            "Balance (INR )": "60662.76",
            "S No.": "4",
        },
        {
            "Transaction Date": "05-01-2024",
            "Transaction Remarks": "UPI-JOHNSMITH-9123456789@paytm",
            "Withdrawal Amount (INR )": "2500.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "58162.76",
            "S No.": "5",
        },
    ]

    # Create Excel file with mixed transactions
    mixed_df = pd.DataFrame(transactions_mixed)
    mixed_file = icici_dir / "statement_mixed_2024_01.xlsx"
    mixed_df.to_excel(mixed_file, index=False)
    realistic_test_files["mixed_transactions"] = str(mixed_file)

    # File 2: Split transaction scenarios
    transactions_splits = [
        {
            "Transaction Date": "10-01-2024",
            "Transaction Remarks": "RESTAURANT BILL - GROUP DINNER",
            "Withdrawal Amount (INR )": "4800.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "53362.76",
            "S No.": "6",
        },
        {
            "Transaction Date": "11-01-2024",
            "Transaction Remarks": "UBER TRIP - AIRPORT",
            "Withdrawal Amount (INR )": "850.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "52512.76",
            "S No.": "7",
        },
    ]

    splits_df = pd.DataFrame(transactions_splits)
    splits_file = icici_dir / "statement_splits_2024_01.xlsx"
    splits_df.to_excel(splits_file, index=False)
    realistic_test_files["split_transactions"] = str(splits_file)

    # File 3: Duplicate detection scenarios
    transactions_duplicates = [
        {
            "Transaction Date": "15-01-2024",
            "Transaction Remarks": "UPI-SWIGGY-BANGALORE-9876543210@paytm",
            "Withdrawal Amount (INR )": "250.00",  # Same as first file
            "Deposit Amount (INR )": "",
            "Balance (INR )": "52262.76",
            "S No.": "8",
        },
        {
            "Transaction Date": "16-01-2024",
            "Transaction Remarks": "NEW UNIQUE TRANSACTION",
            "Withdrawal Amount (INR )": "150.00",
            "Deposit Amount (INR )": "",
            "Balance (INR )": "52112.76",
            "S No.": "9",
        },
    ]

    duplicates_df = pd.DataFrame(transactions_duplicates)
    duplicates_file = icici_dir / "statement_duplicates_2024_01.xlsx"
    duplicates_df.to_excel(duplicates_file, index=False)
    realistic_test_files["duplicate_scenarios"] = str(duplicates_file)

    # File 4: Corrupted/malformed file for error testing
    corrupted_file = icici_dir / "corrupted_statement.xlsx"
    with open(corrupted_file, "w", encoding="utf-8") as f:
        f.write("This is not a valid Excel file")
    realistic_test_files["corrupted_file"] = str(corrupted_file)

    # File 5: Empty file
    empty_file = icici_dir / "empty_statement.xlsx"
    empty_dataframe = pd.DataFrame()
    empty_dataframe.to_excel(empty_file, index=False)
    realistic_test_files["empty_file"] = str(empty_file)

    test_env["test_files"] = realistic_test_files
    return realistic_test_files


# Temporary Directory Fixtures
@pytest.fixture
def temp_dir():  # pylint: disable=unused-variable
    """Create isolated temporary directory for test files"""
    with tempfile.TemporaryDirectory(prefix="ledger_test_") as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_dir(temp_dir):  # pylint: disable=redefined-outer-name
    """Create temporary config directory"""
    base_dir = temp_dir
    config_dir = base_dir / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_data_dir(temp_dir):  # pylint: disable=redefined-outer-name
    """Create temporary data directory"""
    base_dir = temp_dir
    data_dir = base_dir / "data"
    data_dir.mkdir()
    return data_dir


# Configuration Fixtures
@pytest.fixture
def test_config(temp_config_dir):  # pylint: disable=redefined-outer-name
    """Create test configuration"""
    test_config_data = {
        "database": {"url": "sqlite:///:memory:", "test_prefix": "test_"},
        "processors": {"icici_bank": {"enabled": True, "data_path": "data/icici_bank"}},
        "logging": {"level": "DEBUG"},
    }

    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(test_config_data, f)

    return test_config_data


@pytest.fixture
def test_categories_config(temp_config_dir):  # pylint: disable=redefined-outer-name
    """Create test categories configuration"""
    base_config_dir = temp_config_dir
    test_categories_data = {
        "categories": [
            {"name": "income"},
            {"name": "food"},
            {"name": "transport"},
            {"name": "shopping"},
            {"name": "entertainment"},
            {"name": "utilities"},
            {"name": "healthcare"},
            {"name": "other"},
        ]
    }

    categories_file = base_config_dir / "categories.yaml"
    with open(categories_file, "w", encoding="utf-8") as f:
        yaml.dump(test_categories_data, f)

    return test_categories_data


# Database Fixtures
@pytest.fixture
def mock_db_manager():  # pylint: disable=unused-variable
    """Create mock database manager"""
    mock_manager = Mock()
    mock_manager.get_session.return_value = Mock()
    mock_manager.models = {
        "TransactionEnum": Mock(),
        "Transaction": Mock(),
        "Institution": Mock(),
        "ProcessedFile": Mock(),
        "SkippedTransaction": Mock(),
        "ProcessingLog": Mock(),
        "TransactionSplit": Mock(),
    }
    return mock_manager


@pytest.fixture
def in_memory_db():  # pylint: disable=unused-variable
    """Create in-memory SQLite database for testing"""
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


# Test Data Fixtures
@pytest.fixture
def sample_transaction_data():  # pylint: disable=unused-variable
    """Sample transaction data for testing"""
    return [
        {
            "date": "2023-01-01",
            "description": "SALARY CREDIT",
            "debit_amount": "",
            "credit_amount": "50000.00",
            "balance": "50000.00",
            "reference": "SAL001",
        },
        {
            "date": "2023-01-02",
            "description": "SWIGGY FOOD ORDER",
            "debit_amount": "450.00",
            "credit_amount": "",
            "balance": "49550.00",
            "reference": "UPI001",
        },
        {
            "date": "2023-01-03",
            "description": "PETROL PUMP PAYMENT",
            "debit_amount": "2000.00",
            "credit_amount": "",
            "balance": "47550.00",
            "reference": "CARD001",
        },
    ]


@pytest.fixture
def sample_dataframe(sample_transaction_data):  # pylint: disable=redefined-outer-name
    """Sample pandas DataFrame for testing"""
    transaction_data = sample_transaction_data
    return pd.DataFrame(transaction_data)


@pytest.fixture
def sample_excel_file(
    temp_data_dir, sample_transaction_data
):  # pylint: disable=redefined-outer-name
    """Create sample Excel file for testing"""
    base_data_dir = temp_data_dir
    transaction_data = sample_transaction_data
    sample_df = pd.DataFrame(transaction_data)
    excel_file = base_data_dir / "sample_transactions.xlsx"
    sample_df.to_excel(excel_file, index=False)
    return str(excel_file)


# Mock Fixtures
@pytest.fixture
def mock_file_system():  # pylint: disable=unused-variable
    """Mock file system operations"""
    with patch("os.path.exists") as mock_exists, patch("builtins.open") as mock_open:
        mock_exists.return_value = True
        yield {"exists": mock_exists, "open": mock_open}


@pytest.fixture
def mock_yaml_operations():  # pylint: disable=unused-variable
    """Mock YAML operations"""
    with patch("yaml.safe_load") as mock_load, patch("yaml.dump") as mock_dump:
        yield {"load": mock_load, "dump": mock_dump}


# Validation Fixtures
@pytest.fixture
def security_validator():  # pylint: disable=unused-variable
    """Security validation utilities"""

    class SecurityValidator:
        @staticmethod
        def ensure_no_production_changes():
            """Ensure no production database/config changes"""
            assert os.environ.get("LEDGER_TEST_MODE") == "true"

        @staticmethod
        def validate_test_isolation():
            """Validate test isolation"""
            # Check no production configs are being modified
            prod_configs = ["config/config.yaml", "config/categories.yaml"]
            for config_path in prod_configs:
                if os.path.exists(config_path):
                    # Ensure files aren't being modified during tests
                    stat_before = os.path.getmtime(config_path)
                    return lambda: os.path.getmtime(config_path) == stat_before
            return lambda: True

    return SecurityValidator()


# Coverage Fixtures
@pytest.fixture
def coverage_tracker():  # pylint: disable=unused-variable
    """Track test coverage requirements"""

    class CoverageTracker:
        def __init__(self):
            self.covered_lines = set()
            self.total_lines = set()

        def mark_line_covered(self, file_path, line_number):
            self.covered_lines.add(f"{file_path}:{line_number}")

        def add_total_line(self, file_path, line_number):
            self.total_lines.add(f"{file_path}:{line_number}")

        def get_coverage_percentage(self):
            if not self.total_lines:
                return 100.0
            return (len(self.covered_lines) / len(self.total_lines)) * 100

    return CoverageTracker()


# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():  # pylint: disable=unused-variable
    """Automatic cleanup after each test"""
    yield
    # Clean up any test artifacts
    import gc

    gc.collect()
