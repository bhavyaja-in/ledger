# Financial Data Processor - Enterprise Architecture

## 🏗️ Architecture Overview

This financial data processor follows an enterprise-grade architecture with separation of concerns:

```
src/
├── handlers/           # Main processing orchestrators
├── extractors/         # Data extraction components
│   ├── file_based_extractors/      # Generic file extractors (Excel, PDF, CSV)
│   └── channel_based_extractors/   # Institution-specific extractors
├── transformers/       # Data transformation and categorization
├── loaders/           # Database loading and persistence
├── models/            # Database models and schemas
└── utils/             # Utilities and configuration
```

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Production database
python scripts/init_db.py

# Test database (recommended for development)
python scripts/init_db.py --test-mode

# Clean and reinitialize
python scripts/init_db.py --clean --test-mode
```

### 2. Process Financial Files

```bash
# Interactive mode - select processor
python src/handlers/main_handler.py

# Specific processor with auto-file discovery
python src/handlers/main_handler.py --processor icici_bank

# Specific file
python src/handlers/main_handler.py --processor icici_bank --file data/raw/icici_bank/statement.xls

# Test mode (uses test database tables)
python src/handlers/main_handler.py --processor icici_bank --test-mode

# List available processors
python src/handlers/main_handler.py --list-processors
```

## 📊 Two-Level Categorization System

### Level 1: Transaction Enums
- **Purpose**: Pattern-based auto-detection
- **Example**: "SWIGGY" enum detects transactions containing "swiggy", "swiggyit"
- **Storage**: Database table with JSON patterns

### Level 2: Categories  
- **Purpose**: Group enums into expense categories
- **Example**: SWIGGY enum → "Food & Dining" category
- **Storage**: Database table with display names and colors

### Workflow Example:
1. Transaction: "UPI-HIMANSHUJAIN-7665108881@paytm"
2. User creates enum: "HIMANSHUJAIN" with pattern ["himanshujain", "7665108881"]
3. User assigns to category: "Friends"
4. Future transactions with "himanshujain" auto-categorize as "Friends"

## 🔧 Configuration

### Processors Configuration (`config/config.yaml`)

```yaml
processors:
  icici_bank:
    name: "ICICI Bank"
    extraction_folder: "data/raw/icici_bank"
    file_types: ["xls", "xlsx"]
    extractor: "icici_bank_extractor"
    transformer: "icici_bank_transformer"
```

### Adding New Processor

1. **Add configuration** in `config/config.yaml`
2. **Create extractor** in `src/extractors/channel_based_extractors/`
3. **Create transformer** in `src/transformers/`
4. **Follow naming convention**: `{processor_name}_extractor.py` → `{ProcessorName}Extractor` class

## 💾 Database Schema

### Test Mode Support
- **Production tables**: `transactions`, `transaction_enums`, etc.
- **Test tables**: `test_transactions`, `test_transaction_enums`, etc.
- Same schema, different table prefixes

### Key Tables

#### Transactions
```sql
transactions (
    id, transaction_date, description, amount, transaction_type,
    balance, hash, enum_id, category_id, reason, split_data,
    is_settled, reference_number, institution_id, source_file_id
)
```

#### Transaction Enums
```sql
transaction_enums (
    id, name, patterns (JSON), category_id, processor_type
)
```

#### Transaction Categories
```sql
transaction_categories (
    id, name, display_name, description, color_code
)
```

## 🔄 Processing Flow

1. **Handler** → Validates processor, discovers files
2. **Extractor** → Reads file, finds headers, extracts data
3. **Transformer** → Processes transactions, handles categorization
4. **Loader** → Saves to database with deduplication

## 📈 Features

### ✅ Implemented
- **Test Mode**: Separate database tables for testing
- **Auto-Discovery**: Finds files in configured folders
- **Header Detection**: Intelligently finds header rows
- **Two-Level Categorization**: Enums + Categories
- **Deduplication**: Hash-based duplicate detection
- **Interactive Processing**: User-guided categorization
- **Split Tracking**: Multi-person expense splits
- **Skip Functionality**: Skip unclear transactions
- **Real-time Saving**: Immediate persistence

### 🔄 Transaction Processing
- Auto-categorization based on learned patterns
- Manual categorization for new patterns
- Reason/comment per transaction
- Percentage-based splits (yugam 50, chintu 25 = 25% mine)
- Settled status (default: false)

## 🏦 Supported Institutions

- **ICICI Bank**: Excel statements with intelligent header detection
- **Credit Cards**: ICICI, Axis, HDFC, SBI (framework ready)

## 📁 Directory Structure

```
financial_data_processor/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── transaction_enums.json   # Auto-generated enums (legacy)
│   └── expense_categories.json  # Auto-generated categories (legacy)
├── data/
│   ├── raw/                     # Input files by institution
│   ├── processed/               # Processed outputs
│   └── financial_data.db        # SQLite database
├── src/
│   ├── handlers/                # Main orchestrators
│   ├── extractors/              # File reading components
│   ├── transformers/            # Business logic processors
│   ├── loaders/                 # Database operations
│   ├── models/                  # Database schemas
│   └── utils/                   # Shared utilities
└── scripts/
    └── init_db.py              # Database initialization
```

## 🧪 Testing

```bash
# Initialize test database
python scripts/init_db.py --test-mode

# Run with test data
python src/handlers/main_handler.py --processor icici_bank --test-mode

# Clean test database
python scripts/init_db.py --clean-only --test-mode
```

## 📋 Processing Summary

After processing, you'll see:
- **Files Processed**: Number of files successfully processed
- **Transactions Processed**: New transactions added to database
- **Transactions Skipped**: Transactions user chose to skip
- **Already Processed**: Duplicate transactions (previously processed)
- **Already Skipped**: Duplicate transactions (previously skipped)

## 🎯 Best Practices

1. **Use Test Mode** for development and experimentation
2. **Start Small** - process one file at a time initially
3. **Create Meaningful Enums** - use recognizable patterns
4. **Consistent Categories** - reuse existing categories when possible
5. **Descriptive Reasons** - add context for future reference

## 🔍 Troubleshooting

### Common Issues
- **Import Errors**: Ensure you're running from project root
- **Database Errors**: Initialize database first with `init_db.py`
- **File Not Found**: Check file paths and extraction folders
- **Header Not Found**: Verify Excel file format matches ICICI Bank structure

### Debug Mode
```bash
python src/handlers/main_handler.py --processor icici_bank --test-mode
```
Test mode provides more detailed error information.

## 🚧 Future Enhancements

- PDF processing for credit card statements
- OCR support for image-based statements
- Web dashboard for visualization
- Automated expense categorization using AI
- Multi-currency support
- Export functionality (CSV, Excel, PDF reports)
- Mobile app for on-the-go processing 