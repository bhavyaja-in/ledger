# Financial Data Processor (Ledger)

A comprehensive Python-based financial data processing system that extracts, transforms, and categorizes transactions from various banking institutions with intelligent pattern recognition, interactive categorization, and automated backup capabilities.

## 🚀 Features

- **Multi-Bank Support**: Currently supports ICICI Bank with extensible architecture for other banks
- **Multi-Currency Support**: Intelligent currency detection and processing for international transactions
- **Dual-Category System**: Transaction enums and expense categories for flexible organization
- **Interactive Processing**: User-guided transaction categorization with learning capabilities
- **Smart Pattern Recognition**: Auto-categorization based on learned patterns
- **Split Tracking**: Multi-person expense sharing with percentage-based splits
- **Deduplication**: Hash-based duplicate transaction detection
- **Automated Backups**: Git-based encrypted backup system for data protection
- **Performance Monitoring**: Comprehensive performance testing and benchmarking capabilities
- **Security Testing**: 24 comprehensive security tests covering OWASP Top 10 vulnerabilities
- **Test Mode**: Separate database tables for safe testing
- **Enterprise Architecture**: Modular design with clear separation of concerns

## 📋 Requirements

- Python 3.8+
- SQLite (included with Python)
- Git (for backup functionality)
- See `requirements.txt` for detailed dependencies

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bhavyaja-in/ledger.git
   cd ledger
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup configuration**:
   ```bash
   # Copy and customize categories
   cp config/categories.yaml.example config/categories.yaml

   # Copy and customize backup settings
   cp config/backup.yaml.example config/backup.yaml
   ```

5. **Initialize database**:
   ```bash
   # For testing (recommended for first run)
   python scripts/init_db.py --test-mode

   # For production
   python scripts/init_db.py
   ```

## 🚀 Quick Start

### Processing Financial Files

1. **Interactive Mode** (recommended for beginners):
   ```bash
   python src/handlers/main_handler.py
   ```

2. **Specific Bank Processor**:
   ```bash
   python src/handlers/main_handler.py --processor icici_bank
   ```

3. **With Specific File**:
   ```bash
   python src/handlers/main_handler.py --processor icici_bank --file data/icici_bank/statement.xls
   ```

4. **Test Mode** (uses separate test database):
   ```bash
   python src/handlers/main_handler.py --processor icici_bank --test-mode
   ```

### File Structure

Place your bank statements in the appropriate folders:
```
data/
├── icici_bank/              # Place ICICI Bank Excel files here
│   ├── statement1.xls
│   └── statement2.xlsx
└── processed/               # Processed files are moved here (optional)
```

## 🏗️ Architecture

### Directory Structure
```
src/
├── handlers/           # Main processing orchestrators
├── extractors/         # Data extraction components
│   ├── file_based_extractors/      # Generic file extractors
│   └── channel_based_extractors/   # Bank-specific extractors
├── transformers/       # Data transformation and categorization
├── loaders/           # Database loading and persistence
├── models/            # Database models and schemas
└── utils/             # Utilities and configuration
```

### Processing Flow
1. **Handler** → Validates processor and discovers files
2. **Extractor** → Reads file and extracts transaction data
3. **Transformer** → Processes transactions with interactive categorization
4. **Loader** → Saves to database with deduplication

## 📊 Dual-Category System

### Level 1: Transaction Enums
- **Purpose**: Pattern-based auto-detection of transaction types
- **Example**: "SWIGGY" enum detects transactions containing "swiggy", "swiggyit"
- **Storage**: Database with JSON patterns for flexible matching

### Level 2: Transaction Categories
- **Purpose**: Group transactions into logical expense categories (independent of enums)
- **Example**: A Swiggy transaction might have enum "SWIGGY" but category "food"
- **Flexibility**: Transaction category can differ from enum category

### Example Workflow:
1. Transaction: "UPI-JOHNSMITH-9876543210@paytm"
2. System asks for transaction category first: "friends"
3. User creates enum: "JOHNSMITH" with patterns ["johnsmith", "9876543210"]
4. User assigns enum to category: "transfer"
5. Future similar transactions auto-categorize with both categories

## 💾 Backup System

### Automated Git-Based Backups with History
- **Encrypted Storage**: Database backups are encrypted and stored in private git repository
- **Timestamped History**: Previous backups automatically preserved with timestamps
- **Version Control**: Every backup and archive operation tracked in git
- **Remote Safety**: Backups stored on GitHub/GitLab, can't be accidentally deleted
- **Point-in-Time Recovery**: Restore from any historical backup
- **Cross-Device Access**: Restore from any computer with git access

### How Backup Preservation Works
When you create a new backup, the system automatically:
1. **Archives Previous**: Renames existing backup with timestamp (e.g., `financial_data_backup_2025-06-30_01-05-41.db`)
2. **Commits Archive**: Previous backup saved to git with descriptive message
3. **Creates New**: Fresh backup becomes the new latest backup
4. **No Data Loss**: Complete history of all backup states preserved

