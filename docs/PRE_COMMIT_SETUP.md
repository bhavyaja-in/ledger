# Pre-commit Hooks Setup Guide

## 🎯 Overview

This financial data processor uses comprehensive pre-commit hooks to ensure code quality, security, and consistency. These hooks run automatically before each commit and push, preventing low-quality code from entering the repository.

## 🚀 Quick Setup

### Automated Setup (Recommended)

```bash
# Run the automated setup script
python scripts/setup_hooks.py

# Or install dependencies only
python scripts/setup_hooks.py --install-only

# Check current setup status
python scripts/setup_hooks.py --check
```

### Manual Setup

```bash
# 1. Install dependencies
pip install pre-commit black isort pylint bandit mypy

# 2. Install pre-commit hooks
pre-commit install --config config/.pre-commit-config.yaml
pre-commit install --hook-type commit-msg --config config/.pre-commit-config.yaml
pre-commit install --hook-type pre-push --config config/.pre-commit-config.yaml

# 3. Run initial check
pre-commit run --all-files --config config/.pre-commit-config.yaml
```

## 📋 What Gets Checked

### 🎨 Code Formatting & Style
- **Black**: Automatic code formatting (line length: 100)
- **isort**: Import statement sorting and organization
- **Trailing Whitespace**: Removes unnecessary whitespace
- **End of File**: Ensures files end with newline

### 🔍 Code Quality Analysis
- **Pylint**: Comprehensive code quality analysis
  - Coding standards compliance
  - Code complexity analysis
  - Variable naming conventions
  - Function/class design patterns

### 🛡️ Security & Safety
- **Bandit**: Security vulnerability scanning
- **Debug Statements**: Prevents debug code in commits
- **Merge Conflicts**: Detects unresolved merge markers

### 🧪 Testing Requirements
- **Unit Tests**: All unit tests must pass (`pytest -m unit`)
- **Integration Tests**: All integration tests must pass (`pytest -m integration`)
- **Security Tests**: All security tests must pass (`pytest -m security`)
- **Performance Tests**: Run on push only (`pytest -m performance`)
- **Coverage Check**: Minimum 80% test coverage (on push)

### 🔬 Type Safety
- **MyPy**: Static type checking for type hints
- **Type Annotations**: Encourages proper type annotations

### 💬 Commit Message Validation
- **Conventional Commits**: Enforces standardized commit messages
- **Valid Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

## 🎯 Commit Message Format

### Standard Format
```
<type>(<scope>): <description>

<body>

<footer>
```

### Examples
```bash
# Feature addition
feat(processor): add multi-currency transaction support

# Bug fix
fix(database): resolve foreign key constraint error

# Documentation
docs(readme): update installation instructions

# Tests
test(integration): add end-to-end workflow tests

# Refactoring
refactor(transformer): optimize transaction parsing logic

# Performance improvement
perf(database): add indexing for faster queries
```

### Valid Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or fixing tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

## ⚡ Hook Execution Timeline

### On Every Commit
```
1. 🎨 Black Code Formatter
2. 📦 isort Import Sorting
3. ✂️  Trailing Whitespace Removal
4. 📄 End of File Fixes
5. 🔍 YAML/JSON/TOML Validation
6. 🔀 Merge Conflict Detection
7. 🛡️ Bandit Security Scanning
8. 🔍 Pylint Code Analysis
9. 🧪 Unit Tests
10. 🔄 Integration Tests
11. 🛡️ Security Tests
12. 💬 Commit Message Validation
```

### On Push Only
```
1. ⚡ Performance Tests
2. 📊 Test Coverage Check (80% minimum)
3. 🔬 MyPy Type Checking
4. 📚 Documentation Validation
```

## 🔧 Manual Commands

### Run All Hooks
```bash
# Run all hooks on all files
pre-commit run --all-files --config config/.pre-commit-config.yaml

# Run all hooks on staged files only
pre-commit run --config config/.pre-commit-config.yaml
```

### Run Specific Hooks
```bash
# Code formatting
pre-commit run black --config config/.pre-commit-config.yaml
pre-commit run isort --config config/.pre-commit-config.yaml

# Code quality
pre-commit run pylint --config config/.pre-commit-config.yaml
pre-commit run bandit --config config/.pre-commit-config.yaml

# Testing
pre-commit run unit-tests --config config/.pre-commit-config.yaml
pre-commit run integration-tests --config config/.pre-commit-config.yaml
pre-commit run security-tests --config config/.pre-commit-config.yaml

# Type checking
pre-commit run mypy --config config/.pre-commit-config.yaml
```

### Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Security tests only
pytest -m security

# Performance tests only
pytest -m performance

# All tests with coverage
pytest --cov=src --cov-report=html
```

## 🚨 Bypassing Hooks (Emergency Use)

### Skip Pre-commit Hooks
```bash
# Skip all pre-commit hooks (use sparingly!)
git commit --no-verify -m "emergency fix: critical production issue"

# Skip pre-push hooks
git push --no-verify
```

### When to Bypass
- ⚠️ **Critical production hotfixes** (immediate security patches)
- 🔧 **Emergency rollbacks** (reverting broken deployments)
- 📝 **Documentation-only changes** (if hooks are failing due to environment issues)

**⚠️ Important**: Bypassed commits should be fixed in follow-up commits as soon as possible.

## 🛠️ Troubleshooting

### Common Issues

#### 1. Hooks Failing on First Run
```bash
# This is normal - run again after auto-formatting
pre-commit run --all-files
```

#### 2. Pylint Errors
```bash
# Check specific pylint errors
pylint src/your_file.py

# Disable specific warnings (in code)
# pylint: disable=unused-variable

# Update config/pylintrc configuration
```

#### 3. Test Failures
```bash
# Run tests individually to debug
pytest tests/test_specific.py -v

# Run with more verbose output
pytest -v -s
```

#### 4. Type Checking Issues
```bash
# Run mypy manually for debugging
mypy src/

# Add type ignores for external libraries
# type: ignore
```

#### 5. Virtual Environment Issues
```bash
# Ensure you're in the correct environment
which python
which pre-commit

# Reinstall in correct environment
pip install -r requirements.txt
pre-commit install
```

### Updating Hooks

```bash
# Update pre-commit hook versions
pre-commit autoupdate

# Clean and reinstall hooks
pre-commit clean
pre-commit install
```

## 📊 Performance Impact

### Expected Times
- **Code Formatting**: ~2-5 seconds
- **Linting**: ~10-30 seconds (depending on code size)
- **Unit Tests**: ~30-60 seconds
- **Integration Tests**: ~60-120 seconds
- **Security Tests**: ~30-45 seconds
- **Performance Tests**: ~120-300 seconds (push only)

### Optimization Tips
- 🚀 **Incremental Commits**: Commit smaller, focused changes
- 🎯 **Targeted Testing**: Focus on affected modules
- ⚡ **Parallel Execution**: Hooks run in parallel where possible
- 🔄 **Cache Usage**: Pre-commit caches results for unchanged files

## 🎉 Benefits

### Code Quality
- ✅ **Consistent Formatting**: All code follows same style
- 🔍 **Early Bug Detection**: Catch issues before review
- 🛡️ **Security Scanning**: Automated vulnerability detection
- 📚 **Documentation**: Enforce documentation standards

### Team Productivity
- ⚡ **Faster Reviews**: Less time spent on style issues
- 🔄 **Automated Fixes**: Many issues fixed automatically
- 🎯 **Focus on Logic**: Reviewers focus on business logic
- 📈 **Quality Metrics**: Consistent quality measurement

### Risk Reduction
- 🚫 **Prevent Broken Code**: Tests must pass before commit
- 🔒 **Security Compliance**: Automated security checks
- 📊 **Coverage Tracking**: Maintain test coverage standards
- 🎯 **Consistent Standards**: Enforced across all contributors

## 🔗 Integration with CI/CD

The pre-commit hooks integrate seamlessly with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Pre-commit Hooks
  run: |
    pre-commit run --all-files
    
- name: Run Test Suite
  run: |
    pytest -m "unit or integration" --cov=src --cov-fail-under=80
```

## 📞 Support

### Getting Help
1. Check this documentation first
2. Run `python scripts/setup_hooks.py --check` for diagnostics
3. Check existing GitHub issues
4. Create new issue with full error output

### Reporting Issues
Include the following information:
- Operating system and Python version
- Full error output
- Steps to reproduce
- Virtual environment status

---

**🎯 Remember**: These hooks are designed to help maintain high code quality and catch issues early. They may seem strict initially, but they'll save significant time in code review and debugging later! 