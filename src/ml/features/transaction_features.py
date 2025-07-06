"""
Transaction feature extraction for ML models.
"""

import re
import string
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from ..utils.ml_config import MLConfig


class TransactionFeatures:
    """Extract features from transaction data for ML models."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize feature extractor with configuration."""
        self.config = config or MLConfig.get_default_config()["ml"]

    def extract_basic_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic features from transaction data."""
        description = str(transaction.get("description", "")).lower().strip()
        amount = float(transaction.get("debit_amount") or transaction.get("credit_amount") or 0)
        
        features = {
            # Text features
            "description_length": len(description),
            "word_count": len(description.split()),
            "has_numbers": bool(re.search(r'\d', description)),
            "has_special_chars": bool(re.search(r'[^\w\s]', description)),
            "uppercase_ratio": self._get_uppercase_ratio(description),
            
            # Amount features
            "amount": amount,
            "amount_log": np.log1p(amount) if amount > 0 else 0,
            "amount_rounded": round(amount, -1),  # Round to nearest 10
            "is_round_amount": amount % 100 == 0 if amount > 0 else False,
            
            # Transaction type
            "is_debit": transaction.get("debit_amount") is not None,
            "is_credit": transaction.get("credit_amount") is not None,
            
            # Reference features
            "has_reference": bool(transaction.get("reference_number")),
            "reference_length": len(str(transaction.get("reference_number", ""))),
        }
        
        return features

    def extract_text_patterns(self, description: str) -> List[str]:
        """Extract meaningful patterns from transaction description."""
        if not description or len(description) < self.config["feature_extraction"]["min_description_length"]:
            return []
            
        description = description.lower().strip()
        patterns = []
        
        # Extract merchant names (words before common payment terms)
        payment_terms = ['upi', 'neft', 'imps', 'rtgs', 'payment', 'transfer']
        for term in payment_terms:
            if term in description:
                before_term = description.split(term)[0].strip()
                if before_term:
                    patterns.extend(self._extract_meaningful_words(before_term))
        
        # Extract UPI IDs
        upi_matches = re.findall(r'[\w\.-]+@[\w\.-]+', description)
        patterns.extend(upi_matches)
        
        # Extract phone numbers
        phone_matches = re.findall(r'\b\d{10}\b', description)
        patterns.extend(phone_matches)
        
        # Extract meaningful words (not common stop words)
        meaningful_words = self._extract_meaningful_words(description)
        patterns.extend(meaningful_words)
        
        # Filter patterns by length
        min_len = self.config["feature_extraction"]["min_pattern_length"]
        max_len = self.config["feature_extraction"]["max_pattern_length"]
        filtered_patterns = [p for p in patterns if min_len <= len(p) <= max_len]
        
        return list(set(filtered_patterns))  # Remove duplicates

    def extract_temporal_features(self, transaction_date: datetime) -> Dict[str, Any]:
        """Extract temporal features from transaction date."""
        return {
            "day_of_week": transaction_date.weekday(),
            "day_of_month": transaction_date.day,
            "month": transaction_date.month,
            "quarter": (transaction_date.month - 1) // 3 + 1,
            "is_weekend": transaction_date.weekday() >= 5,
            "is_month_start": transaction_date.day <= 5,
            "is_month_end": transaction_date.day >= 25,
            "hour": transaction_date.hour if hasattr(transaction_date, 'hour') else 12,
        }

    def extract_merchant_features(self, description: str) -> Dict[str, Any]:
        """Extract merchant-specific features."""
        description = description.lower()
        
        # Common merchant patterns
        merchant_indicators = {
            'food': ['swiggy', 'zomato', 'food', 'restaurant', 'cafe', 'dominos', 'pizza'],
            'fuel': ['petrol', 'fuel', 'gas', 'bp', 'shell', 'bharat petroleum'],
            'shopping': ['amazon', 'flipkart', 'myntra', 'mall', 'store'],
            'transport': ['uber', 'ola', 'metro', 'bus', 'taxi', 'auto'],
            'utility': ['electricity', 'water', 'gas', 'phone', 'internet', 'wifi'],
            'medical': ['hospital', 'pharmacy', 'medical', 'doctor', 'clinic'],
            'entertainment': ['movie', 'netflix', 'spotify', 'game', 'youtube'],
        }
        
        features = {}
        for category, keywords in merchant_indicators.items():
            features[f'is_{category}'] = any(keyword in description for keyword in keywords)
            
        return features

    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words from text, excluding common stop words."""
        stop_words = {
            'to', 'from', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'with',
            'by', 'upi', 'payment', 'transfer', 'transaction', 'bank', 'ltd', 'pvt',
            'india', 'indian', 'new', 'old', 'good', 'bad', 'big', 'small'
        }
        
        # Remove punctuation and split
        translator = str.maketrans('', '', string.punctuation)
        clean_text = text.translate(translator)
        words = clean_text.split()
        
        # Filter meaningful words
        meaningful = []
        for word in words:
            if (len(word) >= 3 and 
                word.lower() not in stop_words and 
                not word.isdigit() and
                word.isalnum()):
                meaningful.append(word.lower())
                
        return meaningful

    def _get_uppercase_ratio(self, text: str) -> float:
        """Calculate the ratio of uppercase characters in text."""
        if not text:
            return 0.0
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase_count = sum(1 for c in letters if c.isupper())
        return uppercase_count / len(letters)

    def combine_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Combine all feature types for a transaction."""
        basic_features = self.extract_basic_features(transaction)
        
        transaction_date = transaction.get("transaction_date")
        if isinstance(transaction_date, str):
            try:
                transaction_date = pd.to_datetime(transaction_date)
            except (ValueError, TypeError):
                transaction_date = datetime.now()  # Default to current time
        elif transaction_date is None:
            transaction_date = datetime.now()  # Default to current time
            
        temporal_features = self.extract_temporal_features(transaction_date)
        
        description = str(transaction.get("description", ""))
        merchant_features = self.extract_merchant_features(description)
        
        # Combine all features
        all_features = {
            **basic_features,
            **temporal_features,
            **merchant_features,
        }
        
        # Add text patterns as a separate field
        all_features["text_patterns"] = self.extract_text_patterns(description)
        
        return all_features