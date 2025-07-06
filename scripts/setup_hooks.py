#!/usr/bin/env python3
"""
Pre-commit Hooks Setup Script for Financial Data Processor
Automatically installs and configures all pre-commit hooks for code quality assurance

Usage:
    python scripts/setup_hooks.py
    python scripts/setup_hooks.py --install-only  # Skip hook installation
    python scripts/setup_hooks.py --check         # Check current setup
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        print(f"❌ {description} failed")
        print(f"   Error: {result.stderr.strip()}")
        return False
    except (OSError, IOError, subprocess.SubprocessError) as exception:
        print(f"❌ {description} failed with exception: {exception}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    msg = f"❌ Python version {version.major}.{version.minor}.{version.micro} is not compatible"
    print(msg)
    print("   Requires Python 3.8 or higher")
    return False


def check_git_repository():
    """Check if we're in a git repository"""
    if Path(".git").exists() or run_command("git rev-parse --git-dir", "Checking git repository"):
        print("✅ Git repository detected")
        return True
    print("❌ Not in a git repository")
    return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing Pre-commit Dependencies")
    print("=" * 50)

    dependencies = [
        "pre-commit>=3.0.0",
        "black>=22.0.0",
        "isort>=5.13.0",
        "pylint>=3.0.0",
        "bandit>=1.7.5",
        "mypy>=0.991",
    ]

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("Setup cancelled. Please activate a virtual environment first.")
            return False

    success = True
    for dep in dependencies:
        if not run_command(f"pip install '{dep}'", f"Installing {dep.split('>=', maxsplit=1)[0]}"):
            success = False

    return success


def setup_pre_commit():
    """Setup pre-commit hooks"""
    print("\n🔧 Setting Up Pre-commit Hooks")
    print("=" * 50)

    # Install pre-commit hooks
    if not run_command(
        "pre-commit install --config config/.pre-commit-config.yaml",
        "Installing pre-commit hooks",
    ):
        return False

    # Install commit message hooks
    if not run_command(
        "pre-commit install --hook-type commit-msg --config config/.pre-commit-config.yaml",
        "Installing commit message hooks",
    ):
        return False

    # Install pre-push hooks
    if not run_command(
        "pre-commit install --hook-type pre-push --config config/.pre-commit-config.yaml",
        "Installing pre-push hooks",
    ):
        return False

    return True


def run_initial_check():
    """Run initial pre-commit check on all files"""
    print("\n🧪 Running Initial Pre-commit Check")
    print("=" * 50)

    print("⚠️  This may take a few minutes on first run...")

    # Run pre-commit on all files (may fail first time, that's normal)
    result = subprocess.run(
        "pre-commit run --all-files --config config/.pre-commit-config.yaml",
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ All pre-commit checks passed!")
    else:
        print("⚠️  Some pre-commit checks failed (this is normal on first run)")
        print("   Files have been automatically formatted where possible")
        print("   Please review changes and commit them")

        # Show summary of what was changed
        if "files were re-formatted" in result.stdout or "would reformat" in result.stdout:
            print("\n📝 Files were automatically formatted by Black")
        if "Fixing" in result.stdout:
            print("🔧 Files were automatically fixed by other hooks")

    return True


def check_setup():
    """Check current pre-commit setup"""
    print("\n🔍 Checking Pre-commit Setup")
    print("=" * 50)

    # Check if pre-commit is installed
    if not run_command("pre-commit --version", "Checking pre-commit installation"):
        return False

    # Check if hooks are installed
    if not run_command(
        "pre-commit status --config config/.pre-commit-config.yaml",
        "Checking hook installation status",
    ):
        return False

    # List installed hooks
    run_command("ls -la .git/hooks/", "Listing installed git hooks")

    return True


def display_usage_info():
    """Display information about using the pre-commit hooks"""
    print("\n" + "=" * 60)
    print("🎉 PRE-COMMIT HOOKS SETUP COMPLETE!")
    print("=" * 60)

    print("\n📋 What's Installed:")
    print("  🎨 Black - Code formatting")
    print("  📦 isort - Import sorting")
    print("  🔍 Pylint - Code quality analysis")
    print("  🛡️ Bandit - Security scanning")
    print("  🔬 MyPy - Type checking")
    print("  🧪 Unit Tests - All unit tests")
    print("  🔄 Integration Tests - All integration tests")
    print("  🛡️ Security Tests - All security tests")
    print("  💬 Commit Message - Conventional commit validation")

    print("\n🚀 Usage:")
    print("  • Hooks run automatically on every commit")
    print("  • Performance tests run only on push (not every commit)")
    print("  • Coverage checks run on push for full validation")

    print("\n⚡ Manual Commands:")
    print(
        "  pre-commit run --all-files --config config/.pre-commit-config.yaml     # Run all hooks on all files"
    )
    print(
        "  pre-commit run black --config config/.pre-commit-config.yaml          # Run only Black formatter"
    )
    print(
        "  pre-commit run pylint --config config/.pre-commit-config.yaml         # Run only Pylint"
    )
    print(
        "  pre-commit run unit-tests --config config/.pre-commit-config.yaml     # Run only unit tests"
    )

    print("\n🔧 Bypass Hooks (use sparingly):")
    print("  git commit --no-verify        # Skip pre-commit hooks")
    print("  git push --no-verify          # Skip pre-push hooks")

    print("\n📚 Commit Message Format:")
    print("  feat: add new transaction processor")
    print("  fix: resolve currency detection bug")
    print("  docs: update installation guide")
    print("  test: add integration tests for splits")
    print("  refactor: optimize database queries")

    print("\n🎯 Next Steps:")
    print("  1. Make a test commit to verify hooks work")
    print("  2. All team members should run this setup script")
    print("  3. Hooks will ensure consistent code quality")


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="Setup pre-commit hooks for Financial Data Processor"
    )
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Only install dependencies, skip hook setup",
    )
    parser.add_argument("--check", action="store_true", help="Check current setup status")
    args = parser.parse_args()

    print("🚀 Financial Data Processor - Pre-commit Hooks Setup")
    print("=" * 60)

    # Check setup status if requested
    if args.check:
        success = check_setup()
        sys.exit(0 if success else 1)

    # Pre-flight checks
    if not check_python_version():
        sys.exit(1)

    if not check_git_repository():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)

    # Setup hooks (unless install-only)
    if not args.install_only:
        if not setup_pre_commit():
            print("\n❌ Failed to setup pre-commit hooks")
            sys.exit(1)

        # Run initial check
        run_initial_check()

        # Display usage information
        display_usage_info()
    else:
        print("\n✅ Dependencies installed successfully")
        print("   Run 'pre-commit install --config config/.pre-commit-config.yaml' to setup hooks")


if __name__ == "__main__":
    main()