### Backup Commands
```bash
# Create backup (automatically preserves previous backup with timestamp)
python3 scripts/git_backup.py --backup

# View all backup files and git history
python3 scripts/git_backup.py --history

# Restore from latest backup
python3 scripts/git_backup.py --restore

# Restore from specific timestamped backup
python3 scripts/git_backup.py --restore-from financial_data_backup_2025-06-30_01-05-41.db

# Sync latest backups from remote
python3 scripts/git_backup.py --sync
```

### Backup File Structure
Your backup repository maintains:
- `financial_data_backup.db` - Always the latest backup
- `financial_data_backup_YYYY-MM-DD_HH-MM-SS.db` - Timestamped historical backups
- `backup_log.txt` - Detailed log of all backup and archive operations

### Setup Backup Repository
1. Create a private repository on GitHub/GitLab
2. Update `config/backup.yaml` with your repository URL
3. Run initial setup: `python3 scripts/git_backup.py --setup YOUR_REPO_URL`

### Example Backup History
```
📁 Available backup files:
  1. financial_data_backup_2025-06-30_01-06-00.db
  2. financial_data_backup_2025-06-30_01-05-41.db
  3. financial_data_backup.db (LATEST)

📚 Recent git commit history:
Database backup - 2025-06-30 01:06:00
Archive previous backup as financial_data_backup_2025-06-30_01-06-00.db
Database backup - 2025-06-30 01:05:41
Archive previous backup as financial_data_backup_2025-06-30_01-05-41.db
```

## 🔧 Configuration

### Main Configuration (`config/config.yaml`)
Main system configuration - **committed to git**.

### Personal Categories (`config/categories.yaml`)
Your personal spending categories - **gitignored for privacy**.
Copy from `config/categories.yaml.example` and customize.

### Backup Settings (`config/backup.yaml`)
Your backup repository settings - **gitignored for privacy**.
Copy from `config/backup.yaml.example` and customize with your repository URL.

### Currency Configuration

The system supports both **single-currency** and **multi-currency** processors:

#### Single Currency Processor
```yaml
processors:
  icici_bank:
    extractor: "icici_bank_extractor"
    transformer: "icici_bank_transformer"
    file_type: "excel"
    extraction_folder: "data/icici_bank"
    currency: "INR"  # All transactions will be in INR
```

#### Multi-Currency Processor
```yaml
processors:
  icici_forex:
    extractor: "icici_forex_extractor"
    transformer: "icici_forex_transformer"
    file_type: "excel"
    extraction_folder: "data/icici_forex"
    currency: ["USD", "EUR", "GBP", "INR"]  # Multiple currencies supported
```

#### Currency Detection Features
- **Automatic Detection**: System detects currency from transaction descriptions
- **Smart Patterns**: Recognizes currency symbols (₹, $, €, £) and text (USD, EUR, etc.)
- **Interactive Fallback**: When detection fails, asks user to select currency
- **Database Storage**: Currency stored for both transactions and splits
- **Dynamic Display**: Amount formatting adapts to currency (₹1,500 vs $100.00)

#### Supported Currencies
- **USD** ($) - US Dollar
- **EUR** (€) - Euro
- **GBP** (£) - British Pound
- **INR** (₹) - Indian Rupee
- **JPY** (¥) - Japanese Yen
- **CNY** (¥) - Chinese Yuan
- **AUD** (A$) - Australian Dollar
- **CAD** (C$) - Canadian Dollar
- **CHF** (CHF) - Swiss Franc
- **SGD** (S$) - Singapore Dollar

#### Currency Workflow
1. **Single Currency**: Always uses configured currency (no detection needed)
2. **Multi-Currency Detection**:
   - System scans transaction description for currency patterns
   - If single currency detected → Uses automatically
   - If multiple/no currencies detected → Asks user to select
3. **Database Storage**: Currency stored with transaction and splits
4. **Display**: Transaction amounts shown with appropriate currency symbol

## ⚡ Performance Testing

The system includes comprehensive performance monitoring and benchmarking capabilities to ensure optimal performance across all components.

### Performance Test Categories

#### 📊 System Performance Tests
- **Configuration Loading**: Speed and memory usage of system initialization
- **Database Operations**: Bulk insert/query performance with large datasets (1000+ records)
- **File Processing**: Excel extraction performance with various file sizes
- **End-to-End Pipeline**: Complete transaction processing workflow timing

#### 🔧 Component Performance Tests
- **Currency Detection**: Pattern matching speed across different text inputs
- **Transaction Processing**: Single and bulk transaction transformation performance
- **Memory Efficiency**: Memory usage scaling with progressively larger datasets
- **Resource Monitoring**: Real-time CPU and memory tracking during processing

#### 📈 Advanced Monitoring Features
- **Automated Thresholds**: Tests fail if performance degrades beyond acceptable limits
- **Historical Tracking**: Performance data saved to `config/performance_benchmark.json` for trend analysis
- **Regression Detection**: Automatic detection of performance regressions in single transaction processing
- **Benchmark Reporting**: Formatted performance summaries with duration and memory metrics

### Running Performance Tests

#### All Performance Tests
```bash
# Run complete performance test suite
pytest tests/test_performance.py -v

# Run with detailed benchmark output
pytest tests/test_performance.py -v -s
```

