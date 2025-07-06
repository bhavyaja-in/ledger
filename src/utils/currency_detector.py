"""
Currency detection and management utilities
"""

import re
from typing import List, Optional  # pylint: disable=unused-variable

__all__ = ["CurrencyDetector"]


class CurrencyDetector:
    """Detect currency from transaction descriptions and manage currency operations"""

    CURRENCY_PATTERNS = {
        "USD": [r"\$", r"usd", r"dollar", r"united states", r"us\s+dollar"],
        "EUR": [r"€", r"eur", r"euro", r"european"],
        "GBP": [r"£", r"gbp", r"pound", r"sterling", r"british"],
        "INR": [r"₹", r"inr", r"rupee", r"rs\.", r"indian"],
        "JPY": [r"¥", r"jpy", r"yen", r"japanese"],
        "CNY": [r"¥", r"cny", r"yuan", r"rmb", r"chinese"],
        "AUD": [r"aud", r"australian", r"a\$"],
        "CAD": [r"cad", r"canadian", r"c\$"],
        "CHF": [r"chf", r"swiss", r"franc"],
        "SGD": [r"sgd", r"singapore", r"s\$"],
    }

    CURRENCY_SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "INR": "₹",
        "JPY": "¥",
        "CNY": "¥",
        "AUD": "A$",
        "CAD": "C$",
        "CHF": "CHF",
        "SGD": "S$",
    }

    def __init__(self):
        self._interrupted = False

    def detect_currency(self, description: str, available_currencies: List[str]) -> Optional[str]:
        """
        Detect currency from transaction description

        Args:
            description: Transaction description text
            available_currencies: List of currencies supported by processor

        Returns:
            Currency code if single match found, None if multiple/no matches
        """
        if not description or not available_currencies:
            return None

        description_lower = description.lower()

        # Check each available currency for patterns
        detected_currencies = []
        for currency in available_currencies:
            if currency not in self.CURRENCY_PATTERNS:
                continue

            patterns = self.CURRENCY_PATTERNS[currency]
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    if currency not in detected_currencies:
                        detected_currencies.append(currency)
                    break

        # Return single match, or None if multiple/no matches
        return detected_currencies[0] if len(detected_currencies) == 1 else None

    def get_currency_symbol(self, currency_code: str) -> str:
        """Get display symbol for currency"""
        return self.CURRENCY_SYMBOLS.get(currency_code, currency_code)

    def ask_user_for_currency(self, available_currencies: List[str], description: str) -> str:
        """
        Interactive currency selection when detection fails

        Args:
            available_currencies: List of available currency codes
            description: Transaction description for context

        Returns:
            Selected currency code
        """
        print("\n💱 Could not detect currency. Please select for:")
        print(f"📝 Transaction: {description[:60]}{'...' if len(description) > 60 else ''}")
        print("\n📋 Available currencies:")

        for i, currency in enumerate(available_currencies, 1):
            symbol = self.get_currency_symbol(currency)
            print(f"  {i}. {currency} ({symbol})")

        while True:
            if self._interrupted:
                return available_currencies[0]  # Return first currency if interrupted

            try:
                choice = input(f"\n💱 Select currency (1-{len(available_currencies)}): ").strip()

                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_currencies):
                        selected = available_currencies[idx]
                        print(f"✅ Selected currency: {selected}")
                        return selected

                print(f"❌ Please enter a number between 1 and {len(available_currencies)}")

            except (ValueError, KeyboardInterrupt):
                print(f"\n⚠️  Using default currency: {available_currencies[0]}")
                return available_currencies[0]

    def is_valid_currency_code(self, currency_code: str) -> bool:
        """Check if currency code is valid (3 letters)"""
        return bool(currency_code and len(currency_code) == 3 and currency_code.isalpha())

    def normalize_currency_list(self, currencies) -> List[str]:
        """
        Normalize currency configuration to list of valid currency codes

        Args:
            currencies: String or list of currency codes

        Returns:
            List of valid currency codes, defaults to ['INR'] if invalid
        """
        # Handle single currency as string
        if isinstance(currencies, str):
            if self.is_valid_currency_code(currencies):
                return [currencies.upper()]
            return ["INR"]

        # Handle multiple currencies as list
        if isinstance(currencies, list):
            valid_currencies = []
            for currency in currencies:
                if isinstance(currency, str) and self.is_valid_currency_code(currency):
                    valid_currencies.append(currency.upper())

            return valid_currencies if valid_currencies else ["INR"]

        # Invalid configuration - default to INR
        return ["INR"]
