"""
Main Handler - Enterprise Financial Data Processor
Handles processor selection and orchestrates the entire processing flow
"""

import argparse
import glob
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.loaders.database_loader import DatabaseLoader
from src.models.database import DatabaseManager
from src.utils.config_loader import ConfigLoader


class BackupManager:
    """Manages automatic database backups during processing"""

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.backup_config_path = "config/backup.yaml"
        self.backup_script_available = self._check_backup_availability()

    def _check_backup_availability(self) -> bool:
        """Check if backup system is properly configured"""
        try:
            # Check if backup configuration exists
            if not os.path.exists(self.backup_config_path):
                return False

            # Try to import the backup functionality
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
            from scripts.git_backup import GitDatabaseBackup

            return True
        except Exception:
            return False

    def create_backup(self, backup_type="automatic") -> bool:
        """Create database backup with error handling"""
        if not self.backup_script_available:
            if backup_type == "startup":
                print("⚠️  Backup system not configured (continuing without backup)")
            return False

        try:
            from scripts.git_backup import GitDatabaseBackup

            # Create backup manager
            git_backup = GitDatabaseBackup(config_path=self.backup_config_path)

            # Create backup
            backup_type_emoji = {
                "startup": "🚀",
                "completion": "✅",
                "interruption": "⚠️",
                "automatic": "💾",
            }

            emoji = backup_type_emoji.get(backup_type, "💾")
            print(f"{emoji} Creating {backup_type} backup...")

            success = git_backup.create_backup()

            if success:
                print(f"✅ {backup_type.title()} backup completed successfully")
            else:
                print(f"⚠️  {backup_type.title()} backup failed")

            return success

        except Exception as e:
            print(f"⚠️  Backup error: {e}")
            return False