#### By Category
```bash
# System-wide performance tests
pytest -m "performance" -v

# Memory efficiency tests
pytest -m "memory" -v

# Performance benchmarking suite
pytest -m "benchmark" -v

# Performance regression detection
pytest -m "regression" -v

# System resource monitoring
pytest -m "system" -v
```

#### Individual Test Types
```bash
# Configuration loading performance
pytest tests/test_performance.py::TestSystemPerformance::test_config_loading_performance -v

# Database operations performance
pytest tests/test_performance.py::TestSystemPerformance::test_bulk_database_operations_performance -v

# File extraction performance
pytest tests/test_performance.py::TestSystemPerformance::test_excel_extraction_performance -v

# Memory efficiency with large datasets
pytest tests/test_performance.py::TestSystemPerformance::test_memory_efficiency_large_datasets -v
```

### Performance Thresholds

The system monitors performance against these configurable thresholds:

| Operation | Duration Limit | Memory Limit | Description |
|-----------|---------------|--------------|-------------|
| Config Loading | < 1.0s | < 10MB | System configuration loading |
| Database Init | < 2.0s | < 20MB | Database initialization |
| Single Transaction | < 0.1s | - | Individual transaction processing |
| Bulk Processing (1000) | < 30s | < 100MB | 1000 transaction batch processing |
| File Extraction (1MB) | < 5s | < 5MB | Excel file extraction per MB |
| Database Query (1000) | < 2s | < 30MB | Query 1000 database records |

### Performance Benchmark Data

#### Benchmark File Structure
Performance data is automatically saved to `config/performance_benchmark.json`:

```json
[
  {
    "timestamp": "2024-01-15T10:30:45.123456",
    "results": {
      "config_loading": {
        "duration": 0.0045,
        "memory": 0.1
      },
      "database_init": {
        "duration": 0.1250,
        "memory": 12.5
      },
      "currency_detection": {
        "duration": 0.0012,
        "memory": 0.0
      }
    }
  }
]
```

#### Benchmark Analysis
- **Duration**: Measured in seconds with microsecond precision
- **Memory**: Memory delta in MB during operation
- **Historical Tracking**: Multiple test runs create trend data for regression analysis
- **Threshold Validation**: Automated alerts when performance degrades beyond limits

### Performance Monitoring Features

#### Real-Time Resource Monitoring
```bash
# View system resource usage during processing
pytest tests/test_performance.py::TestSystemPerformance::test_system_resource_usage -v -s
```

#### Memory Efficiency Scaling
```bash
# Test memory usage with increasing dataset sizes (100→2000 records)
pytest tests/test_performance.py::TestSystemPerformance::test_memory_efficiency_large_datasets -v
```

#### Performance Regression Detection
```bash
# Run 100 iterations to detect performance regressions
pytest tests/test_performance.py::TestSystemPerformance::test_single_transaction_performance -v
```

#### Comprehensive Benchmark Suite
```bash
# Generate complete performance report with historical data
pytest tests/test_performance.py::TestSystemPerformance::test_performance_benchmark_suite -v -s
```

### Expected Performance Results

On a typical development machine, expect these baseline results:

```
🏆 Performance Benchmark Results:
Operation            Duration (s) Memory (MB)
---------------------------------------------
config_loading       0.0050       0.1          ✅
database_init        0.1440       14.5         ✅
currency_detection   0.0015       0.0          ✅
```

### Performance Test Dependencies

Performance testing requires additional dependencies:

```bash
# Install performance monitoring tools
pip install psutil>=5.9.0

# Verify installation
python -c "import psutil; print('psutil version:', psutil.__version__)"
```

### CI/CD Integration

Performance tests integrate with continuous integration:

```bash
# Pre-commit performance validation
pytest -m "performance" --maxfail=1

# Performance regression check
pytest -m "regression" --maxfail=1

# Full performance validation
pytest tests/test_performance.py --tb=short
```

Performance test failures indicate system degradation and should be investigated before deployment.

## 🧪 Testing

The system includes comprehensive enterprise-grade testing with complete safety guarantees:

### Test Categories

#### 🔧 Unit Tests (`@pytest.mark.unit`)
- **Component Testing**: Individual module validation
- **Database Operations**: CRUD operations and schema validation
- **Configuration Loading**: Environment and config validation
- **Currency Detection**: Multi-currency transformation logic

#### 🔄 Integration Tests (`@pytest.mark.integration`)
- **End-to-End Workflow**: Complete transaction processing simulation
- **Database Integration**: Full database operations with test isolation
- **Configuration Integration**: Environment setup and validation
- **Error Handling**: File corruption, missing files, database errors
- **Security Integration**: Production data isolation verification
- **Performance Integration**: Large dataset processing and memory usage

#### ⚡ Performance Tests (`@pytest.mark.performance`)
- **Large File Processing**: 1000+ transaction handling
- **Memory Optimization**: Efficient resource utilization
- **Database Performance**: Query optimization validation
- **Concurrent Processing**: Multi-file processing capabilities

