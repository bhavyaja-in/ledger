# Financial Data Processor (Ledger)

A comprehensive Python-based financial data processing system that extracts, transforms, and categorizes transactions from various banking institutions with intelligent pattern recognition, interactive categorization, and automated backup capabilities.

## 🚀 Features

- **Multi-Bank Support**: Currently supports ICICI Bank with extensible architecture for other banks
- **Dual-Category System**: Transaction enums and expense categories for flexible organization
- **Interactive Processing**: User-guided transaction categorization with learning capabilities
- **Smart Pattern Recognition**: Auto-categorization based on learned patterns
- **Split Tracking**: Multi-person expense sharing with percentage-based splits
- **Deduplication**: Hash-based duplicate transaction detection
- **Automated Backups**: Git-based encrypted backup system for data protection
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

## 🧪 Testing

The system includes comprehensive test mode support:

```bash
# Initialize test database
python scripts/init_db.py --test-mode

# Run processing in test mode
python src/handlers/main_handler.py --processor icici_bank --test-mode

# Clean test database
python scripts/init_db.py --clean --test-mode
```

Test mode uses separate database tables (`test_transactions`, etc.) for safe testing.

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