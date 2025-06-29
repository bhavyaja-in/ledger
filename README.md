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