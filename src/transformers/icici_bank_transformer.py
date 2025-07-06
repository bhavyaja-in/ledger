"""
ICICI Bank Transformer - Interactive transaction processing with enum management
"""

import hashlib
import os
import signal
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

import pandas as pd

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# Local imports after path setup
from src.loaders.database_loader import (
    DatabaseLoader,
)  # pylint: disable=wrong-import-position
from src.utils.currency_detector import (
    CurrencyDetector,
)  # pylint: disable=wrong-import-position
from src.utils.security import (  # pylint: disable=wrong-import-position
    sanitize_text_input,
    validate_amount,
)


class IciciBankTransformer:
    """ICICI Bank transformer with interactive processing"""

    def __init__(self, db_manager, config, config_loader=None):
        """Initialize transformer with configuration and database access"""
        self.db_manager = db_manager
        self.config = config
        self.config_loader = config_loader
        self.processor_type = "icici_bank"
        self._interrupted = False

        # Set up currency detector early so we can use it for validation
        self.currency_detector = CurrencyDetector()

        # Get processor currencies with proper validation
        processor_currencies = (
            self.config.get("processors", {})
            .get(self.processor_type, {})
            .get("currency", ["INR"])
        )

        # Use the currency detector's normalize_currency_list method for validation
        self.processor_currencies = self.currency_detector.normalize_currency_list(
            processor_currencies
        )

        # Set up database loader
        self.db_loader = DatabaseLoader(db_manager)

        # Set up signal handler for graceful interrupt
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):  # pylint: disable=unused-argument
        """Handle Ctrl+C signal"""
        print("\n\n🛑 Processing interrupted by user (Ctrl+C)")
        print("🔄 Cleaning up and exiting...")
        self._interrupted = True
        sys.exit(0)  # Force exit immediately

    def process_transactions(
        self, extracted_data: Dict[str, Any], institution, processed_file
    ) -> Dict[str, Union[int, str]]:
        """Process transactions with interactive categorization"""
        transactions = extracted_data["transactions"]

        # Initialize results with explicit types
        results: Dict[str, Union[int, str]] = {
            "total_transactions": len(transactions),
            "processed_transactions": 0,
            "skipped_transactions": 0,
            "duplicate_transactions": 0,
            "auto_skipped_transactions": 0,  # Previously skipped, auto-skipped due to config
            "status": "in_progress",  # Track processing status
        }

        print(f"\n💰 Processing {len(transactions)} transactions from ICICI Bank...")
        print("=" * 70)
        print("💡 Press Ctrl+C at any time to stop processing")

        try:
            for i, transaction_data in enumerate(transactions, 1):
                # Check if interrupted
                if self._interrupted:
                    break

                print(
                    f"\n{'🔄' if i <= 5 else '⚡'} Transaction {i} of {len(transactions)}"
                )
                print("-" * 50)

                try:
                    # Step 1: Transform basic transaction data
                    transformed = self._transform_transaction(transaction_data["data"])

                    if not transformed:
                        print("❌ Invalid transaction data - skipping")
                        self._handle_skipped_transaction(
                            transaction_data["data"],
                            institution.id,
                            processed_file.id,
                            "Invalid transaction data",
                            i,
                        )
                        # Explicitly cast to int before incrementing
                        results["skipped_transactions"] = (
                            cast(int, results["skipped_transactions"]) + 1
                        )
                        continue

                    # Step 2: Create transaction hash for deduplication
                    transaction_hash = self._create_transaction_hash(transformed)

                    # Step 3: Check for duplicates
                    if self.db_loader.check_transaction_exists(transaction_hash):
                        print("⚠️  Transaction already processed - skipping duplicate")
                        results["duplicate_transactions"] = (
                            cast(int, results["duplicate_transactions"]) + 1
                        )
                        continue

                    # Step 3.1: Check for skipped transactions based on config
                    reprocess_skipped = self.config.get("processing", {}).get(
                        "reprocess_skipped_transactions", False
                    )

                    # Use the same transaction hash for checking skipped transactions
                    # This ensures consistency across different processing sessions
                    if self.db_loader.check_skipped_exists(transaction_hash):
                        if not reprocess_skipped:
                            print(
                                "⚠️  Transaction previously skipped - auto-skipping (set reprocess_skipped_transactions=true to change)"
                            )
                            results["auto_skipped_transactions"] = (
                                cast(int, results["auto_skipped_transactions"]) + 1
                            )
                            continue
                        print(
                            "⚠️  Transaction previously skipped - reprocessing due to config setting"
                        )

                    # Step 4: Display transaction details
                    self._display_transaction(transformed)

                    # Step 5: Interactive processing with skip option during enum check
                    processing_result = self._process_transaction_interactive(
                        transformed
                    )

                    if processing_result["action"] == "skip":
                        self._handle_skipped_transaction(
                            transaction_data["data"],
                            institution.id,
                            processed_file.id,
                            processing_result["reason"],
                            i,
                            transaction_hash,
                        )
                        results["skipped_transactions"] = (
                            cast(int, results["skipped_transactions"]) + 1
                        )
                        print("⏭️  Transaction skipped")
                        continue

                    # Step 6: Save processed transaction
                    transaction_record = {
                        "transaction_hash": transaction_hash,
                        "institution_id": institution.id,
                        "processed_file_id": processed_file.id,
                        "transaction_date": transformed["date"],
                        "description": transformed["description"],
                        "debit_amount": transformed.get("debit_amount"),
                        "credit_amount": transformed.get("credit_amount"),
                        "balance": transformed.get("balance"),
                        "reference_number": transformed.get("reference_number"),
                        "transaction_type": transformed["transaction_type"],
                        "currency": transformed["currency"],
                        "enum_id": processing_result.get("enum_id"),
                        "category": processing_result.get("category"),
                        "transaction_category": processing_result.get(
                            "transaction_category"
                        ),
                        "reason": processing_result.get("reason"),
                        "splits": processing_result.get("splits"),
                        "is_settled": False,
                    }

                    self.db_loader.create_transaction(transaction_record)
                    results["processed_transactions"] = (
                        cast(int, results["processed_transactions"]) + 1
                    )
                    print("✅ Transaction saved successfully")

                except (
                    ValueError,
                    TypeError,
                    AttributeError,
                    OSError,
                    IOError,
                ) as exception:
                    print(f"\u274c Error processing transaction: {exception}")
                    results["skipped_transactions"] = (
                        cast(int, results["skipped_transactions"]) + 1
                    )

            # Determine final status
            proc_trans = cast(int, results["processed_transactions"])
            skip_trans = cast(int, results["skipped_transactions"])
            total_trans = cast(int, results["total_transactions"])

            if proc_trans + skip_trans == total_trans:
                results["status"] = "completed"
            else:
                results["status"] = "partially_completed"

        except (
            ValueError,
            TypeError,
            AttributeError,
            OSError,
            IOError,
        ) as exception:
            print(f"\n\u274c Error during processing: {exception}")
            results["status"] = "error"

        return results

    def _transform_transaction(
        self, row_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform raw transaction data"""
        try:
            # Extract and parse date
            date_str = str(row_data.get("Transaction Date", "")).strip()
            if not date_str or date_str == "nan":
                return None

            try:
                transaction_date = datetime.strptime(date_str, "%d-%m-%Y")
            except ValueError:
                try:
                    transaction_date = datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    return None

            # Extract and sanitize description to prevent XSS attacks
            raw_description = str(row_data.get("Transaction Remarks", "")).strip()
            if not raw_description or raw_description == "nan":
                return None

            # Sanitize the description to prevent XSS and other injection attacks
            description = sanitize_text_input(raw_description, max_length=1000)

            # Extract amounts using correct column names and validate them
            withdrawal = validate_amount(
                str(row_data.get("Withdrawal Amount (INR )", ""))
            )
            deposit = validate_amount(str(row_data.get("Deposit Amount (INR )", "")))
            balance = validate_amount(str(row_data.get("Balance (INR )", "")))

            # Determine transaction type
            transaction_type = "debit" if withdrawal and withdrawal > 0 else "credit"

            # Get reference number and sanitize it
            reference = str(row_data.get("S No.", "")).strip()

            # Create transaction data
            transaction = {
                "date": transaction_date,
                "description": description,
                "debit_amount": withdrawal,
                "credit_amount": deposit,
                "balance": balance,
                "reference_number": reference,
                "transaction_type": transaction_type,
            }

            # Determine currency for this transaction
            currency = self._determine_transaction_currency(row_data)
            transaction["currency"] = currency

            return transaction

        except (
            ValueError,
            TypeError,
            AttributeError,
            OSError,
            IOError,
        ) as exception:
            print(f"Error transforming transaction: {exception}")
            return None

    def _parse_amount(self, amount_str) -> Optional[float]:
        """Parse amount string to float"""
        if pd.isna(amount_str) or str(amount_str).strip() == "":
            return None

        try:
            # Use the security-validated amount parsing
            return validate_amount(str(amount_str))
        except (ValueError, TypeError):
            return None

    def _determine_transaction_currency(self, row_data: Dict[str, Any]) -> str:
        """
        Determine currency for transaction based on processor configuration and detection

        Args:
            row_data: Full transaction row data including description and amounts

        Returns:
            Currency code for the transaction
        """
        # Single currency processor - use default
        if len(self.processor_currencies) == 1:
            return self.processor_currencies[0]

        # Extract text fields to check for currency
        description = str(row_data.get("Transaction Remarks", "")).strip()
        withdrawal_amount = str(row_data.get("Withdrawal Amount (INR )", "")).strip()
        deposit_amount = str(row_data.get("Deposit Amount (INR )", "")).strip()

        # Priority 1: Check amount fields first (more reliable)
        amount_texts = [withdrawal_amount, deposit_amount]
        for amount_text in amount_texts:
            if amount_text and amount_text != "nan" and amount_text != "":
                detected = self.currency_detector.detect_currency(
                    amount_text, self.processor_currencies
                )
                if detected:
                    print(f"🔍 Detected currency from amount: {detected}")
                    return detected

        # Priority 2: Check description
        if description and description != "nan":
            detected = self.currency_detector.detect_currency(
                description, self.processor_currencies
            )
            if detected:
                print(f"🔍 Detected currency from description: {detected}")
                return detected

        # Priority 3: Ask user if we still can't determine
        context_text = f"Description: {description}"
        if withdrawal_amount:
            context_text += f"\nWithdrawal: {withdrawal_amount}"
        if deposit_amount:
            context_text += f"\nDeposit: {deposit_amount}"

        # Use correct parameter order and ensure we always return a string
        currency = self.currency_detector.ask_user_for_currency(
            self.processor_currencies, context_text
        )

        # Fallback to default currency if detection and user input both fail
        if not currency:
            print(
                f"⚠️ Currency detection failed. Using default: {self.processor_currencies[0]}"
            )
            return self.processor_currencies[0]

        return currency

    def _display_transaction(self, transaction: Dict[str, Any]):
        """Display transaction details with better formatting and dynamic currency"""
        currency = transaction.get("currency", "INR")
        symbol = self.currency_detector.get_currency_symbol(currency)

        print(f"📅 Date: {transaction['date'].strftime('%d/%m/%Y')}")

        # Truncate long descriptions for better display
        description = transaction["description"]
        if len(description) > 80:
            description = description[:77] + "..."
        print(f"💬 Description: {description}")

        if transaction["transaction_type"] == "debit":
            print(f"💸 Amount: {symbol}{transaction['debit_amount']:,.2f} (DEBIT)")
        else:
            print(f"💰 Amount: {symbol}{transaction['credit_amount']:,.2f} (CREDIT)")

        if transaction.get("balance"):
            print(f"🏦 Balance: {symbol}{transaction['balance']:,.2f}")

        if transaction.get("reference_number"):
            print(f"🔖 Reference: {transaction['reference_number']}")

        print(f"💱 Currency: {currency}")

    def _process_transaction_interactive(
        self, transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interactive transaction processing with skip option during enum check"""
        description = transaction["description"]

        # Check for existing enum matches first
        existing_enum = self._check_existing_enum_match(description)

        if existing_enum:
            return self._handle_existing_enum_match(existing_enum, description)

        # No existing pattern found - go directly to enhanced pattern interface
        return self._full_interactive_flow(description)

    def _handle_existing_enum_match(
        self, existing_enum: Dict[str, Any], description: str
    ) -> Dict[str, Any]:
        """Handle transaction when existing enum match is found"""
        print(f"\n🔍 Found matching pattern: '{existing_enum['enum_name']}'")
        print(f"📂 Enum Category: {existing_enum['category']}")

        # Step 1: Ask for transaction category first (can be different from enum category)
        transaction_category_result = self._ask_for_transaction_category_with_options(
            existing_enum["category"]
        )

        if transaction_category_result["action"] == "skip":
            return {
                "action": "skip",
                "reason": "User chose to skip - existing pattern found but not used",
            }
        if transaction_category_result["action"] == "create_new":
            return self._full_interactive_flow(description)

        transaction_category = transaction_category_result["category"]

        # Step 2: Ask for reason
        print("\n📋 What's the reason for this transaction?")
        print(
            "💡 Examples: 'Food delivery', 'Salary credit', 'Bill payment', 'Personal transfer'"
        )

        while True:
            if self._interrupted:
                return {"action": "skip", "reason": "Processing interrupted"}

            user_input = input("\n✍️  Reason [Enter for default]: ").strip()

            # User entered a reason
            if user_input and len(user_input) >= 3:
                reason = user_input
                break

            # Provide default if user just presses enter
            if not user_input:
                reason = f"Transaction: {existing_enum['enum_name']}"
                print(f"ℹ️  Using default reason: {reason}")
                break

            print(
                "❌ Please enter a reason (at least 3 characters) or press Enter for default"
            )

        # Step 3: Ask for splits
        splits = self._ask_for_splits()

        return {
            "action": "process",
            "enum_id": existing_enum["id"],
            "category": existing_enum["category"],
            "transaction_category": transaction_category,
            "reason": reason,
            "splits": splits,
        }

    def _check_existing_enum_match(self, description: str) -> Optional[Dict[str, Any]]:
        """Check if description matches existing enum patterns"""
        session = self.db_manager.get_session()
        try:
            TransactionEnum = self.db_manager.models["TransactionEnum"]

            enums = (
                session.query(TransactionEnum)
                .filter_by(processor_type=self.processor_type, is_active=True)
                .all()
            )

            description_lower = description.lower()

            for enum_obj in enums:
                for pattern in enum_obj.patterns:
                    if pattern.lower() in description_lower:
                        return {
                            "id": enum_obj.id,
                            "enum_name": enum_obj.enum_name,
                            "category": enum_obj.category,
                        }

            return None

        finally:
            session.close()

    def _full_interactive_flow(self, description: str) -> Dict[str, Any]:
        """Full interactive flow for new transactions"""
        try:
            # Step 3.1: Ask for pattern word
            pattern_word = self._ask_for_pattern_word(description)
            if not pattern_word:
                return {
                    "action": "skip",
                    "reason": "User chose to skip - no pattern identified",
                }

            # Step 3.2: Ask for enum name
            enum_name = self._ask_for_enum_name(pattern_word)

            # Step 3.3: Handle enum and category
            enum_obj = self._handle_enum_and_category(enum_name, [pattern_word])

            # Step 3.4: Ask for transaction category
            transaction_category = self._ask_for_transaction_category(enum_obj.category)

            # Step 3.5: Ask for reason
            reason = self._ask_for_reason()

            # Step 3.6: Ask for splits
            splits = self._ask_for_splits()

            return {
                "action": "process",
                "enum_id": enum_obj.id,
                "category": enum_obj.category,
                "transaction_category": transaction_category,
                "reason": reason,
                "splits": splits,
            }

        except KeyboardInterrupt:
            print("\n⏭️  Skipping transaction...")
            return {
                "action": "skip",
                "reason": "User interrupted during pattern creation",
            }

    def _ask_for_pattern_word(self, description: str) -> Optional[str]:
        """Ask user for the pattern word with intelligent suggestions"""
        print(f"\n📝 Transaction: {description[:80]}...")

        # Get the best suggestion
        suggestions = self._get_pattern_suggestions(description)
        suggested_pattern = suggestions[0] if suggestions else "transaction"

        print(f"\n💡 Suggested pattern: {suggested_pattern}")
        print(
            "📝 Enter a custom pattern word, press Enter to use suggestion, or type '2' to skip"
        )

        while True:
            if self._interrupted:
                return None

            user_input = (
                input(f"\n🔤 Pattern [Enter for '{suggested_pattern}' | 2 to skip]: ")
                .strip()
                .lower()
            )

            # Option 1: User pressed Enter - use suggested pattern
            if not user_input:
                print(f"✅ Using suggested pattern: {suggested_pattern}")
                return suggested_pattern

            # Option 2: User typed "2" - skip transaction
            if user_input == "2":
                print("⏭️  Skipping transaction...")
                return None

            # Option 3: User typed custom pattern
            if len(user_input) >= 2:
                print(f"✅ Using custom pattern: {user_input}")
                return user_input
            print(
                "❌ Please enter a valid pattern (at least 2 characters), press Enter for suggestion, or type '2' to skip"
            )

    def _get_pattern_suggestions(self, description: str) -> List[str]:
        """Generate intelligent pattern suggestions from description"""
        suggestions = []
        words = description.lower().split()

        # Common patterns to look for
        for word in words:
            # Skip very common words
            if word in [
                "to",
                "from",
                "the",
                "and",
                "or",
                "in",
                "on",
                "at",
                "by",
                "for",
            ]:
                continue

            # Look for potential company names, UPI IDs, etc.
            if len(word) >= 3:
                # Remove special characters for cleaner patterns
                clean_word = "".join(c for c in word if c.isalnum())
                if len(clean_word) >= 3:
                    suggestions.append(clean_word)

        return suggestions[:5]  # Return top 5 suggestions

    def _ask_for_enum_name(self, pattern_word: str) -> str:
        """Ask user for enum name with intelligent suggestion"""
        suggested_name = f"{pattern_word}_transaction"

        print("\n🤔  What should this enum be called?")
        print(f"💡 Suggestion: {suggested_name}")

        while True:
            if self._interrupted:
                return suggested_name  # Return default if interrupted

            enum_name = input(
                f"\n📛 Enum name [press Enter for '{suggested_name}']: "
            ).strip()

            if not enum_name:
                enum_name = suggested_name

            if enum_name and len(enum_name) >= 3:
                return enum_name

            print("❌ Please enter a valid enum name (at least 3 characters)")

    def _handle_enum_and_category(self, enum_name: str, patterns: List[str]):
        """Handle enum creation and category assignment with custom category support"""
        # Check if enum already exists
        session = self.db_manager.get_session()
        try:
            TransactionEnum = self.db_manager.models["TransactionEnum"]
            existing_enum = (
                session.query(TransactionEnum)
                .filter_by(enum_name=enum_name, processor_type=self.processor_type)
                .first()
            )

            if existing_enum:
                print(
                    f"✅ Enum '{enum_name}' already exists with category '{existing_enum.category}'"
                )
                return existing_enum

        finally:
            session.close()

        # Enum doesn't exist - ask for category (with KeyboardInterrupt handling)
        try:
            category = self._ask_for_category()
        except KeyboardInterrupt:  # pylint: disable=try-except-raise
            # If user interrupts during category selection, bubble it up
            raise

        # Create enum
        enum_obj = self.db_loader.create_or_update_enum(
            enum_name=enum_name,
            patterns=patterns,
            category=category,
            processor_type=self.processor_type,
        )

        print(f"✅ Created enum '{enum_name}' with category '{category}'")
        return enum_obj

    def _ask_for_category(self) -> str:
        """Ask user to select category with option to add custom category by typing directly"""
        categories = [cat["name"] for cat in self.config.get("categories", [])]

        print("\n📂 Select enum category:")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category.title()}")

        print(
            f"\n💡 Type a number (1-{len(categories)}) to select, or type a category name to create it"
        )

        while True:
            if self._interrupted:
                return "other"  # Return default if interrupted

            choice = input("\n🔢 Enum Category: ").strip()

            # Check if user entered a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    selected_category = categories[idx]
                    print(f"✅ Selected enum category: {selected_category.title()}")
                    return selected_category
                print(
                    f"❌ Invalid number. Please enter 1-{len(categories)} or type a category name."
                )
                continue

            # User typed a category name - auto-add it
            if choice and len(choice) >= 2:
                category_name = choice.lower()

                # Add new category using the proper method that maintains order
                if self.config_loader:
                    try:
                        self.config_loader.add_category(category_name)
                        print(
                            f"✅ Created and saved new enum category: {category_name.title()}"
                        )
                    except (OSError, IOError, PermissionError) as exception:
                        print(
                            f"⚠️  Enum category created but couldn't save: {exception}"
                        )
                else:
                    # Fallback if no config_loader available
                    existing_categories = [
                        cat["name"].lower() for cat in self.config.get("categories", [])
                    ]
                    if category_name not in existing_categories:
                        if "categories" not in self.config:
                            self.config["categories"] = []
                        self.config["categories"].append({"name": category_name})
                        print(f"✅ Created new enum category: {category_name.title()}")
                    else:
                        print(
                            f"✅ Selected existing enum category: {category_name.title()}"
                        )

                return category_name
            print("❌ Category name must be at least 2 characters long")

    def _ask_for_transaction_category(self, enum_category: str) -> str:
        """Ask user to select transaction category with auto-suggestion from enum category"""
        categories = [cat["name"] for cat in self.config.get("categories", [])]

        print(f"\n🏷️  Transaction Category (Enum category: {enum_category.title()})")
        print("📂 Available categories:")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category.title()}")

        print(
            f"\n💡 Press Enter to use '{enum_category.title()}', type a number (1-{len(categories)}) to select, or type a category name"
        )

        while True:
            if self._interrupted:
                return enum_category  # Return enum category as default if interrupted

            choice = input(
                f"\n🏷️  Transaction Category [Enter for '{enum_category.title()}']: "
            ).strip()

            # User pressed Enter - use enum category
            if not choice:
                print(f"✅ Using enum category: {enum_category.title()}")
                return enum_category

            # Check if user entered a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    selected_category = categories[idx]
                    print(
                        f"✅ Selected transaction category: {selected_category.title()}"
                    )
                    return selected_category
                print(
                    f"❌ Invalid number. Please enter 1-{len(categories)}, press Enter for '{enum_category.title()}', or type a category name."
                )
                continue

            # User typed a category name - auto-add it
            if choice and len(choice) >= 2:
                category_name = choice.lower()

                # Add new category using the proper method that maintains order
                if self.config_loader:
                    try:
                        self.config_loader.add_category(category_name)
                        print(
                            f"✅ Created and saved new transaction category: {category_name.title()}"
                        )
                    except (OSError, IOError, PermissionError) as exception:
                        print(
                            f"⚠️  Transaction category created but couldn't save: {exception}"
                        )
                else:
                    # Fallback if no config_loader available
                    existing_categories = [
                        cat["name"].lower() for cat in self.config.get("categories", [])
                    ]
                    if category_name not in existing_categories:
                        if "categories" not in self.config:
                            self.config["categories"] = []
                        self.config["categories"].append({"name": category_name})
                        print(
                            f"✅ Created new transaction category: {category_name.title()}"
                        )
                    else:
                        print(
                            f"✅ Selected existing transaction category: {category_name.title()}"
                        )

                return category_name
            print("❌ Category name must be at least 2 characters long")

    def _ask_for_transaction_category_with_options(
        self, enum_category: str
    ) -> Dict[str, Any]:
        """Ask user to select transaction category with skip and create new pattern options"""
        categories = [cat["name"] for cat in self.config.get("categories", [])]

        print(
            f"\n🏷️  Choose Transaction Category (can be different from enum category '{enum_category.title()}')"
        )
        print("📂 Available categories:")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category.title()}")

        print(
            f"\n💡 Press Enter to use '{enum_category.title()}', type a number (1-{len(categories)}) to select, or type a category name"
        )
        print("📝 Special options: '2' to skip transaction, '3' to create new pattern")

        while True:
            if self._interrupted:
                return {"action": "skip", "reason": "Processing interrupted"}

            choice = input(
                f"\n🏷️  Transaction Category [Enter for '{enum_category.title()}' | 2=skip | 3=new pattern]: "
            ).strip()

            # Special option 2: Skip transaction
            if choice == "2":
                return {"action": "skip"}

            # Special option 3: Create new pattern
            if choice == "3":
                return {"action": "create_new"}

            # User pressed Enter - use enum category
            if not choice:
                print(f"✅ Using enum category: {enum_category.title()}")
                return {"action": "process", "category": enum_category}

            # Check if user entered a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    selected_category = categories[idx]
                    print(
                        f"✅ Selected transaction category: {selected_category.title()}"
                    )
                    return {"action": "process", "category": selected_category}
                print(
                    f"❌ Invalid number. Please enter 1-{len(categories)}, press Enter for '{enum_category.title()}', or use special options (2=skip, 3=new pattern)"
                )
                continue

            # User typed a category name - auto-add it
            if choice and len(choice) >= 2:
                category_name = choice.lower()

                # Add new category using the proper method that maintains order
                if self.config_loader:
                    try:
                        self.config_loader.add_category(category_name)
                        print(
                            f"✅ Created and saved new transaction category: {category_name.title()}"
                        )
                    except (OSError, IOError, PermissionError) as exception:
                        print(
                            f"⚠️  Transaction category created but couldn't save: {exception}"
                        )
                else:
                    # Fallback if no config_loader available
                    existing_categories = [
                        cat["name"].lower() for cat in self.config.get("categories", [])
                    ]
                    if category_name not in existing_categories:
                        if "categories" not in self.config:
                            self.config["categories"] = []
                        self.config["categories"].append({"name": category_name})
                        print(
                            f"✅ Created new transaction category: {category_name.title()}"
                        )
                    else:
                        print(
                            f"✅ Selected existing transaction category: {category_name.title()}"
                        )

                return {"action": "process", "category": category_name}
            print("❌ Category name must be at least 2 characters long")

    def _ask_for_reason(self) -> str:
        """Ask user for transaction reason with suggestions"""
        print("\n📋 What's the reason for this transaction?")
        print(
            "💡 Examples: 'Food delivery', 'Salary credit', 'Bill payment', 'Personal transfer'"
        )

        while True:
            if self._interrupted:
                return "General transaction"  # Return default if interrupted

            reason = input("\n✍️  Reason: ").strip()

            if reason and len(reason) >= 3:
                return reason

            # Provide default if user just presses enter
            if not reason:
                default_reason = "General transaction"
                print(f"ℹ️  Using default reason: {default_reason}")
                return default_reason

            print(
                "❌ Please enter a reason (at least 3 characters) or press Enter for default"
            )

    def _ask_for_splits(self) -> Optional[List[Dict[str, Any]]]:
        """Ask user for transaction splits with better guidance"""
        print("\n💰 Transaction splits (press Enter if no splits needed):")
        print("💡 Format examples:")
        print("   • yugam:50,chintu:25 → (remaining 25% is yours)")
        print("   • yugam:100 → (everything goes to yugam)")
        print("   • friend:30 → (30% to friend, 70% is yours)")

        while True:
            if self._interrupted:
                return None  # Return None if interrupted

            splits_input = input("\n🔀 Splits: ").strip()

            if not splits_input:
                return None

            splits: List[Dict[str, Any]] = []
            total_percentage: float = 0.0

            for split in splits_input.split(","):
                try:
                    person, percentage_str = split.strip().split(":")
                    percentage = float(percentage_str)

                    if percentage <= 0.0 or percentage > 100.0:
                        print("❌ Percentage must be between 1 and 100")
                        continue

                    splits.append({"person": person.strip(), "percentage": percentage})
                    total_percentage += percentage

                except ValueError:
                    print(f"❌ Invalid format in '{split}'. Use 'name:percentage'")
                    continue

            if total_percentage > 100.0:
                print(f"❌ Total percentage ({total_percentage}%) exceeds 100%")
                continue
            if splits:
                remaining = 100.0 - total_percentage
                if remaining > 0.0:
                    print(f"ℹ️  Your share: {remaining}%")
                return splits

    def _handle_skipped_transaction(
        self,
        row_data: Dict[str, Any],
        institution_id: int,
        processed_file_id: int,
        skip_reason: str,
        row_number: Optional[int] = None,
        transaction_hash: Optional[str] = None,
    ):
        """Handle skipped transaction by storing raw data as-is"""
        try:
            # Use provided transaction hash or generate one for consistency
            if not transaction_hash:
                # Fallback: create hash from raw data (for backward compatibility)
                raw_data_str = str(sorted(row_data.items()))
                hash_input = f"{raw_data_str}_{processed_file_id}_{institution_id}"
                transaction_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            skipped_record = {
                "transaction_hash": transaction_hash,
                "institution_id": institution_id,
                "processed_file_id": processed_file_id,
                "raw_data": row_data,  # Store complete raw data as-is
                "row_number": row_number,
                "skip_reason": skip_reason,
            }

            self.db_loader.create_skipped_transaction(skipped_record)

        except (OSError, IOError, ValueError, KeyError, AttributeError) as exception:
            print(f"❌ Error saving skipped transaction: {exception}")

    def _create_transaction_hash(self, transaction_data: Dict[str, Any]) -> str:
        """Create unique hash for transaction deduplication"""
        # Handle ICICI Bank specific field names
        date_value = (
            transaction_data.get("date")
            or transaction_data.get("Transaction Date")
            or transaction_data.get("transaction_date")
        )

        if date_value is None:
            date_str = "unknown_date"
        elif isinstance(date_value, datetime):
            date_str = date_value.strftime("%Y-%m-%d")
        else:
            date_str = str(date_value)

        # Handle description field with multiple possible names
        description = (
            str(transaction_data.get("description", ""))
            or str(transaction_data.get("Transaction Remarks", ""))
            or str(transaction_data.get("transaction_remarks", ""))
        )

        # Handle amount fields with multiple possible names - fix the logic
        debit_amount = "0"
        if "debit_amount" in transaction_data:
            debit_amount = str(transaction_data["debit_amount"])
        elif "Withdrawal Amount (INR )" in transaction_data:
            debit_amount = str(transaction_data["Withdrawal Amount (INR )"])
        elif "withdrawal_amount" in transaction_data:
            debit_amount = str(transaction_data["withdrawal_amount"])

        credit_amount = "0"
        if "credit_amount" in transaction_data:
            credit_amount = str(transaction_data["credit_amount"])
        elif "Deposit Amount (INR )" in transaction_data:
            credit_amount = str(transaction_data["Deposit Amount (INR )"])
        elif "deposit_amount" in transaction_data:
            credit_amount = str(transaction_data["deposit_amount"])

        # Include additional unique identifiers if available
        reference = str(transaction_data.get("reference_number", "")) or str(
            transaction_data.get("S No.", "")
        )

        hash_string = f"{date_str}_{description}_{debit_amount}_{credit_amount}_{reference}".lower().strip()

        return hashlib.sha256(hash_string.encode()).hexdigest()
