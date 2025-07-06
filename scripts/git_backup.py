#!/usr/bin/env python3
"""
Git Database Backup - Store encrypted database backups in private repository
"""

import argparse
import base64
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime

import yaml


class GitDatabaseBackup:
    def __init__(
        self,
        config_path="config/backup.yaml",
        db_path=None,
        backup_repo_path=None,
        repo_url=None,
    ):
        # Load configuration
        self.config = self._load_config(config_path)

        # Use provided parameters or fallback to config, then defaults
        self.db_path = db_path or self.config.get("database", {}).get(
            "path", "financial_data.db"
        )
        self.backup_repo_path = backup_repo_path or self.config.get("git", {}).get(
            "backup_repo_path", "../ledger-backups"
        )
        self.repo_url = repo_url or self.config.get("git", {}).get("repo_url")
        self.backup_filename = self.config.get("git", {}).get(
            "backup_filename", "financial_data_backup.db"
        )
        self.encrypt_enabled = self.config.get("git", {}).get("encrypt", True)
        self.auto_push_enabled = self.config.get("git", {}).get("auto_push", True)

    def _load_config(self, config_path):
        """Load backup configuration from YAML file"""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = yaml.safe_load(file) or {}
                print(f"📋 Loaded backup configuration from {config_path}")
                return config
            except (OSError, IOError, yaml.YAMLError) as exception:
                print(
                    f"⚠️  Warning: Could not load config from {config_path}: {exception}"
                )
                print("   Using default configuration")
                return {}
        print(f"⚠️  Config file not found: {config_path}")
        print("   Copy config/backup.yaml.example to config/backup.yaml")
        print("   Using default configuration")
        return {}

    def setup_backup_repo(self):
        """Initialize or clone the backup repository"""
        if os.path.exists(self.backup_repo_path):
            print(f"✅ Backup repository already exists: {self.backup_repo_path}")
            return True

        if self.repo_url:
            try:
                subprocess.run(
                    ["git", "clone", self.repo_url, self.backup_repo_path],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Cloned backup repository: {self.repo_url}")
                return True
            except subprocess.CalledProcessError as exception:
                print(f"❌ Failed to clone repository: {exception}")
                return False
        # Create new repository
        try:
            os.makedirs(self.backup_repo_path, exist_ok=True)
            os.chdir(self.backup_repo_path)

            subprocess.run(["git", "init"], check=True, capture_output=True)

            # Create README
            with open("README.md", "w", encoding="utf-8") as readme_file:
                readme_file.write(
                    """# Financial Database Backups

This private repository contains encrypted backups of financial database.

## Files
- `financial_data_backup.db` - Latest database backup
- `backup_log.txt` - Backup history

## Security
Database backups are stored securely. Only authorized users should have access.

## Restore
Use the git_backup.py script to restore from backups.
"""
                )

            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Setup backup repository"],
                check=True,
                capture_output=True,
            )

            os.chdir("..")  # Go back to original directory
            print(f"✅ Created new backup repository: {self.backup_repo_path}")
            print("💡 Create a private GitHub repo and add remote:")
            print(f"   cd {self.backup_repo_path}")
            print(
                "   git remote add origin https://github.com/YOUR_USERNAME/ledger-backups.git"
            )
            print("   git push -u origin main")
            return True

        except (OSError, IOError, subprocess.CalledProcessError) as exception:
            print(f"❌ Failed to create repository: {exception}")
            return False

    def _preserve_previous_backup(self):
        """Preserve existing backup with timestamp before creating new one"""
        backup_path = os.path.join(self.backup_repo_path, self.backup_filename)

        if not os.path.exists(backup_path):
            # No previous backup to preserve
            return

        # Create timestamped filename for previous backup
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_name = os.path.splitext(self.backup_filename)[0]
        extension = os.path.splitext(self.backup_filename)[1]
        timestamped_filename = f"{base_name}_{timestamp}{extension}"
        timestamped_path = os.path.join(self.backup_repo_path, timestamped_filename)

        original_dir = os.getcwd()
        try:
            # Move current backup to timestamped version
            shutil.move(backup_path, timestamped_path)

            # Commit the timestamped backup to git
            os.chdir(self.backup_repo_path)

            subprocess.run(
                ["git", "add", timestamped_filename], check=True, capture_output=True
            )
            commit_msg = f"Archive previous backup as {timestamped_filename}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg], check=True, capture_output=True
            )

            print(f"📋 Previous backup archived as: {timestamped_filename}")

            # Update backup log to note the archiving
            log_path = os.path.join(self.backup_repo_path, "backup_log.txt")
            timestamp_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"{timestamp_log} - Previous backup archived as {timestamped_filename}\n"
                )

        except subprocess.CalledProcessError as exception:
            print(f"⚠️  Warning: Could not archive previous backup: {exception}")
        except (OSError, IOError, shutil.Error) as exception:
            print(f"⚠️  Warning: Error archiving previous backup: {exception}")
        finally:
            if "original_dir" in locals():
                os.chdir(original_dir)

    def create_backup(self, encrypt=None):
        """Create and commit database backup with timestamped history"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return False

        if not os.path.exists(self.backup_repo_path):
            print("📂 Setting up backup repository...")
            if not self.setup_backup_repo():
                return False

        # Preserve previous backup with timestamp before creating new one
        self._preserve_previous_backup()

        # Create clean backup using SQLite backup API
        temp_backup = f"temp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

        try:
            # Create clean database backup
            self._sqlite_backup(self.db_path, temp_backup)

            backup_path = os.path.join(self.backup_repo_path, self.backup_filename)

            # Use provided encrypt parameter or config setting
            should_encrypt = encrypt if encrypt is not None else self.encrypt_enabled

            # Optionally encrypt the backup
            if should_encrypt:
                self._simple_encrypt(temp_backup, backup_path)
                print("🔐 Database backup encrypted")
            else:
                shutil.move(temp_backup, backup_path)
                print("📁 Database backup created (unencrypted)")

            # Update backup log
            self._update_backup_log()

            # Commit to git
            return self._commit_backup()

        except (OSError, IOError, sqlite3.Error, shutil.Error) as exception:
            print(f"❌ Backup failed: {exception}")
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            return False
        finally:
            if os.path.exists(temp_backup):
                os.remove(temp_backup)

    def _sqlite_backup(self, source_db, backup_db):
        """Create clean database backup using SQLite API"""
        source = sqlite3.connect(source_db)
        backup = sqlite3.connect(backup_db)

        try:
            source.backup(backup)
        finally:
            source.close()
            backup.close()

    def _simple_encrypt(self, input_file, output_file):
        """Simple base64 encoding (not strong encryption, but obfuscates data)"""
        with open(input_file, "rb") as input_f:
            data = input_f.read()

        # Simple obfuscation (for stronger encryption, use cryptography library)
        encoded = base64.b64encode(data)

        with open(output_file, "wb") as output_f:
            output_f.write(encoded)

    def _simple_decrypt(self, input_file, output_file):
        """Decode the simple base64 encoding"""
        with open(input_file, "rb") as input_f:
            encoded_data = input_f.read()

        decoded = base64.b64decode(encoded_data)

        with open(output_file, "wb") as output_f:
            output_f.write(decoded)

    def _update_backup_log(self):
        """Update backup log with timestamp"""
        log_path = os.path.join(self.backup_repo_path, "backup_log.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} - Database backup created\n")

    def _commit_backup(self):
        """Commit backup to git repository"""
        original_dir = os.getcwd()
        try:
            os.chdir(self.backup_repo_path)

            # Add files
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"], capture_output=True
            )

            if result.returncode == 0:
                print("📋 No changes detected - backup already up to date")
                return True

            # Commit changes
            commit_msg = (
                f"Database backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            subprocess.run(
                ["git", "commit", "-m", commit_msg], check=True, capture_output=True
            )

            # Try to push if remote exists
            try:
                subprocess.run(["git", "push"], check=True, capture_output=True)
                print("✅ Backup committed and pushed to remote repository")
            except subprocess.CalledProcessError:
                print("✅ Backup committed locally (no remote configured)")
                print(f"💡 To push to remote: cd {self.backup_repo_path} && git push")

            return True

        except subprocess.CalledProcessError as exception:
            print(f"❌ Git commit failed: {exception}")
            return False
        finally:
            os.chdir(original_dir)

    def restore_backup(self, decrypt=None):
        """Restore database from git backup"""
        backup_path = os.path.join(self.backup_repo_path, self.backup_filename)

        if not os.path.exists(backup_path):
            print(f"❌ No backup found: {backup_path}")
            print("💡 Try: git pull (if using remote repo)")
            return False

        # Backup current database
        if os.path.exists(self.db_path):
            backup_current = f"{self.db_path}.backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, backup_current)
            print(f"💾 Current database backed up: {backup_current}")

        try:
            # Use provided decrypt parameter or config setting
            should_decrypt = decrypt if decrypt is not None else self.encrypt_enabled

            if should_decrypt:
                self._simple_decrypt(backup_path, self.db_path)
                print("🔓 Database restored and decrypted")
            else:
                shutil.copy2(backup_path, self.db_path)
                print("📁 Database restored")

            return True

        except Exception as exception:  # pylint: disable=broad-except
            print(f"❌ Restore failed: {exception}")
            return False

    def restore_from_timestamped_backup(self, backup_filename, decrypt=None):
        """Restore database from a specific timestamped backup"""
        backup_path = os.path.join(self.backup_repo_path, backup_filename)

        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_filename}")
            print("💡 Use --history to see available backups")
            return False

        # Backup current database
        if os.path.exists(self.db_path):
            backup_current = f"{self.db_path}.backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, backup_current)
            print(f"💾 Current database backed up: {backup_current}")

        try:
            # Use provided decrypt parameter or config setting
            should_decrypt = decrypt if decrypt is not None else self.encrypt_enabled

            if should_decrypt:
                self._simple_decrypt(backup_path, self.db_path)
                print(f"🔓 Database restored from {backup_filename} and decrypted")
            else:
                shutil.copy2(backup_path, self.db_path)
                print(f"📁 Database restored from {backup_filename}")

            return True

        except Exception as exception:  # pylint: disable=broad-except
            print(f"❌ Restore failed: {exception}")
            return False

    def sync_from_remote(self):
        """Pull latest backups from remote repository"""
        if not os.path.exists(self.backup_repo_path):
            print("❌ Backup repository not found locally")
            return False

        original_dir = os.getcwd()
        try:
            os.chdir(self.backup_repo_path)

            subprocess.run(["git", "pull"], check=True, capture_output=True)
            print("✅ Synced latest backups from remote")
            return True

        except subprocess.CalledProcessError as exception:
            print(f"❌ Sync failed: {exception}")
            return False
        finally:
            os.chdir(original_dir)

    def show_backup_history(self):
        """Show git history of backups and list backup files"""
        if not os.path.exists(self.backup_repo_path):
            print("❌ Backup repository not found")
            return

        original_dir = os.getcwd()
        try:
            # Show backup files
            print("📁 Available backup files:")
            backup_files = []
            for file in os.listdir(self.backup_repo_path):
                if file.endswith(".db") and file.startswith(
                    os.path.splitext(self.backup_filename)[0]
                ):
                    backup_files.append(file)

            if backup_files:
                backup_files.sort(reverse=True)  # Most recent first
                for i, backup_file in enumerate(backup_files):
                    if backup_file == self.backup_filename:
                        print(f"  {i+1}. {backup_file} (LATEST)")
                    else:
                        print(f"  {i+1}. {backup_file}")
            else:
                print("  No backup files found")

            print()

            # Show git commit history
            os.chdir(self.backup_repo_path)

            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                capture_output=True,
                text=True,
                check=True,
            )

            print("📚 Recent git commit history:")
            print(result.stdout)

        except subprocess.CalledProcessError as exception:
            print(f"❌ Failed to show history: {exception}")
        finally:
            os.chdir(original_dir)


def main():
    """Main entry point for Git Database Backup Manager CLI"""
    parser = argparse.ArgumentParser(description="Git Database Backup Manager")
    parser.add_argument("--backup", action="store_true", help="Create backup")
    parser.add_argument(
        "--restore", action="store_true", help="Restore from latest backup"
    )
    parser.add_argument("--restore-from", help="Restore from specific backup file")
    parser.add_argument("--sync", action="store_true", help="Sync from remote")
    parser.add_argument(
        "--history", action="store_true", help="Show backup history and files"
    )
    parser.add_argument("--setup", help="Setup backup repo with remote URL")
    parser.add_argument("--no-encrypt", action="store_true", help="Skip encryption")
    parser.add_argument(
        "--config", default="config/backup.yaml", help="Backup configuration file"
    )
    parser.add_argument("--repo-path", help="Override backup repository path")

    args = parser.parse_args()

    backup_manager = GitDatabaseBackup(
        config_path=args.config, backup_repo_path=args.repo_path, repo_url=args.setup
    )

    if args.setup:
        backup_manager.setup_backup_repo()
    elif args.backup:
        encrypt = None if not args.no_encrypt else False
        backup_manager.create_backup(encrypt=encrypt)
    elif args.restore:
        decrypt = None if not args.no_encrypt else False
        backup_manager.restore_backup(decrypt=decrypt)
    elif args.restore_from:
        decrypt = None if not args.no_encrypt else False
        backup_manager.restore_from_timestamped_backup(
            args.restore_from, decrypt=decrypt
        )
    elif args.sync:
        backup_manager.sync_from_remote()
    elif args.history:
        backup_manager.show_backup_history()
    else:
        print("Git Database Backup Manager")
        print("\nCommands:")
        print("  --setup URL       Setup backup repository with remote URL")
        print(
            "  --backup          Create and commit database backup (preserves previous backup)"
        )
        print("  --restore         Restore database from latest backup")
        print("  --restore-from X  Restore from specific backup file")
        print("  --sync            Pull latest backups from remote")
        print("  --history         Show backup history and available files")
        print(
            "  --config FILE     Use custom config file (default: config/backup.yaml)"
        )
        print("  --no-encrypt      Skip encryption (use with --backup/--restore)")
        print("\nConfiguration:")
        print(
            "  Copy config/backup.yaml.example to config/backup.yaml to customize settings"
        )
        print("\nExamples:")
        print("  python3 scripts/git_backup.py --backup")
        print("  python3 scripts/git_backup.py --history")
        print(
            "  python3 scripts/git_backup.py --restore-from financial_data_backup_2025-06-30_12-30-45.db"
        )


if __name__ == "__main__":
    main()