#### 🛡️ Security Tests (`@pytest.mark.security`)
- **Input Validation**: SQL injection and XSS prevention
- **Data Protection**: Sensitive information in logs and memory
- **File Security**: Path traversal and access control
- **Database Security**: Transaction isolation and parameterization
- **Cryptographic Security**: Encryption strength validation
- **System Boundaries**: Production environment protection

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m performance   # Performance tests only
pytest -m security      # Security tests only

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test files
pytest tests/test_integration.py -v     # Integration tests
pytest tests/test_security.py -v       # Security tests
pytest tests/test_performance.py -v    # Performance tests

# CI/CD Integration
pytest -m "unit or integration" --maxfail=1 --tb=line
```

### Test Environment

#### Safe Test Mode
```bash
# Initialize test database
python scripts/init_db.py --test-mode

# Run processing in test mode
python src/handlers/main_handler.py --processor icici_bank --test-mode

# Clean test database
python scripts/init_db.py --clean --test-mode
```

#### Integration Test Environment
- **Complete Isolation**: Uses in-memory SQLite with test prefixes
- **Realistic Data**: Generates authentic transaction scenarios without production files
- **Security Boundaries**: Ensures no production data access
- **Comprehensive Coverage**: Tests all workflows, error scenarios, and edge cases

#### Test Data Generation
```python
# Integration tests create realistic scenarios:
test_scenarios = [
    'Mixed transaction types with multi-currency support',
    'Split transaction processing and settlement tracking',
    'Error handling (corrupted files, missing data)',
    'Performance validation with large datasets',
    'Security boundary verification'
]
```

Test mode uses separate database tables (`test_transactions`, etc.) for complete safety.

## 🔧 Pre-commit Hooks & Code Quality

Enterprise-grade pre-commit hooks ensure consistent code quality and prevent issues before they reach the repository.

### Quick Setup

```bash
# Automated setup (recommended)
python scripts/setup_hooks.py

# Manual verification
python scripts/setup_hooks.py --check
```

### What Gets Checked

- **🎨 Code Formatting**: Black formatter with 100-char line length
- **📦 Import Sorting**: isort for consistent import organization
- **🔍 Code Quality**: Pylint analysis for standards compliance
- **🛡️ Security Scanning**: Bandit for vulnerability detection
- **🧪 Test Requirements**: All unit, integration, and security tests must pass
- **🔬 Type Safety**: MyPy static type checking
- **💬 Commit Messages**: Conventional commit format validation

### Commit Message Format

```bash
# Examples of valid commit messages
feat(processor): add multi-currency transaction support
fix(database): resolve foreign key constraint error
docs(readme): update installation instructions
test(integration): add end-to-end workflow tests
```

### Manual Commands

```bash
# Run all hooks on all files
pre-commit run --all-files --config config/.pre-commit-config.yaml

# Run specific checks
pre-commit run black --config config/.pre-commit-config.yaml          # Code formatting only
pre-commit run pylint --config config/.pre-commit-config.yaml         # Code quality only
pre-commit run unit-tests --config config/.pre-commit-config.yaml     # Unit tests only

# Bypass hooks (emergency use only)
git commit --no-verify -m "emergency fix"
```

### Performance Impact

- **Commit Time**: ~60-120 seconds (formatting, linting, tests)
- **Push Time**: ~180-300 seconds (includes performance tests, coverage)
- **Automatic Fixes**: Code formatting and import sorting applied automatically

For detailed setup instructions and troubleshooting, see [Pre-commit Setup Guide](docs/PRE_COMMIT_SETUP.md).

> 📁 **Configuration Files**: All configuration files (pylint, commitlint, pre-commit) are organized in the `config/` directory.

## 🏦 Supported Banks

- **ICICI Bank**: Excel statements (.xls, .xlsx) with intelligent header detection
- **Framework Ready**: Easy to add support for other banks

### Adding New Bank Support
1. Add processor configuration in `config/config.yaml`
2. Create extractor in `src/extractors/channel_based_extractors/`
3. Create transformer in `src/transformers/`
4. Follow naming convention: `{bank_name}_extractor.py`

## 📈 Transaction Processing Features

- **Auto-categorization**: Based on learned patterns and user input
- **Manual Override**: Full control over categorization
- **Reason/Comments**: Add context to each transaction
- **Split Tracking**: Multi-person expense sharing (e.g., "yugam 50, chintu 25")
- **Multi-Currency Support**: Handle transactions in multiple currencies with automatic detection
- **Currency Intelligence**: Smart detection from transaction descriptions with interactive fallback
- **Skip Functionality**: Skip unclear transactions for later review
- **Real-time Saving**: Immediate database persistence
- **Duplicate Prevention**: Hash-based detection of already-processed transactions

## 🔒 Privacy & Security

- **Local Database**: All data stored locally in SQLite
- **Encrypted Backups**: Backup files are encrypted before git storage
- **Gitignored Configs**: Personal settings never committed to public repos
- **No Cloud Dependencies**: Works completely offline (except backups)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 Additional Resources

- **Setup Guide**: Follow the installation steps above
- **Backup Guide**: See backup system section for data protection
- **Architecture Details**: Check the architecture section for technical overview
- **Contributing Guide**: See contributing section for development setup

**Happy Financial Processing! 💰📊**

# Ledger Database Backups

🔒 **Private Repository** for encrypted financial database backups from the [Ledger Financial Data Processor](https://github.com/bhavyaja-in/ledger).

## 🛡️ Security & Privacy

This repository contains **encrypted backups** of financial transaction databases.

- **⚠️ PRIVATE REPOSITORY**: This repo should NEVER be made public
- **🔐 ENCRYPTED DATA**: All database files are encrypted before storage
- **📅 VERSION CONTROLLED**: Every backup and archive operation tracked with timestamps
- **🚫 NO SENSITIVE DATA**: Raw financial data is encrypted and obfuscated

## 📁 Repository Contents

- `financial_data_backup.db` - **Latest encrypted database backup**
- `financial_data_backup_YYYY-MM-DD_HH-MM-SS.db` - **Timestamped historical backups**
- `backup_log.txt` - **Log of all backup and archive operations**
- `README.md` - This documentation

## 🔄 How Timestamped Backups Work

The backup system now automatically preserves backup history using timestamps:

### Backup Creation Process
1. **Archive Previous**: Existing backup renamed with timestamp (e.g., `financial_data_backup_2025-06-30_01-05-41.db`)
2. **Commit Archive**: Previous backup committed to git with descriptive message
3. **Create New**: Fresh backup created as `financial_data_backup.db` (always latest)
4. **Commit New**: New backup committed to git
5. **Push Remote**: All changes pushed to this private repository

### Benefits
- ✅ **Complete History**: Every backup state preserved forever
- ✅ **Point-in-Time Recovery**: Restore from any specific backup
- ✅ **No Data Loss**: Previous backups never overwritten
- ✅ **Git Versioning**: Full audit trail of all backup operations

## 🚀 Usage

### From Main Ledger Application

```bash
# Create new backup (automatically preserves previous with timestamp)
python3 scripts/git_backup.py --backup