class MainHandler:
    """Main handler for financial data processing"""

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        # First load config without database manager
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_config()
        self.db_manager = DatabaseManager(self.config, test_mode=test_mode)
        self.db_loader = DatabaseLoader(self.db_manager)

        # Now re-initialize config loader with database manager for dynamic category loading
        self.config_loader = ConfigLoader(db_manager=self.db_manager)
        self.config = self.config_loader.get_config()

        # Initialize backup manager
        self.backup_manager = BackupManager(test_mode=test_mode)

        mode = "TEST" if test_mode else "PRODUCTION"
        print(f"🚀 Financial Data Processor initialized in {mode} mode")

    def run(self, processor_type=None, file_path=None):
        """Main execution flow with automatic backups"""
        try:
            # Step 0: Create startup backup
            print("\n" + "=" * 50)
            print("💾 BACKUP SYSTEM")
            print("=" * 50)
            self.backup_manager.create_backup("startup")
            print()

            # Step 1: Get processor type
            if not processor_type:
                processor_type = self._select_processor()
            else:
                # Validate provided processor
                if processor_type not in self.config["processors"]:
                    print(f"❌ Unknown processor: {processor_type}")
                    print(f"📋 Available processors: {', '.join(self.config['processors'].keys())}")
                    return {
                        "status": "error",
                        "message": f"Unknown processor: {processor_type}",
                    }
                print(f"✅ Using processor: {processor_type}")

            # Step 2: Get file path (auto-detect or user selection)
            if not file_path:
                file_path = self._auto_detect_or_select_file(processor_type)
            else:
                # Validate provided file
                if not os.path.exists(file_path):
                    print(f"❌ File not found: {file_path}")
                    return {
                        "status": "error",
                        "message": f"File not found: {file_path}",
                    }
                print(f"✅ Using file: {os.path.basename(file_path)}")

            # Step 3: Process file
            result = self._process_file(processor_type, file_path)

            # Step 4: Display summary
            self._display_summary(result)

            # Step 5: Create completion backup
            print("\n" + "=" * 50)
            print("💾 COMPLETION BACKUP")
            print("=" * 50)
            self.backup_manager.create_backup("completion")

            return result

        except KeyboardInterrupt:
            print("\n🛑 Processing interrupted by user...")
            print("\n" + "=" * 50)
            print("💾 INTERRUPTION BACKUP")
            print("=" * 50)
            self.backup_manager.create_backup("interruption")
            print("👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"💥 Error in main processing: {e}")
            # Create backup even on error
            print("\n🔄 Creating backup before exit...")
            self.backup_manager.create_backup("interruption")
            return {"status": "error", "message": str(e)}

    def _select_processor(self) -> str:
        """Interactive processor selection with intelligent menu"""
        processors = list(self.config["processors"].keys())

        print("\n" + "=" * 50)
        print("📊 FINANCIAL DATA PROCESSOR")
        print("=" * 50)
        print("🏦 Available processors:")

        for i, processor in enumerate(processors, 1):
            # Make processor names more readable
            display_name = processor.replace("_", " ").title()
            print(f"  {i}. {display_name}")

        print(f"  {len(processors) + 1}. Exit")

        while True:
            try:
                print("\n💡 Tip: You can also pass --processor <name> as argument")
                choice = input(f"🔢 Select processor (1-{len(processors) + 1}): ").strip()

                if choice == str(len(processors) + 1):
                    print("👋 Goodbye!")
                    sys.exit(0)

                idx = int(choice) - 1
                if 0 <= idx < len(processors):
                    selected = processors[idx]
                    print(f"✅ Selected: {selected.replace('_', ' ').title()}")
                    return selected
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                # Signal handler will take care of this
                raise

    def _auto_detect_or_select_file(self, processor_type: str) -> str:
        """Auto-detect file or provide selection menu"""
        processor_config = self.config["processors"][processor_type]
        extraction_folder = processor_config["extraction_folder"]

        if not os.path.exists(extraction_folder):
            raise FileNotFoundError(f"📁 Extraction folder not found: {extraction_folder}")

        # Get supported file extensions
        file_extensions = {"excel": [".xls", ".xlsx"], "csv": [".csv"], "pdf": [".pdf"]}

        processor_file_type = processor_config.get("file_type", "excel")
        supported_extensions = file_extensions.get(processor_file_type, [".xls", ".xlsx", ".csv"])

        # Find all supported files
        files = []
        for file in os.listdir(extraction_folder):
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(extraction_folder, file)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                files.append(
                    {
                        "name": file,
                        "path": file_path,
                        "size": file_size,
                        "modified": file_modified,
                    }
                )

        if not files:
            raise FileNotFoundError(f"📂 No processable files found in {extraction_folder}")

        # Sort by modification date (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

        # Auto-detect: if only one file, use it automatically
        if len(files) == 1:
            print(f"🎯 Auto-detected file: {files[0]['name']}")
            return files[0]["path"]

        # Multiple files: show intelligent selection menu
        return self._select_file_with_details(files, extraction_folder)

    def _select_file_with_details(self, files: List[Dict], extraction_folder: str) -> str:
        """Show file selection menu with details"""
        print(f"\n📁 Files in {extraction_folder}:")
        print("-" * 80)

        for i, file_info in enumerate(files, 1):
            size_mb = file_info["size"] / (1024 * 1024)
            modified_str = file_info["modified"].strftime("%Y-%m-%d %H:%M")

            print(f"  {i}. {file_info['name']}")
            print(f"     📦 Size: {size_mb:.1f} MB | 📅 Modified: {modified_str}")
            if i < len(files):
                print()

        print(f"  {len(files) + 1}. Browse for different file")
        print(f"  {len(files) + 2}. Back to processor selection")

        while True:
            try:
                choice = input(f"\n🔢 Select file (1-{len(files) + 2}): ").strip()

                if choice == str(len(files) + 2):
                    return self._select_processor()
                elif choice == str(len(files) + 1):
                    return self._browse_for_file()

                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    selected_file = files[idx]["path"]
                    print(f"✅ Selected: {files[idx]['name']}")
                    return selected_file
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                # Signal handler will take care of this
                raise

    def _browse_for_file(self) -> str:
        """Allow user to manually enter file path"""
        while True:
            try:
                file_path = input("\n📎 Enter full file path: ").strip()
                if os.path.exists(file_path):
                    print(f"✅ File found: {os.path.basename(file_path)}")
                    return file_path
                else:
                    print("❌ File not found. Please try again.")
                    retry = input("🔄 Try again? (y/n): ").strip().lower()
                    if retry != "y":
                        print("🔙 Returning to file selection...")
                        return self._select_processor()
            except KeyboardInterrupt:
                # Signal handler will take care of this
                raise

    def _process_file(self, processor_type: str, file_path: str) -> Dict[str, Any]:
        """Process file using specified processor"""
        print(f"\n⚡ Processing file with {processor_type.replace('_', ' ').title()}...")
        start_time = time.time()

        # Get processor configuration
        processor_config = self.config["processors"][processor_type]
        extractor_name = processor_config["extractor"]
        transformer_name = processor_config["transformer"]

        # Step 1: Create/get institution
        institution = self._get_or_create_institution(processor_type)

        # Step 2: Create processed file record
        processed_file = self._create_processed_file_record(
            institution.id, file_path, processor_type
        )

        try:
            # Step 3: Extract data using configured extractor
            print("📊 Extracting data...")
            extracted_data = self._extract_data(extractor_name, file_path)

            # Step 4: Transform data using configured transformer
            print("🔄 Processing transactions...")
            result = self._transform_data(
                transformer_name, extracted_data, institution, processed_file
            )

            # Step 5: Update processing status based on result
            processing_time = time.time() - start_time

            if result.get("status") == "interrupted":
                # User interrupted - mark as partially processed
                self.db_loader.update_processed_file_status(
                    processed_file.id, "partially_processed"
                )
                result["final_status"] = "partially_processed"
                print("\n⚠️  Processing interrupted - marked as partially processed")
            elif result.get("status") == "completed":
                # Completed successfully
                self.db_loader.update_processed_file_status(processed_file.id, "completed")
                result["final_status"] = "completed"
            elif result.get("status") == "partially_completed":
                # Some transactions processed but not all
                self.db_loader.update_processed_file_status(
                    processed_file.id, "partially_processed"
                )
                result["final_status"] = "partially_processed"
            else:
                # Default to completed if status unclear
                self.db_loader.update_processed_file_status(processed_file.id, "completed")
                result["final_status"] = "completed"

            # Step 6: Create processing log (even for partial processing)
            self._create_processing_log(processed_file.id, result, processing_time)

            result["status"] = "success"
            result["processed_file_id"] = processed_file.id
            result["processing_time"] = processing_time

        except Exception as e:
            # Update status to failed
            self.db_loader.update_processed_file_status(processed_file.id, "failed")
            raise e

        return result

    def _extract_data(self, extractor_name: str, file_path: str) -> Dict[str, Any]:
        """Extract data using specified extractor"""
        # Dynamic import of extractor
        module_path = f"src.extractors.channel_based_extractors.{extractor_name}"
        module = __import__(module_path, fromlist=[extractor_name])

        # Get extractor class (convert snake_case to CamelCase)
        class_name = "".join(word.capitalize() for word in extractor_name.split("_"))
        extractor_class = getattr(module, class_name)

        # Create and use extractor
        extractor = extractor_class(self.config)
        return extractor.extract(file_path)

    def _transform_data(
        self,
        transformer_name: str,
        extracted_data: Dict[str, Any],
        institution,
        processed_file,
    ) -> Dict[str, Any]:
        """Transform data using specified transformer"""
        # Dynamic import of transformer
        module_path = f"src.transformers.{transformer_name}"
        module = __import__(module_path, fromlist=[transformer_name])

        # Get transformer class (convert snake_case to CamelCase)
        class_name = "".join(word.capitalize() for word in transformer_name.split("_"))
        transformer_class = getattr(module, class_name)

        # Create and use transformer
        transformer = transformer_class(self.db_manager, self.config, self.config_loader)
        return transformer.process_transactions(extracted_data, institution, processed_file)

    def _get_or_create_institution(self, processor_type: str):
        """Get or create institution record"""
        institution_name = processor_type.replace("_", " ").title()
        return self.db_loader.get_or_create_institution(institution_name, "bank")

    def _create_processed_file_record(
        self, institution_id: int, file_path: str, processor_type: str
    ):
        """Create processed file record"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        return self.db_loader.create_processed_file(
            institution_id=institution_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            processor_type=processor_type,
        )

    def _create_processing_log(
        self, processed_file_id: int, result: Dict[str, Any], processing_time: float
    ):
        """Create processing log"""
        self.db_loader.create_processing_log(
            processed_file_id=processed_file_id,
            total_transactions=result.get("total_transactions", 0),
            processed_transactions=result.get("processed_transactions", 0),
            skipped_transactions=result.get("skipped_transactions", 0),
            duplicate_transactions=result.get("duplicate_transactions", 0),
            duplicate_skipped=result.get("auto_skipped_transactions", 0),
            processing_time=processing_time,
        )

    def _display_summary(self, result: Dict[str, Any]):
        """Display processing summary with better formatting"""
        print("\n" + "=" * 60)
        print("📋 PROCESSING SUMMARY")
        print("=" * 60)

        status = result.get("status", "unknown").upper()
        final_status = result.get("final_status", "").upper()

        # Show appropriate status emoji and message
        if status == "SUCCESS":
            if final_status == "PARTIALLY_PROCESSED":
                status_emoji = "⚠️"
                status_msg = f"{status} - {final_status}"
            else:
                status_emoji = "✅"
                status_msg = status
        else:
            status_emoji = "❌"
            status_msg = status

        print(f"{status_emoji} Status: {status_msg}")

        print(f"📊 Total Transactions Found: {result.get('total_transactions', 0)}")
        print(f"✅ Successfully Processed: {result.get('processed_transactions', 0)}")
        print(f"⏭️  Skipped (New): {result.get('skipped_transactions', 0)}")
        print(f"🔄 Already Processed (Duplicates): {result.get('duplicate_transactions', 0)}")
        print(f"⏸️  Already Skipped (Duplicates): {result.get('auto_skipped_transactions', 0)}")

        # Show completion percentage for partial processing
        total_found = result.get("total_transactions", 0)
        processed_or_skipped = result.get("processed_transactions", 0) + result.get(
            "skipped_transactions", 0
        )
        if total_found > 0 and final_status == "PARTIALLY_PROCESSED":
            completion_pct = (processed_or_skipped / total_found) * 100
            print(
                f"📈 Completion Rate: {completion_pct:.1f}% ({processed_or_skipped}/{total_found})"
            )

        if "processing_time" in result:
            print(f"⏱️  Processing Time: {result['processing_time']:.2f} seconds")

        print("=" * 60)


def main():
    """CLI entry point with enhanced argument parsing"""
    parser = argparse.ArgumentParser(
        description="🏦 Financial Data Processor - Enterprise Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 src/handlers/main_handler.py --test-mode
  python3 src/handlers/main_handler.py --processor icici_bank
  python3 src/handlers/main_handler.py --processor icici_bank --file path/to/file.xls
  python3 src/handlers/main_handler.py --test-mode --processor icici_bank
        """,
    )

    parser.add_argument(
        "--processor",
        help="Processor type (e.g., icici_bank). If not provided, will show selection menu.",
    )
    parser.add_argument(
        "--file",
        help="Path to file to process. If not provided, will auto-detect or show selection menu.",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (uses test_ prefixed database tables)",
    )

    args = parser.parse_args()

    try:
        print("=" * 60)
        print("🏦 FINANCIAL DATA PROCESSOR - ENTERPRISE EDITION")
        print("=" * 60)

        # Create and run handler
        handler = MainHandler(test_mode=args.test_mode)
        result = handler.run(processor_type=args.processor, file_path=args.file)

        # Exit with appropriate code
        sys.exit(0 if result.get("status") == "success" else 1)

    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        # Try to create emergency backup
        try:
            if "handler" in locals():
                print("🔄 Creating emergency backup...")
                handler.backup_manager.create_backup("interruption")
        except:
            pass  # Don't fail if backup fails
        sys.exit(1)


if __name__ == "__main__":
    main()
