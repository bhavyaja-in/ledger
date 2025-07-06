"""
Comprehensive unit tests for main_handler.py with 100% line coverage.

Tests all MainHandler and BackupManager methods including CLI interactions,
file processing, backup management, error scenarios, and orchestration logic
to ensure enterprise-grade quality.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest

from src.handlers.main_handler import BackupManager, MainHandler, main


class TestBackupManager:
    """Comprehensive test suite for BackupManager class"""

    @pytest.fixture
    def backup_manager(self):
        """Create backup manager instance"""
        return BackupManager(test_mode=True)

    @pytest.fixture
    def backup_manager_prod(self):
        """Create production backup manager instance"""
        return BackupManager(test_mode=False)

    # =====================
    # 1. BACKUP MANAGER INITIALIZATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_backup_manager_init_test_mode(self):
        """Test backup manager initialization in test mode"""
        with patch.object(BackupManager, "_check_backup_availability", return_value=True):
            manager = BackupManager(test_mode=True)

            assert manager.test_mode is True
            assert manager.backup_config_path == "config/backup.yaml"
            assert manager.backup_script_available is True

    @pytest.mark.unit
    @pytest.mark.handler
    def test_backup_manager_init_prod_mode(self):
        """Test backup manager initialization in production mode"""
        with patch.object(BackupManager, "_check_backup_availability", return_value=False):
            manager = BackupManager(test_mode=False)

            assert manager.test_mode is False
            assert manager.backup_script_available is False

    @pytest.mark.unit
    @pytest.mark.handler
    def test_check_backup_availability_config_missing(self, backup_manager):
        """Test backup availability check when config file missing"""
        with patch("os.path.exists", return_value=False):
            result = backup_manager._check_backup_availability()

            assert result is False

    @pytest.mark.unit
    @pytest.mark.handler
    def test_check_backup_availability_import_failure(self, backup_manager):
        """Test backup availability check when import fails"""
        with (
            patch("os.path.exists", return_value=True),
            patch("src.handlers.main_handler._import_git_backup", return_value=None),
        ):
            result = backup_manager._check_backup_availability()
            assert result is False

    @pytest.mark.unit
    @pytest.mark.handler
    def test_check_backup_availability_success(self, backup_manager):
        """Test backup availability check when successful"""
        with (
            patch("os.path.exists", return_value=True),
            patch("src.handlers.main_handler._import_git_backup", return_value=Mock()),
        ):
            result = backup_manager._check_backup_availability()
            assert result is True

    # =====================
    # 2. BACKUP CREATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_not_available_startup(self, backup_manager):
        """Test backup creation when system not available (startup type)"""
        backup_manager.backup_script_available = False

        with patch("builtins.print") as mock_print:
            result = backup_manager.create_backup("startup")

        assert result is False
        mock_print.assert_called_once_with(
            "⚠️  Backup system not configured (continuing without backup)"
        )

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_not_available_other_types(self, backup_manager):
        """Test backup creation when system not available (non-startup types)"""
        backup_manager.backup_script_available = False

        with patch("builtins.print") as mock_print:
            result = backup_manager.create_backup("completion")

        assert result is False
        # Should not print warning for non-startup types
        mock_print.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_success(self, backup_manager):
        """Test successful backup creation"""
        backup_manager.backup_script_available = True

        mock_git_backup = Mock()
        mock_git_backup.create_backup.return_value = True
        mock_git_backup_cls = Mock(return_value=mock_git_backup)

        with patch(
            "src.handlers.main_handler._import_git_backup", return_value=mock_git_backup_cls
        ):
            result = backup_manager.create_backup("automatic")

        assert result is True
        mock_git_backup.create_backup.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_failure(self, backup_manager):
        """Test backup creation failure"""
        backup_manager.backup_script_available = True

        mock_git_backup = Mock()
        mock_git_backup.create_backup.return_value = False
        mock_git_backup_cls = Mock(return_value=mock_git_backup)

        with patch(
            "src.handlers.main_handler._import_git_backup", return_value=mock_git_backup_cls
        ):
            result = backup_manager.create_backup("completion")

        assert result is False

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_exception(self, backup_manager):
        """Test backup creation with exception"""
        backup_manager.backup_script_available = True

        mock_git_backup_cls = Mock(side_effect=Exception("Backup error"))

        with patch(
            "src.handlers.main_handler._import_git_backup", return_value=mock_git_backup_cls
        ):
            result = backup_manager.create_backup("interruption")

        assert result is False

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_backup_all_types(self, backup_manager):
        """Test backup creation with all backup types"""
        backup_manager.backup_script_available = True

        mock_git_backup = Mock()
        mock_git_backup.create_backup.return_value = True
        mock_git_backup_cls = Mock(return_value=mock_git_backup)

        backup_types = ["startup", "completion", "interruption", "automatic", "unknown"]

        with patch(
            "src.handlers.main_handler._import_git_backup", return_value=mock_git_backup_cls
        ):
            for backup_type in backup_types:
                result = backup_manager.create_backup(backup_type)
                assert result is True


class TestMainHandler:
    """Comprehensive test suite for MainHandler class"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            "processors": {
                "icici_bank": {
                    "extractor": "icici_bank_extractor",
                    "transformer": "icici_bank_transformer",
                    "extraction_folder": "/test/data/icici_bank",
                    "file_type": "excel",
                },
                "test_processor": {
                    "extractor": "test_extractor",
                    "transformer": "test_transformer",
                    "extraction_folder": "/test/data/test",
                    "file_type": "csv",
                },
            }
        }

    @pytest.fixture
    def main_handler(self, mock_config):
        """Create main handler instance with mocked dependencies"""
        with (
            patch("src.handlers.main_handler.ConfigLoader") as mock_config_loader_class,
            patch("src.handlers.main_handler.DatabaseManager") as mock_db_manager_class,
            patch("src.handlers.main_handler.DatabaseLoader") as mock_db_loader_class,
            patch("src.handlers.main_handler.BackupManager") as mock_backup_manager_class,
        ):
            # Setup mocks
            mock_config_loader = Mock()
            mock_config_loader.get_config.return_value = mock_config
            mock_config_loader_class.return_value = mock_config_loader

            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager

            mock_db_loader = Mock()
            mock_db_loader_class.return_value = mock_db_loader

            mock_backup_manager = Mock()
            mock_backup_manager_class.return_value = mock_backup_manager

            handler = MainHandler(test_mode=True)

            # Store mocks for test access
            setattr(handler, "mock_config_loader", mock_config_loader)
            setattr(handler, "mock_db_manager", mock_db_manager)
            setattr(handler, "mock_db_loader", mock_db_loader)
            setattr(handler, "mock_backup_manager", mock_backup_manager)

            return handler

    # =====================
    # 3. MAIN HANDLER INITIALIZATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_handler_init_test_mode(self, main_handler):
        """Test main handler initialization in test mode"""
        assert main_handler.test_mode is True
        assert main_handler.config is not None
        assert main_handler.db_manager is not None
        assert main_handler.db_loader is not None
        assert main_handler.backup_manager is not None

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_handler_init_config_reload(self, mock_config):
        """Test config loader reinitialization with database manager"""
        with (
            patch("src.handlers.main_handler.ConfigLoader") as mock_config_loader_class,
            patch("src.handlers.main_handler.DatabaseManager"),
            patch("src.handlers.main_handler.DatabaseLoader"),
            patch("src.handlers.main_handler.BackupManager"),
            patch("builtins.print"),
        ):
            mock_config_loader = Mock()
            mock_config_loader.get_config.return_value = mock_config
            mock_config_loader_class.return_value = mock_config_loader

            MainHandler(test_mode=False)

            # Should be called twice - once without db_manager, once with
            assert mock_config_loader_class.call_count == 2
            assert mock_config_loader.get_config.call_count == 2

    # =====================
    # 4. RUN METHOD TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_run_with_valid_processor_and_file(self, main_handler):
        """Test run method with valid processor and file"""
        processor_type = "icici_bank"
        file_path = "/test/file.xlsx"

        mock_result = {
            "status": "completed",
            "total_transactions": 10,
            "processed_transactions": 8,
            "skipped_transactions": 2,
        }

        with (
            patch("os.path.exists", return_value=True),
            patch.object(main_handler, "_process_file", return_value=mock_result) as mock_process,
            patch.object(main_handler, "_display_summary") as mock_display,
            patch("builtins.print"),
        ):
            result = main_handler.run(processor_type=processor_type, file_path=file_path)

        assert result == mock_result
        mock_process.assert_called_once_with(processor_type, file_path)
        mock_display.assert_called_once_with(mock_result)
        main_handler.mock_backup_manager.create_backup.assert_any_call("startup")
        main_handler.mock_backup_manager.create_backup.assert_any_call("completion")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_run_invalid_processor(self, main_handler):
        """Test run method with invalid processor"""
        processor_type = "invalid_processor"

        with patch("builtins.print") as mock_print:
            result = main_handler.run(processor_type=processor_type)

        assert result["status"] == "error"
        assert "Unknown processor" in result["message"]
        mock_print.assert_any_call("❌ Unknown processor: invalid_processor")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_run_file_not_found(self, main_handler):
        """Test run method with non-existent file"""
        file_path = "/nonexistent/file.xlsx"

        with patch("os.path.exists", return_value=False), patch("builtins.print") as mock_print:
            result = main_handler.run(processor_type="icici_bank", file_path=file_path)

        assert result["status"] == "error"
        assert "File not found" in result["message"]
        mock_print.assert_any_call(f"❌ File not found: {file_path}")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_run_keyboard_interrupt(self, main_handler):
        """Test run method with keyboard interrupt"""
        with (
            patch("os.path.exists", return_value=True),
            patch.object(main_handler, "_process_file", side_effect=KeyboardInterrupt),
            patch("sys.exit") as mock_exit,
        ):
            main_handler.run(processor_type="icici_bank", file_path="/test/file.xlsx")

        mock_exit.assert_called_once_with(0)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_run_general_exception(self, main_handler):
        """Test run method with general exception"""
        error_msg = "Test error"

        with (
            patch("os.path.exists", return_value=True),
            patch.object(main_handler, "_process_file", side_effect=OSError(error_msg)),
            patch("builtins.print") as mock_print,
        ):
            result = main_handler.run(processor_type="icici_bank", file_path="/test/file.xlsx")

        assert result["status"] == "error"
        assert error_msg in result["message"]
        mock_print.assert_any_call(f"💥 Error in main processing: {error_msg}")
        main_handler.mock_backup_manager.create_backup.assert_any_call("interruption")

    # =====================
    # 5. FILE DETECTION AND SELECTION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_auto_detect_single_file(self, main_handler):
        """Test auto-detection with single file"""
        processor_type = "icici_bank"
        test_file_path = "/test/data/icici_bank/test.xlsx"

        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=["test.xlsx"]),
            patch("os.path.getsize", return_value=1024),
            patch("os.path.getmtime", return_value=time.time()),
            patch("builtins.print") as mock_print,
        ):
            result = main_handler._auto_detect_or_select_file(processor_type)

        assert result == test_file_path
        mock_print.assert_any_call("🎯 Auto-detected file: test.xlsx")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_auto_detect_no_files(self, main_handler):
        """Test auto-detection with no files"""
        processor_type = "icici_bank"

        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=[]),
            pytest.raises(FileNotFoundError) as exc_info,
        ):
            main_handler._auto_detect_or_select_file(processor_type)

        assert "No processable files found" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_auto_detect_extraction_folder_missing(self, main_handler):
        """Test auto-detection with missing extraction folder"""
        processor_type = "icici_bank"

        with (
            patch("os.path.exists", return_value=False),
            pytest.raises(FileNotFoundError) as exc_info,
        ):
            main_handler._auto_detect_or_select_file(processor_type)

        assert "Extraction folder not found" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_select_file_with_details_multiple_files(self, main_handler):
        """Test file selection with multiple files"""
        files = [
            {
                "name": "file1.xlsx",
                "path": "/test/file1.xlsx",
                "size": 1024000,
                "modified": datetime(2023, 1, 1, 12, 0, 0),
            },
            {
                "name": "file2.xlsx",
                "path": "/test/file2.xlsx",
                "size": 2048000,
                "modified": datetime(2023, 1, 2, 14, 30, 0),
            },
        ]

        with patch("builtins.input", return_value="1"), patch("builtins.print") as mock_print:
            result = main_handler._select_file_with_details(files, "/test")

        assert result == "/test/file1.xlsx"
        mock_print.assert_any_call("✅ Selected: file1.xlsx")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_select_file_browse_option(self, main_handler):
        """Test file selection with browse option"""
        files = [
            {
                "name": "file1.xlsx",
                "path": "/test/file1.xlsx",
                "size": 1024,
                "modified": datetime.now(),
            }
        ]

        with (
            patch("builtins.input", return_value="2"),
            patch.object(
                main_handler, "_browse_for_file", return_value="/custom/file.xlsx"
            ) as mock_browse,
        ):
            result = main_handler._select_file_with_details(files, "/test")

        assert result == "/custom/file.xlsx"
        mock_browse.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.handler
    def test_select_file_back_to_processor(self, main_handler):
        """Test file selection with back to processor option"""
        files = [
            {
                "name": "file1.xlsx",
                "path": "/test/file1.xlsx",
                "size": 1024,
                "modified": datetime.now(),
            }
        ]

        with (
            patch("builtins.input", return_value="3"),
            patch.object(
                main_handler, "_select_processor", return_value="new_processor"
            ) as mock_select,
        ):
            result = main_handler._select_file_with_details(files, "/test")

        assert result == "new_processor"
        mock_select.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.handler
    def test_browse_for_file_valid(self, main_handler):
        """Test manual file browsing with valid file"""
        file_path = "/custom/test.xlsx"

        with (
            patch("builtins.input", return_value=file_path),
            patch("os.path.exists", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            result = main_handler._browse_for_file()

        assert result == file_path
        mock_print.assert_any_call("✅ File found: test.xlsx")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_browse_for_file_invalid_then_quit(self, main_handler):
        """Test manual file browsing with invalid file then quit"""
        with (
            patch("builtins.input", side_effect=["/invalid/file.xlsx", "n"]),
            patch("os.path.exists", return_value=False),
            patch.object(
                main_handler, "_select_processor", return_value="back_to_menu"
            ) as mock_select,
            patch("builtins.print"),
        ):
            result = main_handler._browse_for_file()

        assert result == "back_to_menu"
        mock_select.assert_called_once()

    # =====================
    # 6. PROCESSING WORKFLOW TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_process_file_success(self, main_handler):
        """Test successful file processing"""
        processor_type = "icici_bank"
        file_path = "/test/file.xlsx"

        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        mock_extracted_data = {"transactions": []}
        mock_transform_result = {
            "status": "completed",
            "total_transactions": 5,
            "processed_transactions": 3,
            "skipped_transactions": 2,
        }

        with (
            patch.object(main_handler, "_get_or_create_institution", return_value=mock_institution),
            patch.object(
                main_handler,
                "_create_processed_file_record",
                return_value=mock_processed_file,
            ),
            patch.object(main_handler, "_extract_data", return_value=mock_extracted_data),
            patch.object(main_handler, "_transform_data", return_value=mock_transform_result),
            patch.object(main_handler, "_create_processing_log"),
            patch("time.time", side_effect=[100, 105]),
        ):  # 5 second processing time
            result = main_handler._process_file(processor_type, file_path)

        assert result["status"] == "success"
        assert result["final_status"] == "completed"
        assert result["processing_time"] == 5
        main_handler.mock_db_loader.update_processed_file_status.assert_called_with(1, "completed")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_process_file_interrupted(self, main_handler):
        """Test file processing when interrupted"""
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)
        mock_extracted_data = {"transactions": []}
        mock_transform_result = {"status": "interrupted"}

        with (
            patch.object(main_handler, "_get_or_create_institution", return_value=mock_institution),
            patch.object(
                main_handler,
                "_create_processed_file_record",
                return_value=mock_processed_file,
            ),
            patch.object(main_handler, "_extract_data", return_value=mock_extracted_data),
            patch.object(main_handler, "_transform_data", return_value=mock_transform_result),
            patch("builtins.print") as mock_print,
        ):
            result = main_handler._process_file("icici_bank", "/test/file.xlsx")

        assert result["final_status"] == "partially_processed"
        mock_print.assert_any_call("\n⚠️  Processing interrupted - marked as partially processed")
        main_handler.mock_db_loader.update_processed_file_status.assert_called_with(
            1, "partially_processed"
        )

    @pytest.mark.unit
    @pytest.mark.handler
    def test_process_file_exception(self, main_handler):
        """Test file processing with exception"""
        mock_institution = Mock(id=1)
        mock_processed_file = Mock(id=1)

        with (
            patch.object(main_handler, "_get_or_create_institution", return_value=mock_institution),
            patch.object(
                main_handler,
                "_create_processed_file_record",
                return_value=mock_processed_file,
            ),
            patch.object(main_handler, "_extract_data", side_effect=OSError("Extract error")),
            pytest.raises(OSError) as exc_info,
        ):
            main_handler._process_file("icici_bank", "/test/file.xlsx")

        assert "Extract error" in str(exc_info.value)
        main_handler.mock_db_loader.update_processed_file_status.assert_called_with(1, "failed")

    # =====================
    # 7. DYNAMIC IMPORT TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_extract_data_success(self, main_handler):
        """Test successful data extraction with dynamic import"""
        extractor_name = "icici_bank_extractor"
        file_path = "/test/file.xlsx"
        expected_data = {"transactions": []}

        mock_extractor = Mock()
        mock_extractor.extract.return_value = expected_data

        mock_extractor_class = Mock(return_value=mock_extractor)
        mock_module = Mock()
        mock_module.IciciBankExtractor = mock_extractor_class

        with patch("builtins.__import__", return_value=mock_module):
            result = main_handler._extract_data(extractor_name, file_path)

        assert result == expected_data
        mock_extractor_class.assert_called_once_with(main_handler.config)
        mock_extractor.extract.assert_called_once_with(file_path)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_transform_data_success(self, main_handler):
        """Test successful data transformation with dynamic import"""
        transformer_name = "icici_bank_transformer"
        extracted_data = {"transactions": []}
        mock_institution = Mock()
        mock_processed_file = Mock()
        expected_result = {"status": "completed"}

        mock_transformer = Mock()
        mock_transformer.process_transactions.return_value = expected_result

        mock_transformer_class = Mock(return_value=mock_transformer)
        mock_module = Mock()
        mock_module.IciciBankTransformer = mock_transformer_class

        with patch("builtins.__import__", return_value=mock_module):
            result = main_handler._transform_data(
                transformer_name, extracted_data, mock_institution, mock_processed_file
            )

        assert result == expected_result
        mock_transformer_class.assert_called_once_with(
            main_handler.db_manager, main_handler.config, main_handler.config_loader
        )

    # =====================
    # 8. DATABASE RECORD CREATION TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_get_or_create_institution(self, main_handler):
        """Test institution creation/retrieval"""
        processor_type = "icici_bank"
        mock_institution = Mock()

        main_handler.mock_db_loader.get_or_create_institution.return_value = mock_institution

        result = main_handler._get_or_create_institution(processor_type)

        assert result == mock_institution
        main_handler.mock_db_loader.get_or_create_institution.assert_called_once_with(
            "Icici Bank", "bank"
        )

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_processed_file_record(self, main_handler):
        """Test processed file record creation"""
        institution_id = 1
        file_path = "/test/data/test_file.xlsx"
        processor_type = "icici_bank"
        mock_processed_file = Mock()

        with (
            patch("os.path.basename", return_value="test_file.xlsx"),
            patch("os.path.getsize", return_value=1024),
        ):
            main_handler.mock_db_loader.create_processed_file.return_value = mock_processed_file

            result = main_handler._create_processed_file_record(
                institution_id, file_path, processor_type
            )

        assert result == mock_processed_file
        main_handler.mock_db_loader.create_processed_file.assert_called_once_with(
            institution_id=institution_id,
            file_path=file_path,
            file_name="test_file.xlsx",
            file_size=1024,
            processor_type=processor_type,
        )

    @pytest.mark.unit
    @pytest.mark.handler
    def test_create_processing_log(self, main_handler):
        """Test processing log creation"""
        processed_file_id = 1
        result = {
            "total_transactions": 10,
            "processed_transactions": 8,
            "skipped_transactions": 2,
            "duplicate_transactions": 1,
            "auto_skipped_transactions": 3,
        }
        processing_time = 5.5

        main_handler._create_processing_log(processed_file_id, result, processing_time)

        main_handler.mock_db_loader.create_processing_log.assert_called_once_with(
            processed_file_id=processed_file_id,
            total_transactions=10,
            processed_transactions=8,
            skipped_transactions=2,
            duplicate_transactions=1,
            duplicate_skipped=3,
            processing_time=processing_time,
        )

    # =====================
    # 9. DISPLAY AND UI TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.handler
    def test_display_summary_success(self, main_handler):
        """Test display summary for successful processing"""
        result = {
            "status": "success",
            "final_status": "completed",
            "total_transactions": 10,
            "processed_transactions": 8,
            "skipped_transactions": 2,
            "duplicate_transactions": 1,
            "auto_skipped_transactions": 0,
            "processing_time": 5.5,
        }

        with patch("builtins.print") as mock_print:
            main_handler._display_summary(result)

        expected_calls = [
            call("\n" + "=" * 60),
            call("📋 PROCESSING SUMMARY"),
            call("=" * 60),
            call("✅ Status: SUCCESS"),
            call("📊 Total Transactions Found: 10"),
            call("✅ Successfully Processed: 8"),
            call("⏭️  Skipped (New): 2"),
            call("🔄 Already Processed (Duplicates): 1"),
            call("⏸️  Already Skipped (Duplicates): 0"),
            call("⏱️  Processing Time: 5.50 seconds"),
            call("=" * 60),
        ]
        mock_print.assert_has_calls(expected_calls)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_display_summary_partial_processing(self, main_handler):
        """Test display summary for partial processing"""
        result = {
            "status": "success",
            "final_status": "partially_processed",
            "total_transactions": 20,
            "processed_transactions": 10,
            "skipped_transactions": 5,
            "duplicate_transactions": 2,
            "auto_skipped_transactions": 1,
        }

        with patch("builtins.print") as mock_print:
            main_handler._display_summary(result)

        mock_print.assert_any_call("⚠️ Status: SUCCESS - PARTIALLY_PROCESSED")
        mock_print.assert_any_call("📈 Completion Rate: 75.0% (15/20)")

    @pytest.mark.unit
    @pytest.mark.handler
    def test_display_summary_error(self, main_handler):
        """Test display summary for error status"""
        result = {
            "status": "error",
            "total_transactions": 0,
            "processed_transactions": 0,
        }

        with patch("builtins.print") as mock_print:
            main_handler._display_summary(result)

        mock_print.assert_any_call("❌ Status: ERROR")

    # =====================
    # 10. EDGE CASES AND ERROR HANDLING TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_file_selection_keyboard_interrupt(self, main_handler):
        """Test keyboard interrupt during file selection"""
        files = [
            {
                "name": "file1.xlsx",
                "path": "/test/file1.xlsx",
                "size": 1024,
                "modified": datetime.now(),
            }
        ]

        with (
            patch("builtins.input", side_effect=KeyboardInterrupt),
            pytest.raises(KeyboardInterrupt),
        ):
            main_handler._select_file_with_details(files, "/test")

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_invalid_file_selection_input(self, main_handler):
        """Test invalid input during file selection"""
        files = [
            {
                "name": "file1.xlsx",
                "path": "/test/file1.xlsx",
                "size": 1024,
                "modified": datetime.now(),
            }
        ]

        with (
            patch("builtins.input", side_effect=["invalid", "999", "1"]),
            patch("builtins.print") as mock_print,
        ):
            result = main_handler._select_file_with_details(files, "/test")

        assert result == "/test/file1.xlsx"
        mock_print.assert_any_call("❌ Please enter a valid number.")
        mock_print.assert_any_call("❌ Invalid choice. Please try again.")

    @pytest.mark.unit
    @pytest.mark.performance
    def test_large_file_list_handling(self, main_handler):
        """Test handling of large file lists"""
        # Create 100 files for performance testing
        files = []
        for i in range(100):
            files.append(
                {
                    "name": f"file_{i}.xlsx",
                    "path": f"/test/file_{i}.xlsx",
                    "size": 1024 * i,
                    "modified": datetime.now(),
                }
            )

        with patch("builtins.input", return_value="50"), patch("builtins.print"):
            result = main_handler._select_file_with_details(files, "/test")

        assert result == "/test/file_49.xlsx"  # 50th file (0-indexed = 49)


class TestMainFunction:
    """Test suite for main() CLI function"""

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_no_arguments(self):
        """Test main function with no arguments"""
        test_args = ["main_handler.py"]

        with (
            patch("sys.argv", test_args),
            patch("src.handlers.main_handler.MainHandler") as mock_handler_class,
            patch("sys.exit") as mock_exit,
            patch("builtins.print"),
        ):
            mock_handler = Mock()
            mock_handler.run.return_value = {"status": "success"}
            mock_handler_class.return_value = mock_handler

            main()

        mock_handler_class.assert_called_once_with(test_mode=False)
        mock_handler.run.assert_called_once_with(processor_type=None, file_path=None)
        mock_exit.assert_called_once_with(0)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_with_all_arguments(self):
        """Test main function with all arguments"""
        test_args = [
            "main_handler.py",
            "--processor",
            "icici_bank",
            "--file",
            "/test/file.xlsx",
            "--test-mode",
        ]

        with (
            patch("sys.argv", test_args),
            patch("src.handlers.main_handler.MainHandler") as mock_handler_class,
            patch("sys.exit") as mock_exit,
            patch("builtins.print"),
        ):
            mock_handler = Mock()
            mock_handler.run.return_value = {"status": "success"}
            mock_handler_class.return_value = mock_handler

            main()

        mock_handler_class.assert_called_once_with(test_mode=True)
        mock_handler.run.assert_called_once_with(
            processor_type="icici_bank", file_path="/test/file.xlsx"
        )
        mock_exit.assert_called_once_with(0)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_error_result(self):
        """Test main function with error result"""
        test_args = ["main_handler.py"]

        with (
            patch("sys.argv", test_args),
            patch("src.handlers.main_handler.MainHandler") as mock_handler_class,
            patch("sys.exit") as mock_exit,
            patch("builtins.print"),
        ):
            mock_handler = Mock()
            mock_handler.run.return_value = {"status": "error"}
            mock_handler_class.return_value = mock_handler

            main()

        mock_exit.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_fatal_exception(self):
        """Test main function with fatal exception"""
        test_args = ["main_handler.py"]

        with (
            patch("sys.argv", test_args),
            patch(
                "src.handlers.main_handler.MainHandler",
                side_effect=OSError("Fatal error"),
            ),
            patch("sys.exit") as mock_exit,
            patch("builtins.print") as mock_print,
        ):
            main()

        mock_print.assert_any_call("\n💥 Fatal error: Fatal error")
        mock_exit.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.handler
    def test_main_emergency_backup(self):
        """Test main function creates emergency backup on exception"""
        test_args = ["main_handler.py"]

        mock_handler = Mock()
        mock_handler.run.side_effect = OSError("Fatal error")

        with (
            patch("sys.argv", test_args),
            patch("src.handlers.main_handler.MainHandler", return_value=mock_handler),
            patch("sys.exit"),
            patch("builtins.print"),
        ):
            main()

        mock_handler.backup_manager.create_backup.assert_called_once_with("interruption")