# View all backup files and git history
python3 scripts/git_backup.py --history

# Restore from latest backup
python3 scripts/git_backup.py --restore

# Restore from specific timestamped backup
python3 scripts/git_backup.py --restore-from financial_data_backup_2025-06-30_01-05-41.db

# Sync latest backups from remote
python3 scripts/git_backup.py --sync
```

### Manual Repository Operations

```bash
# Clone this backup repository
git clone https://github.com/bhavyaja-in/ledger-backup.git

# Pull latest backups
git pull

# View git history
git log --oneline

# List all backup files
ls -la *.db
```

## 📊 Example Current State

This repository currently contains:

### Backup Files
```
financial_data_backup.db                          (LATEST)
financial_data_backup_2025-06-30_01-06-00.db    (Historical)
financial_data_backup_2025-06-30_01-05-41.db    (Historical)
```

### Backup Log Sample
```
2025-06-30 01:06:00 - Previous backup archived as financial_data_backup_2025-06-30_01-06-00.db
2025-06-30 01:06:00 - Database backup created
2025-06-30 01:05:41 - Previous backup archived as financial_data_backup_2025-06-30_01-05-41.db
2025-06-30 01:05:41 - Database backup created
```

### Git Commit History
```
Database backup - 2025-06-30 01:06:00
Archive previous backup as financial_data_backup_2025-06-30_01-06-00.db
Database backup - 2025-06-30 01:05:41
Archive previous backup as financial_data_backup_2025-06-30_01-05-41.db
```

## 🔒 Security Notes

### What's Protected
- ✅ **Financial transaction data** - Encrypted before storage
- ✅ **Personal spending patterns** - Not readable in raw form
- ✅ **Bank account information** - Obfuscated in backups
- ✅ **Complete backup history** - All versions preserved securely

### Best Practices
- 🔐 Keep this repository **PRIVATE** at all times
- 🚫 Never share backup files directly
- 💾 Regular backups ensure data protection
- 🔄 Test restore process periodically
- 📅 Use timestamped backups for point-in-time recovery

## 🏗️ Technical Details

### Backup Process
1. **Source**: SQLite database from main ledger application
2. **Preservation**: Previous backup archived with timestamp
3. **Encryption**: Base64 encoding for data obfuscation
4. **Storage**: Git version control with timestamped commits
5. **Location**: Private GitHub repository

### File Structure
```
ledger-backups/
├── financial_data_backup.db                      # Latest backup
├── financial_data_backup_2025-06-30_01-05-41.db # Historical backup
├── financial_data_backup_2025-06-30_01-06-00.db # Historical backup
├── backup_log.txt                                # Operation log
├── README.md                                     # This documentation
└── .git/                                         # Git version control
```

### Restore Process
1. **Safety Backup**: Current database backed up before restore
2. **File Selection**: Choose latest or specific timestamped backup
3. **Decryption**: Base64 decoding to restore original database
4. **Database Replace**: Restored database replaces current version
5. **Verification**: Process completion confirmed

## 🔗 Related

- **Main Repository**: [Ledger Financial Data Processor](https://github.com/bhavyaja-in/ledger)
- **Setup Guide**: See main repository README for backup configuration
- **Support**: Open issues in the main repository

---

## ⚠️ Important Reminders

- **NEVER** make this repository public
- **NEVER** commit unencrypted database files
- **ALWAYS** verify backup integrity before relying on them
- **REGULARLY** test the restore process to ensure backups work
- **USE** timestamped backups for point-in-time recovery when needed

---

## 📈 Backup History Growth

As you use the system, this repository will accumulate:
- **Daily/Weekly Backups**: Regular snapshots of your financial data
- **Timestamped Archives**: Historical versions for point-in-time recovery
- **Git History**: Complete audit trail of all backup operations
- **Log Records**: Detailed timestamps of every backup and archive operation

This ensures **complete data protection** with **professional-grade versioning**! 🛡️

---

*Last Updated: 2025-06-30*

## 🧪 Test Suite Documentation

### Overview

This project implements a **comprehensive enterprise-grade unit test suite** with 296 tests across 7,011 lines of test code, achieving near-100% line coverage. The test suite follows both enterprise and open-source best practices for financial software testing.

### Test Structure

```
tests/
├── conftest.py                     # Enterprise-grade fixtures and configuration
├── test_config_loader.py          # Configuration management tests (31 tests)
├── test_database.py               # Database model tests (33 tests)
├── test_database_loader.py        # Database operations tests (37 tests)
├── test_excel_extractor.py        # Excel processing tests (33 tests)
├── test_icici_bank_extractor.py   # Bank extractor tests (39 tests)
├── test_icici_bank_transformer.py # Transaction processing tests (65 tests)
├── test_git_backup.py            # Backup system tests (45 tests)
└── test_main_handler.py          # Main orchestration tests (45 tests)
```

### Test Categories

The test suite is organized with comprehensive pytest markers:

- `@pytest.mark.unit` - Pure unit tests (majority)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security validation tests
- `@pytest.mark.performance` - Performance and scalability tests
- `@pytest.mark.edge_case` - Edge case and error handling tests
- `@pytest.mark.database` - Database-related tests
- `@pytest.mark.extractor` - Data extraction tests
- `@pytest.mark.transformer` - Data transformation tests
- `@pytest.mark.handler` - Main handler tests
- `@pytest.mark.backup` - Backup system tests

### Running Tests

#### Recommended Testing Workflow

```bash
# 1. FIRST: Quick smoke test (30 seconds) ⚡
PYTHONPATH=. python3 tests/smoke_test.py

