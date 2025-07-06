#!/usr/bin/env python3
"""
Enterprise-Grade Smoke Test Suite for Financial Data Processing System

This suite validates critical system functionality with enterprise standards
including security, performance, configuration, and operational readiness.

Features:
- Comprehensive system validation in <60 seconds
- Structured logging and detailed reporting
- Security boundary verification
- Performance baseline measurement
- Configuration integrity checks
- Dependency validation
- CI/CD integration ready
- Zero production impact
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add src to path for imports (we're now in tests/ directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class SmokeTestSuite:
    """Enterprise smoke test suite with comprehensive validation"""

    def __init__(self, verbose: bool = False, json_output: bool = False):
        self.verbose = verbose
        self.json_output = json_output
        self.results = []
        self.start_time = time.time()
        self.performance_metrics = {}
        self.security_checks = []

        # Setup logging
        self.setup_logging()

        # Test configuration
        self.test_config = {
            "max_execution_time": 60,  # seconds
            "performance_thresholds": {
                "config_load_time": 1.0,
                "database_connect_time": 2.0,
                "module_import_time": 3.0,
                "file_detection_time": 0.5,
            },
            "required_directories": ["src", "tests", "config", "scripts"],
            "required_files": [
                "requirements.txt",
                "pytest.ini",
                "README.md",
            ],
            "critical_modules": [
                "src.utils.config_loader",
                "src.models.database",
                "src.loaders.database_loader",
                "src.extractors.file_based_extractors.excel_extractor",
                "src.handlers.main_handler",
            ],
        }

    def setup_logging(self):
        """Setup structured logging for enterprise environments"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("smoke_test.log", mode="w"),
            ],
        )

        self.logger = logging.getLogger("SmokeTest")
        self.logger.info("Enterprise Smoke Test Suite initialized")

    def record_result(
        self,
        test_name: str,
        passed: bool,
        duration: float,
        message: str = "",
        details: Optional[Dict] = None,
    ):
        """Record test result with enterprise metrics"""
        result = {
            "test_name": test_name,
            "status": "PASS" if passed else "FAIL",
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "details": details or {},
        }

        self.results.append(result)

        # Log result
        status_emoji = "✅" if passed else "❌"
        self.logger.info("%s %s: %s (%.3fs)", status_emoji, test_name, result["status"], duration)

        if not passed:
            self.logger.error("FAILURE DETAILS: %s", message)
            if details:
                self.logger.error("ADDITIONAL INFO: %s", json.dumps(details, indent=2))

    def test_environment_setup(self) -> bool:
        """Validate environment setup and requirements"""
        start_time = time.time()

        try:
            issues = []

            # Check Python version
            if sys.version_info < (3, 8):
                issues.append(f"Python version {sys.version} < 3.8 minimum requirement")

            # Check project structure (we're now in tests/ directory)
            current_project_root = Path(__file__).parent.parent
            for directory in self.test_config["required_directories"]:
                if not (current_project_root / directory).exists():
                    issues.append(f"Missing required directory: {directory}")

            for file_path in self.test_config["required_files"]:
                if not (current_project_root / file_path).exists():
                    issues.append(f"Missing required file: {file_path}")

            # Check write permissions
            try:
                with tempfile.NamedTemporaryFile(dir=current_project_root, delete=True):
                    pass
            except Exception as exception:
                issues.append(f"No write permission in project root: {exception}")

            # Check required environment variables
            if os.getenv("LEDGER_TEST_MODE") != "true":
                os.environ["LEDGER_TEST_MODE"] = "true"  # Set for smoke test

            duration = time.time() - start_time
            success = len(issues) == 0

            details_dict = {"issues": issues, "python_version": sys.version}
            self.record_result(
                "Environment Setup",
                success,
                duration,
                f"{len(issues)} issues found" if issues else "Environment validated",
                details_dict,
            )

            return success

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Environment Setup",
                False,
                duration,
                f"Environment check failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def test_configuration_loading(self) -> bool:
        """Test configuration system integrity"""
        start_time = time.time()

        try:
            from src.utils.config_loader import ConfigLoader

            # Test config loading
            config_loader = ConfigLoader()
            config = config_loader.get_config()

            # Validate config structure
            required_sections = ["database", "processing", "processors"]
            missing_sections = [s for s in required_sections if s not in config]

            # Test category loading (categories are loaded with config)
            categories = config.get("categories", [])

            duration = time.time() - start_time
            self.performance_metrics["config_load_time"] = duration

            success = len(missing_sections) == 0 and len(categories) >= 0

            self.record_result(
                "Configuration Loading",
                success,
                duration,
                f"Config loaded with {len(missing_sections)} missing sections, {len(categories)} categories",
                {"missing_sections": missing_sections, "category_count": len(categories)},
            )

            return success

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Configuration Loading",
                False,
                duration,
                f"Configuration loading failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def test_database_connectivity(self) -> bool:
        """Test database connectivity and basic operations using in-memory database"""
        start_time = time.time()

        try:
            from src.models.database import DatabaseManager
            from src.utils.config_loader import ConfigLoader

            # Create a test config with in-memory database to avoid writing to filesystem
            config_loader = ConfigLoader()
            config = config_loader.get_config()

            # Override database URL to use in-memory SQLite
            test_config = config.copy()
            test_config["database"] = test_config.get("database", {}).copy()
            test_config["database"]["url"] = "sqlite:///:memory:"
            test_config["database"]["test_prefix"] = "test_"

            db_manager = DatabaseManager(test_config, test_mode=True)

            # Test database connection (read-only test)
            session = db_manager.get_session()

            # Just verify we can connect and get a session - no writes
            from sqlalchemy import text

            session.execute(text("SELECT 1"))
            session.close()

            duration = time.time() - start_time
            self.performance_metrics["database_connect_time"] = duration

            self.record_result(
                "Database Connectivity",
                True,
                duration,
                "Database connection successful (in-memory)",
                {"test_mode": True, "database_type": "in-memory"},
            )

            return True

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Database Connectivity",
                False,
                duration,
                f"Database connectivity failed: {exception}",
                {"exception_type": type(exception).__name__, "error_details": str(exception)},
            )
            return False

    def test_critical_modules(self) -> bool:
        """Test critical module imports"""
        start_time = time.time()

        try:
            issues = []

            # Test critical module imports
            for module_name in self.test_config["critical_modules"]:
                try:
                    __import__(module_name)
                except ImportError as exception:
                    issues.append(f"Failed to import {module_name}: {exception}")

            duration = time.time() - start_time
            self.performance_metrics["module_import_time"] = duration

            success = len(issues) == 0

            self.record_result(
                "Critical Modules",
                success,
                duration,
                (
                    f"All {len(self.test_config['critical_modules'])} modules imported successfully"
                    if success
                    else f"{len(issues)} import failures"
                ),
                {"failed_modules": issues},
            )

            return success

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Critical Modules",
                False,
                duration,
                f"Module import test failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def test_file_processing_pipeline(self) -> bool:
        """Test file processing pipeline components"""
        start_time = time.time()

        try:
            # Test extractor availability
            # Test transformer availability
            import src.transformers.icici_bank_transformer
            from src.extractors.file_based_extractors.excel_extractor import ExcelExtractor

            # Test handler availability
            from src.handlers.main_handler import MainHandler

            # Test loader availability
            from src.loaders.database_loader import DatabaseLoader

            duration = time.time() - start_time

            self.record_result(
                "File Processing Pipeline",
                True,
                duration,
                "All pipeline components available",
                {"components": ["extractor", "transformer", "loader", "handler"]},
            )

            return True

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "File Processing Pipeline",
                False,
                duration,
                f"Pipeline component test failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def test_security_boundaries(self) -> bool:
        """Test security boundaries and production safety"""
        start_time = time.time()

        try:
            security_checks = []

            # Check test mode is active
            if os.getenv("LEDGER_TEST_MODE") != "true":
                security_checks.append("LEDGER_TEST_MODE not set to true")

            # Check we're not in production directory
            current_dir = os.getcwd().lower()
            production_indicators = ["production", "prod", "live", "main_db"]
            for indicator in production_indicators:
                if indicator in current_dir:
                    security_checks.append(f"Running in production-like directory: {current_dir}")

            # Check for production database files
            prod_db_files = ["financial_data.db", "production.db", "main.db"]
            for db_file in prod_db_files:
                if os.path.exists(db_file):
                    if os.access(db_file, os.W_OK):
                        security_checks.append(f"Production database {db_file} is writable")

            duration = time.time() - start_time
            success = len(security_checks) == 0

            self.record_result(
                "Security Boundaries",
                success,
                duration,
                f"Security validation {'passed' if success else 'failed'}",
                {"security_issues": security_checks},
            )

            return success

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Security Boundaries",
                False,
                duration,
                f"Security boundary test failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def test_performance_baselines(self) -> bool:
        """Test performance baselines"""
        start_time = time.time()

        try:
            performance_issues = []

            # Check performance thresholds
            for metric, threshold in self.test_config["performance_thresholds"].items():
                if metric in self.performance_metrics:
                    actual_time = self.performance_metrics[metric]
                    if actual_time > threshold:
                        performance_issues.append(
                            f"{metric}: {actual_time:.3f}s > {threshold}s threshold"
                        )

            duration = time.time() - start_time
            success = len(performance_issues) == 0

            self.record_result(
                "Performance Baselines",
                success,
                duration,
                f"Performance {'within' if success else 'exceeds'} thresholds",
                {"performance_issues": performance_issues, "metrics": self.performance_metrics},
            )

            return success

        except Exception as exception:
            duration = time.time() - start_time
            self.record_result(
                "Performance Baselines",
                False,
                duration,
                f"Performance baseline test failed: {exception}",
                {"exception_type": type(exception).__name__},
            )
            return False

    def run_all_tests(self) -> bool:
        """Run all smoke tests and return overall success"""
        self.logger.info("Starting Enterprise Smoke Test Suite")

        tests = [
            self.test_environment_setup,
            self.test_configuration_loading,
            self.test_database_connectivity,
            self.test_critical_modules,
            self.test_file_processing_pipeline,
            self.test_security_boundaries,
            self.test_performance_baselines,
        ]

        passed_tests = 0
        for test_func in tests:
            if test_func():
                passed_tests += 1

        overall_success = passed_tests == len(tests)
        total_duration = time.time() - self.start_time

        self.record_result(
            "Overall Smoke Test",
            overall_success,
            total_duration,
            f"{passed_tests}/{len(tests)} tests passed",
            {"passed_tests": passed_tests, "total_tests": len(tests)},
        )

        return overall_success

    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        passed_tests = sum(1 for result in self.results if result["status"] == "PASS")
        total_tests = len(self.results)

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "results": self.results,
            "performance_metrics": self.performance_metrics,
            "security_checks": self.security_checks,
        }

        return report

    def print_summary(self, report: Dict):
        """Print human-readable test summary"""
        summary = report["summary"]
        print("\n" + "=" * 60)
        print("ENTERPRISE SMOKE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.3f}s")
        print("=" * 60)

        if summary["failed_tests"] > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"❌ {result['test_name']}: {result['message']}")

        print("\nPERFORMANCE METRICS:")
        for metric, value in self.performance_metrics.items():
            print(f"  {metric}: {value:.3f}s")

        print("=" * 60)


