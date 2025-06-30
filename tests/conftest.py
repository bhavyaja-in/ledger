"""
Enterprise-grade pytest configuration and fixtures.

This module provides comprehensive test fixtures for isolated, secure testing
of the financial data processing system.
"""
import os
import sqlite3
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import yaml


# Test Environment Setup
@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Ensure test environment is properly configured"""
    os.environ["LEDGER_TEST_MODE"] = "true"
    yield
    # Cleanup after all tests
    if "LEDGER_TEST_MODE" in os.environ:
        del os.environ["LEDGER_TEST_MODE"]


# Temporary Directory Fixtures
@pytest.fixture
def temp_dir():
    """Create isolated temporary directory for test files"""
    with tempfile.TemporaryDirectory(prefix="ledger_test_") as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_dir(temp_dir):
    """Create temporary config directory"""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_data_dir(temp_dir):
    """Create temporary data directory"""
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    return data_dir


# Configuration Fixtures
@pytest.fixture
def test_config(temp_config_dir):
    """Create test configuration"""
    config = {
        "database": {"url": "sqlite:///:memory:", "test_prefix": "test_"},
        "processors": {"icici_bank": {"enabled": True, "data_path": "data/icici_bank"}},
        "logging": {"level": "DEBUG"},
    }

    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return config


@pytest.fixture
def test_categories_config(temp_config_dir):
    """Create test categories configuration"""
    categories = {
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

    categories_file = temp_config_dir / "categories.yaml"
    with open(categories_file, "w") as f:
        yaml.dump(categories, f)

    return categories


# Database Fixtures
@pytest.fixture
def mock_db_manager():
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
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


# Test Data Fixtures
@pytest.fixture
def sample_transaction_data():
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
def sample_dataframe(sample_transaction_data):
    """Sample pandas DataFrame for testing"""
    return pd.DataFrame(sample_transaction_data)


@pytest.fixture
def sample_excel_file(temp_data_dir, sample_transaction_data):
    """Create sample Excel file for testing"""
    df = pd.DataFrame(sample_transaction_data)
    excel_file = temp_data_dir / "sample_transactions.xlsx"
    df.to_excel(excel_file, index=False)
    return str(excel_file)


# Mock Fixtures
@pytest.fixture
def mock_file_system():
    """Mock file system operations"""
    with patch("os.path.exists") as mock_exists, patch("builtins.open") as mock_open:
        mock_exists.return_value = True
        yield {"exists": mock_exists, "open": mock_open}


@pytest.fixture
def mock_yaml_operations():
    """Mock YAML operations"""
    with patch("yaml.safe_load") as mock_load, patch("yaml.dump") as mock_dump:
        yield {"load": mock_load, "dump": mock_dump}


# Validation Fixtures
@pytest.fixture
def security_validator():
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
def coverage_tracker():
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
def cleanup_after_test():
    """Automatic cleanup after each test"""
    yield
    # Clean up any test artifacts
    import gc

    gc.collect()