# 2. THEN: Run comprehensive tests (2-5 minutes) 🧪
python3 -m pytest


```

**Why This Order?**
- **Smoke tests catch obvious issues immediately** - don't waste time on broken systems
- **Unit/integration tests provide comprehensive validation** - 296 tests with full coverage

#### Basic Test Execution
```bash
# Run all tests
python3 -m pytest

# Run tests with coverage
python3 -m pytest --cov=src --cov-report=html

# Run specific test categories
python3 -m pytest -m unit
python3 -m pytest -m security
python3 -m pytest -m performance
```

#### Advanced Test Execution
```bash
# Run tests with detailed coverage
python3 -m pytest --cov=src --cov=scripts --cov-report=term-missing --cov-report=html -v

# Run tests for specific modules
python3 -m pytest tests/test_database_loader.py -v
python3 -m pytest tests/test_icici_bank_transformer.py::TestIciciBankTransformer::test_process_transactions_complete_workflow_success -v

# Run tests with performance profiling
python3 -m pytest -m performance --durations=10

# Run tests in parallel (if pytest-xdist installed)
python3 -m pytest -n auto
```

#### Coverage Analysis
```bash
# Generate comprehensive coverage report
python3 -m pytest --cov=src --cov=scripts --cov-report=html --cov-report=xml --cov-report=term-missing

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Smoke Testing

**Enterprise-grade smoke tests** validate critical system functionality in under 60 seconds:

```bash
# Quick system validation (recommended first step)
PYTHONPATH=. python3 tests/smoke_test.py

# Detailed output for troubleshooting
PYTHONPATH=. python3 tests/smoke_test.py --verbose

# JSON output for CI/CD integration
PYTHONPATH=. python3 tests/smoke_test.py --json-output > smoke_results.json
```

**What Smoke Tests Validate**:
- ✅ Environment setup and project structure
- ✅ Configuration loading and validation
- ✅ Database connectivity and test mode isolation
- ✅ Critical module imports and initialization
- ✅ File processing pipeline basics
- ✅ Security boundaries and data isolation
- ✅ Performance baselines (<1s config, <3s imports)

**Enterprise Features**:
- Structured logging with timestamps
- Performance metrics and thresholds
- Security boundary validation
- Exit codes for automation (0=pass, 1=fail)
- Complete system readiness assessment

### Security Testing

The system includes a **comprehensive security test suite** with 24 security tests to ensure robust protection against common vulnerabilities and attacks. Security is paramount for financial data processing systems.

#### Security Test Categories

**🛡️ Input Validation Security**
- **SQL Injection Prevention**: Tests protection against malicious SQL injection attempts in all user inputs
- **XSS Injection Prevention**: Validates that cross-site scripting attempts are properly sanitized
- **Path Traversal Prevention**: Ensures file operations cannot access unauthorized system files
- **Buffer Overflow Prevention**: Tests handling of extremely large inputs without system compromise

