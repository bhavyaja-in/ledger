# Financial Data Processor (Ledger)

A comprehensive Python-based financial data processing system that extracts, transforms, and categorizes transactions from various banking institutions with intelligent pattern recognition and interactive categorization.

## 🚀 Features

- **Multi-Bank Support**: Currently supports ICICI Bank with extensible architecture for other banks
- **Intelligent Processing**: Smart pattern recognition and categorization system
- **Interactive Categorization**: User-guided transaction categorization with learning capabilities
- **Two-Level Classification**: Transaction enums and expense categories
- **Split Tracking**: Multi-person expense sharing with percentage-based splits
- **Deduplication**: Hash-based duplicate transaction detection
- **Test Mode**: Separate database tables for safe testing
- **Enterprise Architecture**: Modular design with clear separation of concerns

## 📋 Requirements

- Python 3.8+
- SQLite (included with Python)
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

4. **Initialize database**:
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
   python src/handlers/main_handler.py --processor icici_bank --file data/raw/icici_bank/statement.xls
   ```

4. **Test Mode** (uses separate test database):
   ```bash
   python src/handlers/main_handler.py --processor icici_bank --test-mode
   ```

### File Structure

Place your bank statements in the appropriate folders:
```
data/
├── raw/
│   └── icici_bank/          # Place ICICI Bank Excel files here
│       ├── statement1.xls
│       └── statement2.xlsx
└── processed/               # Processed files are moved here
```

## 🏗️ Architecture

### Directory Structure
```
src/
├── handlers/           # Main processing orchestrators
├── extractors/         # Data extraction components
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

## 📊 Two-Level Categorization System

### Level 1: Transaction Enums
- **Purpose**: Pattern-based auto-detection of transaction types
- **Example**: "SWIGGY" enum detects transactions containing "swiggy", "swiggyit"
- **Storage**: Database with JSON patterns for flexible matching

### Level 2: Categories
- **Purpose**: Group enums into logical expense categories
- **Example**: SWIGGY enum → "Food & Dining" category
- **Customizable**: Add new categories on-the-fly during processing

### Example Workflow:
1. Transaction: "UPI-JOHNSMITH-9876543210@paytm"
2. User creates enum: "JOHNSMITH" with patterns ["johnsmith", "9876543210"]
3. User assigns to category: "Friends"
4. Future transactions with "johnsmith" auto-categorize as "Friends"

## 🔧 Configuration

Edit `config/config.yaml` to customize:

```yaml
processors:
  icici_bank:
    name: "ICICI Bank"
    extraction_folder: "data/raw/icici_bank"
    file_types: ["xls", "xlsx"]

categories:
  - name: "income"
  - name: "food"
  - name: "transport"
  # Add more categories as needed
```

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

## 🏦 Supported Banks

- **ICICI Bank**: Excel statements (.xls, .xlsx)
- **Framework Ready**: Easy to add support for other banks

## 📈 Future Enhancements

- **ML-Powered Recommendations**: Smart pattern extraction and categorization
- **Web Dashboard**: Interactive transaction management interface
- **Multi-Bank Integration**: Support for more banking institutions
- **Advanced Analytics**: Spending insights and trends
- **API Integration**: Real-time transaction processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Security Note

- Never commit actual financial data or sensitive information
- Use test mode for development and testing
- Keep your database files secure and backed up

## 📞 Support

For support, please open an issue on GitHub or contact the maintainers.

---

**Happy Financial Processing! 💰📊** 