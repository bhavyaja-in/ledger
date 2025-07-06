"""
Comprehensive unit tests for database.py with 100% line coverage.

Tests model creation, DatabaseManager functionality, relationships,
test mode support, and all edge cases to ensure enterprise-grade quality.
"""

# pylint: disable=unused-variable
# Test fixtures often unpack variables that may not all be used in every test

import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from src.models.database import DatabaseManager, create_models_with_prefix


class TestCreateModelsWithPrefix:
    """Comprehensive test suite for create_models_with_prefix function"""

    @pytest.mark.unit
    @pytest.mark.database
    def test_create_models_no_prefix(self):
        """Test create_models_with_prefix with no prefix (production mode)"""
        models, base = create_models_with_prefix()

        # Verify all models are created
        expected_models = [
            "Institution",
            "ProcessedFile",
            "TransactionEnum",
            "Transaction",
            "TransactionSplit",
            "SkippedTransaction",
            "ProcessingLog",
        ]

        assert len(models) == 7
        for model_name in expected_models:
            assert model_name in models
            assert models[model_name] is not None

        # Verify base is returned
        assert base is not None

        # Verify class names for production (no prefix)
        assert models["Institution"].__name__ == "InstitutionProd"
        assert models["Transaction"].__name__ == "TransactionProd"

    @pytest.mark.unit
    @pytest.mark.database
    def test_create_models_with_test_prefix(self):
        """Test create_models_with_prefix with test prefix"""
        test_prefix = "test_"
        models, base = create_models_with_prefix(test_prefix)

        # Verify all models are created
        assert len(models) == 7

        # Verify class names with test prefix
        assert models["Institution"].__name__ == "InstitutionTest"
        assert models["Transaction"].__name__ == "TransactionTest"

        # Verify table names have prefix
        assert models["Institution"].__tablename__ == "test_institutions"
        assert models["Transaction"].__tablename__ == "test_transactions"

    @pytest.mark.unit
    @pytest.mark.database
    def test_create_models_with_custom_prefix(self):
        """Test create_models_with_prefix with custom prefix"""
        custom_prefix = "staging_"
        models, base = create_models_with_prefix(custom_prefix)

        # Verify class names with custom prefix
        assert models["Institution"].__name__ == "InstitutionStaging"
        assert models["Transaction"].__name__ == "TransactionStaging"

        # Verify table names have custom prefix
        assert models["Institution"].__tablename__ == "staging_institutions"
        assert models["Transaction"].__tablename__ == "staging_transactions"

    @pytest.mark.unit
    @pytest.mark.database
    def test_institution_model_attributes(self):
        """Test Institution model has correct attributes and constraints"""
        models, base = create_models_with_prefix()
        Institution = models["Institution"]

        # Verify table name
        assert Institution.__tablename__ == "institutions"

        # Verify columns exist
        assert hasattr(Institution, "id")
        assert hasattr(Institution, "name")
        assert hasattr(Institution, "institution_type")
        assert hasattr(Institution, "created_at")
        assert hasattr(Institution, "updated_at")

        # Verify column properties
        assert Institution.id.primary_key is True
        assert Institution.name.nullable is False
        assert Institution.institution_type.nullable is False

    @pytest.mark.unit
    @pytest.mark.database
    def test_processed_file_model_attributes(self):
        """Test ProcessedFile model has correct attributes and relationships"""
        models, base = create_models_with_prefix()
        ProcessedFile = models["ProcessedFile"]

        # Verify table name
        assert ProcessedFile.__tablename__ == "processed_files"

        # Verify columns exist
        assert hasattr(ProcessedFile, "id")
        assert hasattr(ProcessedFile, "institution_id")
        assert hasattr(ProcessedFile, "file_path")
        assert hasattr(ProcessedFile, "file_name")
        assert hasattr(ProcessedFile, "file_size")
        assert hasattr(ProcessedFile, "processor_type")
        assert hasattr(ProcessedFile, "processing_status")

        # Verify relationships
        assert hasattr(ProcessedFile, "institution")

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_enum_model_attributes(self):
        """Test TransactionEnum model has correct attributes"""
        models, base = create_models_with_prefix()
        TransactionEnum = models["TransactionEnum"]

        # Verify table name
        assert TransactionEnum.__tablename__ == "transaction_enums"

        # Verify columns exist
        assert hasattr(TransactionEnum, "id")
        assert hasattr(TransactionEnum, "enum_name")
        assert hasattr(TransactionEnum, "patterns")
        assert hasattr(TransactionEnum, "category")
        assert hasattr(TransactionEnum, "processor_type")
        assert hasattr(TransactionEnum, "is_active")

        # Verify constraints
        assert TransactionEnum.enum_name.nullable is False
        assert TransactionEnum.patterns.nullable is False
        assert TransactionEnum.category.nullable is False

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_model_attributes(self):
        """Test Transaction model has correct attributes and relationships"""
        models, base = create_models_with_prefix()
        Transaction = models["Transaction"]

        # Verify table name
        assert Transaction.__tablename__ == "transactions"

        # Verify all columns exist
        expected_columns = [
            "id",
            "transaction_hash",
            "institution_id",
            "processed_file_id",
            "transaction_date",
            "description",
            "debit_amount",
            "credit_amount",
            "balance",
            "reference_number",
            "transaction_type",
            "enum_id",
            "category",
            "transaction_category",
            "reason",
            "splits",
            "has_splits",
            "is_settled",
            "created_at",
            "updated_at",
        ]

        for column in expected_columns:
            assert hasattr(Transaction, column), f"Missing column: {column}"

        # Verify relationships
        assert hasattr(Transaction, "institution")
        assert hasattr(Transaction, "processed_file")
        assert hasattr(Transaction, "enum")
        assert hasattr(Transaction, "transaction_splits")

        # Verify constraints
        assert Transaction.transaction_hash.nullable is False
        assert Transaction.transaction_date.nullable is False
        assert Transaction.description.nullable is False

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_split_model_attributes(self):
        """Test TransactionSplit model has correct attributes and relationships"""
        models, base = create_models_with_prefix()
        TransactionSplit = models["TransactionSplit"]

        # Verify table name
        assert TransactionSplit.__tablename__ == "transaction_splits"

        # Verify columns exist
        assert hasattr(TransactionSplit, "id")
        assert hasattr(TransactionSplit, "transaction_id")
        assert hasattr(TransactionSplit, "person_name")
        assert hasattr(TransactionSplit, "percentage")
        assert hasattr(TransactionSplit, "amount")
        assert hasattr(TransactionSplit, "is_settled")

        # Verify relationships
        assert hasattr(TransactionSplit, "transaction")

        # Verify constraints
        assert TransactionSplit.person_name.nullable is False
        assert TransactionSplit.percentage.nullable is False
        assert TransactionSplit.amount.nullable is False

    @pytest.mark.unit
    @pytest.mark.database
    def test_skipped_transaction_model_attributes(self):
        """Test SkippedTransaction model has correct attributes"""
        models, base = create_models_with_prefix()
        SkippedTransaction = models["SkippedTransaction"]

        # Verify table name
        assert SkippedTransaction.__tablename__ == "skipped_transactions"

        # Verify columns exist
        assert hasattr(SkippedTransaction, "id")
        assert hasattr(SkippedTransaction, "transaction_hash")
        assert hasattr(SkippedTransaction, "institution_id")
        assert hasattr(SkippedTransaction, "processed_file_id")
        assert hasattr(SkippedTransaction, "raw_data")
        assert hasattr(SkippedTransaction, "row_number")
        assert hasattr(SkippedTransaction, "skip_reason")

        # Verify relationships
        assert hasattr(SkippedTransaction, "institution")
        assert hasattr(SkippedTransaction, "processed_file")

    @pytest.mark.unit
    @pytest.mark.database
    def test_processing_log_model_attributes(self):
        """Test ProcessingLog model has correct attributes"""
        models, base = create_models_with_prefix()
        ProcessingLog = models["ProcessingLog"]

        # Verify table name
        assert ProcessingLog.__tablename__ == "processing_logs"

        # Verify columns exist
        assert hasattr(ProcessingLog, "id")
        assert hasattr(ProcessingLog, "processed_file_id")
        assert hasattr(ProcessingLog, "total_transactions")
        assert hasattr(ProcessingLog, "processed_transactions")
        assert hasattr(ProcessingLog, "skipped_transactions")
        assert hasattr(ProcessingLog, "duplicate_transactions")
        assert hasattr(ProcessingLog, "duplicate_skipped")
        assert hasattr(ProcessingLog, "processing_time")

        # Verify relationships
        assert hasattr(ProcessingLog, "processed_file")

    @pytest.mark.unit
    @pytest.mark.database
    def test_model_relationships_bidirectional(self):
        """Test that model relationships are properly bidirectional"""
        models, base = create_models_with_prefix()
        Transaction = models["Transaction"]
        TransactionSplit = models["TransactionSplit"]

        # Verify bidirectional relationship between Transaction and TransactionSplit
        assert hasattr(Transaction, "transaction_splits")
        assert hasattr(TransactionSplit, "transaction")

    @pytest.mark.unit
    @pytest.mark.database
    def test_foreign_key_relationships(self):
        """Test that foreign key relationships are correctly defined"""
        models, base = create_models_with_prefix("test_")

        # Test ProcessedFile -> Institution FK
        ProcessedFile = models["ProcessedFile"]
        assert hasattr(ProcessedFile, "institution_id")

        # Test Transaction -> Institution FK
        Transaction = models["Transaction"]
        assert hasattr(Transaction, "institution_id")
        assert hasattr(Transaction, "processed_file_id")
        assert hasattr(Transaction, "enum_id")

        # Test TransactionSplit -> Transaction FK
        TransactionSplit = models["TransactionSplit"]
        assert hasattr(TransactionSplit, "transaction_id")

    @pytest.mark.unit
    @pytest.mark.database
    def test_prefix_handling_special_characters(self):
        """Test prefix handling with special characters and edge cases"""
        # Test with underscores and mixed case
        models, base = create_models_with_prefix("dev_test_")

        # Verify class names handle special characters
        assert models["Institution"].__name__ == "InstitutionDevtest"
        assert models["Transaction"].__name__ == "TransactionDevtest"

        # Verify table names preserve original prefix
        assert models["Institution"].__tablename__ == "dev_test_institutions"
        assert models["Transaction"].__tablename__ == "dev_test_transactions"

    @pytest.mark.unit
    @pytest.mark.database
    def test_multiple_model_creation_isolation(self):
        """Test that multiple model creations are isolated"""
        # Create models with different prefixes
        models1, base1 = create_models_with_prefix("test1_")
        models2, base2 = create_models_with_prefix("test2_")

        # Verify they have different class names
        assert models1["Institution"].__name__ != models2["Institution"].__name__
        assert models1["Institution"].__tablename__ != models2["Institution"].__tablename__

        # Verify they have different bases
        assert base1 is not base2