**🔐 Sensitive Data Protection**
- **Logging Security**: Verifies that sensitive financial data (account numbers, amounts) never appears in logs
- **Memory Data Clearing**: Tests that sensitive data is properly cleared from memory after processing
- **Configuration Secrets**: Ensures secrets and sensitive configuration don't leak in error messages
- **Connection String Protection**: Validates database connection strings don't expose sensitive credentials

**📁 File Access Security**
- **Permission Validation**: Tests proper file permission handling and access control
- **Safe File Handling**: Ensures dangerous file types are handled safely without execution
- **Directory Traversal Protection**: Prevents access to files outside intended directories
- **Path Traversal Prevention**: Advanced detection of `../`, `~`, URL-encoded paths, and system directory access
- **Legitimate Path Support**: Allows legitimate test paths and relative paths while blocking malicious access

**🗄️ Database Security**
- **Transaction Isolation**: Validates proper isolation between test and production data
- **SQL Parameterization**: Ensures all database queries use parameterized statements
- **Schema Protection**: Tests that database schema information isn't exposed

**🔒 Cryptographic Security**
- **Encryption Strength**: Validates encryption methods use appropriate cryptographic strength
- **Hash Collision Resistance**: Tests transaction hashing for collision resistance
- **Random Data Quality**: Verifies cryptographically secure random number generation

**🏰 System Boundary Security**
- **Test Mode Isolation**: Ensures complete isolation between test and production environments
- **Environment Variable Security**: Checks for sensitive data leakage in environment variables
- **Exception Information Disclosure**: Validates exceptions don't reveal sensitive system information
- **Default Security Settings**: Tests that system defaults are secure

#### Running Security Tests

```bash
# Run all security tests (24 tests)
python3 -m pytest -m security

# Run security tests with detailed output
python3 -m pytest -m security -v --tb=long

# Security tests for CI/CD pipelines
python3 -m pytest -m security --maxfail=1 --tb=line

# Run specific security test categories
python3 -m pytest tests/test_security.py::TestInputValidationSecurity -v
python3 -m pytest tests/test_security.py::TestSensitiveDataProtection -v
python3 -m pytest tests/test_security.py::TestDatabaseSecurity -v
```

#### Security Test Results Interpretation

**Expected Security Test Behavior:**
- **Some tests may fail intentionally** - This indicates the security test found a potential vulnerability
- **Passing tests** - Indicate the security control is working properly
- **Failed tests should be investigated** - May indicate actual vulnerabilities or expected security findings

**Sample Security Test Output:**
```bash
PASSED test_sql_injection_prevention     # ✅ SQL injection protection working
FAILED test_xss_injection_prevention     # ⚠️  XSS vulnerability - needs sanitization
PASSED test_encryption_strength         # ✅ Encryption properly implemented
PASSED test_hash_collision_resistance   # ✅ Transaction hashing is secure
FAILED test_memory_data_clearing         # ⚠️  Sensitive data may persist in memory
```

#### Security Compliance

The security test suite validates compliance with:
- **OWASP Top 10** security vulnerabilities
- **Financial data protection** standards
- **Input validation** best practices
- **Secure coding** principles
- **Data privacy** requirements

#### Security Test Maintenance

```bash
# Monthly security validation
python3 -m pytest -m security --tb=short > security_audit.log

# Update security test patterns for new vulnerabilities
# Add new test cases when security issues are discovered
# Review failed tests for actual vulnerabilities vs. false positives
```

**Security Testing Integration:**
```python
# All modules include security validation
@pytest.mark.unit
@pytest.mark.security
def test_input_validation_prevents_injection(self, system_under_test):
    """Test that malicious inputs are properly handled"""
    malicious_input = "'; DROP TABLE transactions; --"

    with pytest.raises(ValidationError):
        system_under_test.process_input(malicious_input)

@pytest.mark.security
def test_sensitive_data_not_logged(self, system_under_test, caplog):
    """Test that sensitive financial data is not logged"""
    sensitive_data = {'account_number': '123456789'}

    system_under_test.process(sensitive_data)

    # Verify sensitive data not in logs
    assert '123456789' not in caplog.text
```

### Test Quality Standards

#### Enterprise-Grade Requirements

1. **100% Isolation**: No production data, files, or systems touched
2. **Security First**: All tests validate security boundaries
3. **Performance Tested**: Large dataset and memory usage validation
4. **Error Resilience**: Comprehensive exception and edge case coverage
5. **Documentation**: Every test method documents its purpose and scope

#### Coverage Requirements

- **Minimum Line Coverage**: 80% (configured in `pytest.ini`)
- **Branch Coverage**: Enabled for comprehensive path testing
- **Missing Line Reporting**: All uncovered lines must be explicitly documented
- **Critical Path Coverage**: 100% coverage required for financial calculations

#### Test Data Security

```python
# ✅ CORRECT: Use isolated test data
@pytest.fixture
def test_transaction_data():
    return {
        'Transaction Date': '01-01-2023',
        'Transaction Remarks': 'TEST TRANSACTION',
        'Withdrawal Amount (INR )': '100.00'
    }

# ❌ WRONG: Never use production data
# Don't load actual bank files or production databases
```