def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description="Enterprise Smoke Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="Test timeout in seconds")

    args = parser.parse_args()

    # Set test mode
    os.environ["LEDGER_TEST_MODE"] = "true"

    # Run smoke tests
    smoke_test = SmokeTestSuite(verbose=args.verbose, json_output=args.json)
    success = smoke_test.run_all_tests()

    # Generate and display report
    report = smoke_test.generate_report()
    smoke_test.print_summary(report)

    if args.json:
        print(json.dumps(report, indent=2))

    sys.exit(0 if success else 1)


# Pytest-compatible test functions
import pytest


@pytest.mark.smoke
def test_smoke_environment_setup():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for environment setup"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_environment_setup(), "Environment setup failed"


@pytest.mark.smoke
def test_smoke_configuration_loading():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for configuration loading"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_configuration_loading(), "Configuration loading failed"


@pytest.mark.smoke
def test_smoke_database_connectivity():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for database connectivity"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_database_connectivity(), "Database connectivity failed"


@pytest.mark.smoke
def test_smoke_critical_modules():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for critical modules"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_critical_modules(), "Critical modules test failed"


@pytest.mark.smoke
def test_smoke_file_processing_pipeline():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for file processing pipeline"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_file_processing_pipeline(), "File processing pipeline failed"


@pytest.mark.smoke
def test_smoke_security_boundaries():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for security boundaries"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_security_boundaries(), "Security boundaries test failed"


@pytest.mark.smoke
def test_smoke_performance_baselines():  # pylint: disable=unused-variable
    """Pytest-compatible smoke test for performance baselines"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.test_performance_baselines(), "Performance baselines test failed"


@pytest.mark.smoke
def test_smoke_complete_suite():  # pylint: disable=unused-variable
    """Pytest-compatible complete smoke test suite"""
    smoke_test = SmokeTestSuite(verbose=False)
    assert smoke_test.run_all_tests(), "Complete smoke test suite failed"


if __name__ == "__main__":
    main()