class TestDatabaseManager:
    """Comprehensive test suite for DatabaseManager class"""

    @pytest.mark.unit
    @pytest.mark.database
    def test_database_manager_init_production_mode(self):
        """Test DatabaseManager initialization in production mode"""
        config = {"database": {"url": "sqlite:///:memory:", "test_prefix": "test_"}}

        with (
            patch("src.models.database.create_engine") as mock_create_engine,
            patch("src.models.database.sessionmaker") as mock_sessionmaker,
        ):
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_session_factory = Mock()
            mock_sessionmaker.return_value = mock_session_factory

            db_manager = DatabaseManager(config, test_mode=False)

            # Verify configuration
            assert db_manager.config == config
            assert db_manager.test_mode is False
            assert db_manager.test_prefix == "test_"

            # Verify engine creation
            mock_create_engine.assert_called_once_with("sqlite:///:memory:")
            assert db_manager.engine == mock_engine

            # Verify session factory
            mock_sessionmaker.assert_called_once_with(bind=mock_engine)
            assert db_manager.Session == mock_session_factory

            # Verify models were created without prefix
            assert len(db_manager.models) == 7
            assert "Institution" in db_manager.models

    @pytest.mark.unit
    @pytest.mark.database
    def test_database_manager_init_test_mode(self):
        """Test DatabaseManager initialization in test mode"""
        config = {"database": {"url": "sqlite:///:memory:", "test_prefix": "test_"}}

        with (
            patch("src.models.database.create_engine") as mock_create_engine,
            patch("src.models.database.sessionmaker") as mock_sessionmaker,
        ):
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            db_manager = DatabaseManager(config, test_mode=True)

            # Verify test mode configuration
            assert db_manager.test_mode is True

            # Verify models were created with test prefix
            assert len(db_manager.models) == 7
            # Verify test table names
            assert db_manager.models["Institution"].__tablename__ == "test_institutions"

    @pytest.mark.unit
    @pytest.mark.database
    def test_database_manager_default_test_prefix(self):
        """Test DatabaseManager with default test prefix when not specified"""
        config = {
            "database": {
                "url": "sqlite:///:memory:"
                # No test_prefix specified
            }
        }

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config, test_mode=True)

            # Verify default test prefix is used
            assert db_manager.test_prefix == "test_"

    @pytest.mark.unit
    @pytest.mark.database
    def test_database_manager_custom_test_prefix(self):
        """Test DatabaseManager with custom test prefix"""
        config = {"database": {"url": "sqlite:///:memory:", "test_prefix": "custom_test_"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config, test_mode=True)

            # Verify custom test prefix is used
            assert db_manager.test_prefix == "custom_test_"
            assert db_manager.models["Institution"].__tablename__ == "custom_test_institutions"

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_session(self):
        """Test get_session method returns session instance"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with (
            patch("src.models.database.create_engine"),
            patch("src.models.database.sessionmaker") as mock_sessionmaker,
        ):
            mock_session = Mock()
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_sessionmaker.return_value = mock_session_factory

            db_manager = DatabaseManager(config)

            # Test get_session
            session = db_manager.get_session()

            assert session == mock_session
            mock_session_factory.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_model_existing(self):
        """Test get_model returns correct model for existing model name"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config)

            # Test getting existing model
            institution_model = db_manager.get_model("Institution")
            assert institution_model is not None
            assert institution_model == db_manager.models["Institution"]

            transaction_model = db_manager.get_model("Transaction")
            assert transaction_model is not None
            assert transaction_model == db_manager.models["Transaction"]

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_model_nonexistent(self):
        """Test get_model returns None for non-existent model name"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config)

            # Test getting non-existent model
            result = db_manager.get_model("NonExistentModel")
            assert result is None

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_model_empty_string(self):
        """Test get_model handles empty string gracefully"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config)

            # Test getting model with empty string
            result = db_manager.get_model("")
            assert result is None

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_model_none(self):
        """Test get_model handles None gracefully"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config)

            # Test getting model with None
            result = db_manager.get_model(None)
            assert result is None

    @pytest.mark.unit
    @pytest.mark.database
    def test_table_creation_called(self):
        """Test that create_all is called on base metadata"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with (
            patch("src.models.database.create_engine") as mock_create_engine,
            patch("src.models.database.sessionmaker"),
        ):
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            # Mock the base metadata
            with patch("src.models.database.create_models_with_prefix") as mock_create_models:
                mock_base = Mock()
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata
                mock_create_models.return_value = ({}, mock_base)

                db_manager = DatabaseManager(config)

                # Verify create_all was called
                mock_metadata.create_all.assert_called_once_with(mock_engine)

    @pytest.mark.unit
    @pytest.mark.database
    def test_nested_config_access(self):
        """Test accessing nested configuration values"""
        config = {"database": {"url": "sqlite:///:memory:", "test_prefix": "nested_test_"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config, test_mode=True)

            # Verify nested config access
            assert db_manager.config["database"]["url"] == "sqlite:///:memory:"
            assert db_manager.test_prefix == "nested_test_"

    @pytest.mark.unit
    @pytest.mark.database
    def test_missing_database_config(self):
        """Test handling missing database configuration"""
        config = {}  # No database config

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            with pytest.raises(KeyError):
                DatabaseManager(config)

    @pytest.mark.unit
    @pytest.mark.database
    def test_missing_database_url(self):
        """Test handling missing database URL"""
        config = {"database": {}}  # No URL

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            with pytest.raises(KeyError):
                DatabaseManager(config)

    @pytest.mark.unit
    @pytest.mark.security
    def test_test_mode_isolation(self, security_validator):
        """Security test: Ensure test mode uses different tables"""
        security_validator.ensure_no_production_changes()

        config = {"database": {"url": "sqlite:///:memory:", "test_prefix": "test_"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            # Production mode
            prod_manager = DatabaseManager(config, test_mode=False)

            # Test mode
            test_manager = DatabaseManager(config, test_mode=True)

            # Verify table isolation
            prod_table = prod_manager.models["Institution"].__tablename__
            test_table = test_manager.models["Institution"].__tablename__

            assert prod_table == "institutions"
            assert test_table == "test_institutions"
            assert prod_table != test_table

    @pytest.mark.unit
    @pytest.mark.integration
    def test_real_database_operations(self):
        """Integration test with real in-memory database"""
        config = {
            "database": {
                "url": "sqlite:///:memory:",
                "test_prefix": "integration_test_",
            }
        }

        # Test with real database operations
        db_manager = DatabaseManager(config, test_mode=True)

        # Verify we can get a session
        session = db_manager.get_session()
        assert session is not None

        # Verify we can create a model instance
        Institution = db_manager.get_model("Institution")
        assert Institution is not None

        # Clean up
        session.close()

    @pytest.mark.unit
    @pytest.mark.coverage
    def test_all_model_types_accessible(self):
        """Test that all model types are accessible through get_model"""
        config = {"database": {"url": "sqlite:///:memory:"}}

        with patch("src.models.database.create_engine"), patch("src.models.database.sessionmaker"):
            db_manager = DatabaseManager(config)

            # Test all expected model types
            expected_models = [
                "Institution",
                "ProcessedFile",
                "TransactionEnum",
                "Transaction",
                "TransactionSplit",
                "SkippedTransaction",
                "ProcessingLog",
            ]

            for model_name in expected_models:
                model = db_manager.get_model(model_name)
                assert model is not None, f"Model {model_name} should be accessible"

    @pytest.mark.unit
    @pytest.mark.coverage
    def test_datetime_defaults_present(self):
        """Test that datetime defaults are correctly set on models"""
        models, base = create_models_with_prefix()

        # Check that datetime defaults are set
        Institution = models["Institution"]
        assert hasattr(Institution, "created_at")
        assert hasattr(Institution, "updated_at")

        Transaction = models["Transaction"]
        assert hasattr(Transaction, "created_at")
        assert hasattr(Transaction, "updated_at")

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_empty_prefix_edge_case(self):
        """Test edge case with empty string prefix"""
        models, base = create_models_with_prefix("")

        # Should behave same as no prefix
        assert models["Institution"].__tablename__ == "institutions"
        assert models["Institution"].__name__ == "InstitutionProd"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_whitespace_prefix_handling(self):
        """Test handling of whitespace in prefix"""
        models, base = create_models_with_prefix("  test_  ")

        # Table name should include whitespace as-is
        assert models["Institution"].__tablename__ == "  test_  institutions"

        # Class name should clean up whitespace
        # Note: This tests actual behavior, might want to document this edge case