### Test Development Guidelines

#### 1. Writing New Tests

When adding new functionality, ensure:

```python
@pytest.mark.unit
@pytest.mark.database  # Appropriate category marker
def test_new_feature_positive_case(self, fixture_name):
    """Test new feature with valid input - describe exact scenario"""
    # Arrange
    test_data = create_test_data()

    # Act
    result = system_under_test.method(test_data)

    # Assert
    assert result.status == 'success'
    assert result.data is not None
    # Verify no side effects
    mock_database.commit.assert_not_called()

@pytest.mark.unit
@pytest.mark.edge_case
def test_new_feature_edge_cases(self, fixture_name):
    """Test new feature with edge cases - invalid input, boundary conditions"""
    # Test empty input
    with pytest.raises(ValueError, match="Input cannot be empty"):
        system_under_test.method(None)

    # Test boundary conditions
    # Test error scenarios
```

#### 2. Required Test Coverage

For each new module/class, implement:

- **Initialization tests**: Constructor with various parameters
- **Happy path tests**: Normal operation scenarios
- **Error handling tests**: Exception scenarios and error recovery
- **Edge case tests**: Boundary conditions, empty inputs, large datasets
- **Security tests**: Input validation, injection prevention
- **Performance tests**: Memory usage, processing time for large datasets
- **Integration tests**: Interaction with other system components

#### 3. Mock Strategy

```python
# ✅ CORRECT: Mock external dependencies
with patch('src.loaders.database_loader.DatabaseLoader') as mock_db:
    mock_db.return_value.create_transaction.return_value = Mock(id=1)

# ✅ CORRECT: Mock file operations
with patch('builtins.open', mock_open(read_data="test,data\n1,2")):

# ❌ WRONG: Don't mock the system under test itself
# This defeats the purpose of testing actual functionality
```

#### 4. Security Test Requirements

Every module must include security tests:

```python
@pytest.mark.unit
@pytest.mark.security
def test_input_validation_prevents_injection(self, system_under_test):
    """Test that SQL injection attempts are properly handled"""
    malicious_input = "'; DROP TABLE transactions; --"

    with pytest.raises(ValidationError):
        system_under_test.process_input(malicious_input)

@pytest.mark.unit
@pytest.mark.security
def test_sensitive_data_not_logged(self, system_under_test, caplog):
    """Test that sensitive financial data is not logged"""
    sensitive_data = {'account_number': '123456789'}

    system_under_test.process(sensitive_data)

    # Verify sensitive data not in logs
    assert '123456789' not in caplog.text
```

### Continuous Integration

#### Pre-commit Requirements

Before committing code, ensure:

```bash
# 1. All tests pass
python3 -m pytest

# 2. Coverage meets minimum requirements
python3 -m pytest --cov=src --cov-fail-under=80

# 3. Security tests pass
python3 -m pytest -m security

# 4. Performance tests pass
python3 -m pytest -m performance
```

#### Test Environment Setup

```bash
# Install test dependencies
pip install -r requirements.txt

# Set test environment variables
export LEDGER_TEST_MODE=true
export PYTHONPATH=.

# Verify test environment
python3 -c "import os; print('Test mode:', os.getenv('LEDGER_TEST_MODE'))"
```

### Test Configuration

#### pytest.ini Configuration

```ini
[tool:pytest]
# Test discovery
testpaths = tests
python_files = test_*.py

# Coverage requirements
addopts =
    --cov=src
    --cov-fail-under=80
    --cov-branch
    --strict-markers

# Performance monitoring
timeout = 300
```

### Test Maintenance

#### Monthly Test Review Checklist

- [ ] Review coverage reports for gaps
- [ ] Update test data for new edge cases discovered
- [ ] Performance benchmark validation
- [ ] Security test effectiveness review
- [ ] Deprecated test cleanup
- [ ] Test execution time optimization

#### Test Failure Investigation

When tests fail:

1. **Check test isolation**: Ensure no test pollution
2. **Verify mock accuracy**: Ensure mocks match real behavior
3. **Review recent changes**: Identify code changes affecting tests
4. **Update test data**: Ensure test data matches current requirements
5. **Security verification**: Confirm no production data exposure

### Best Practices Summary

#### ✅ Do This:
- Write tests before implementing features (TDD)
- Use descriptive test names explaining the scenario
- Test one specific behavior per test method
- Use appropriate pytest markers
- Mock external dependencies completely
- Validate both positive and negative scenarios
- Include performance and security tests
- Maintain test data isolation

#### ❌ Avoid This:
- Testing multiple unrelated behaviors in one test
- Using production data or configurations
- Mocking the system under test
- Writing tests without clear assertions
- Ignoring edge cases and error scenarios
- Skipping security and performance tests
- Committing code without running tests

### Resources

- **Coverage Reports**: `htmlcov/index.html`
- **Test Logs**: Captured automatically during test runs
- **Performance Metrics**: Available via `--durations` flag
- **Security Guidelines**: See security tests for examples

For questions about testing standards or adding new test categories, refer to the existing test files as examples of enterprise-grade testing patterns.
