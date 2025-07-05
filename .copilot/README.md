# GitHub Copilot Instructions for Ledger Project

## Project Overview
This is a financial data processing system that extracts, transforms, and loads transaction data from various bank formats into a SQLite database.

## Architecture
- **Extractors**: Parse bank statements (Excel, CSV, etc.)
- **Transformers**: Convert raw data to standardized format
- **Loaders**: Store processed data in SQLite database
- **Utils**: Security, configuration, currency detection

## Key Technologies
- Python 3.9+
- SQLAlchemy (ORM)
- Pandas (data processing)
- Pytest (testing)
- SQLite (database)

## Code Style & Standards

### Python Code
- Follow PEP 8 with Black formatting (line length: 100)
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public functions
- Use f-strings for string formatting
- Prefer list comprehensions over map/filter when readable

### Security Requirements
- **NEVER** use `shell=True` in subprocess calls
- Always validate file paths to prevent directory traversal
- Use parameterized queries to prevent SQL injection
- Sanitize all user inputs
- Block access to system directories (`/etc/`, `/var/`, etc.)

### Database Patterns
- Use SQLAlchemy ORM for all database operations
- Always use test mode (`test_mode=True`) in tests
- Use in-memory SQLite (`sqlite:///:memory:`) for tests
- Prefix test tables with `test_` to avoid conflicts

### Testing Requirements
- Write unit tests for all new functions
- Use pytest fixtures for test data
- Mock external dependencies
- Ensure 100% test isolation (no production data access)
- Use `@pytest.mark.integration` for integration tests
- Use `@pytest.mark.performance` for performance tests

## File Structure
```
src/
├── extractors/          # Data extraction from files
├── transformers/        # Data transformation logic
├── loaders/            # Database loading operations
├── models/             # SQLAlchemy models
└── utils/              # Shared utilities
tests/
├── conftest.py         # Test fixtures
├── test_*.py          # Test files
└── integration/        # Integration tests
config/
├── config.yaml         # Main configuration
└── categories.yaml     # Transaction categories
```

## Common Patterns

### Configuration Loading
```python
from src.utils.config_loader import ConfigLoader

config_loader = ConfigLoader(
    config_path="config/config.yaml",
    categories_path="config/categories.yaml"
)
config = config_loader.get_config()
```

### Database Operations
```python
from src.models.database import DatabaseManager
from src.loaders.database_loader import DatabaseLoader

db_manager = DatabaseManager(config, test_mode=True)
db_loader = DatabaseLoader(db_manager)
```

### Security Validation
```python
from src.utils.security import sanitize_filename

# Always validate file paths
safe_path = sanitize_filename(file_path)
```

### Error Handling
```python
try:
    # Operation that might fail
    result = some_operation()
except (ValueError, PermissionError) as e:
    # Handle specific exceptions
    logger.error(f"Operation failed: {e}")
    raise
```

## Testing Guidelines

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies
- Use descriptive test names
- Test both success and failure cases

### Integration Tests
- Test complete workflows
- Use realistic test data
- Ensure no production data access
- Test error scenarios

### Performance Tests
- Measure execution time and memory usage
- Use large datasets for stress testing
- Set reasonable performance thresholds
- Monitor for regressions

## Security Checklist
- [ ] No `shell=True` in subprocess calls
- [ ] File paths validated for traversal attempts
- [ ] SQL queries use parameterized statements
- [ ] User inputs sanitized
- [ ] System directory access blocked
- [ ] Test mode used in all tests
- [ ] No hardcoded secrets

## Performance Guidelines
- Use generators for large datasets
- Implement proper cleanup in tests
- Monitor memory usage
- Use efficient data structures
- Profile performance-critical code

## Error Messages
- Use clear, actionable error messages
- Include relevant context
- Avoid exposing internal details
- Log errors appropriately

## Documentation
- Update README.md for new features
- Document configuration options
- Include usage examples
- Maintain changelog

## Git Workflow
- Use conventional commit messages
- Create feature branches
- Write descriptive PR descriptions
- Include tests with new features
- Update documentation as needed

## Common Issues to Avoid
- Don't access production data in tests
- Don't use global state
- Don't ignore security warnings
- Don't skip error handling
- Don't use deprecated APIs
- Don't commit sensitive data

## When in Doubt
- Prefer explicit over implicit
- Choose security over convenience
- Write tests first
- Document your decisions
- Ask for review on complex changes 