"""
Main ML model for transaction classification and categorization.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ..features.transaction_features import TransactionFeatures
from ..utils.ml_config import MLConfig
from .similarity_engine import SimilarityEngine

__all__ = ["TransactionClassifier"]


class TransactionClassifier:
    """ML-powered transaction classifier with continuous learning."""

    def __init__(self, db_manager=None, config: Optional[Dict[str, Any]] = None):
        """Initialize the transaction classifier."""
        self.db_manager = db_manager
        self.config = config or MLConfig.get_default_config()["ml"]

        # Initialize components
        self.feature_extractor = TransactionFeatures(config)
        self.similarity_engine = SimilarityEngine(config)

        # ML Models
        self.category_classifier = None
        self.enum_classifier = None
        self.reason_generator = None

        # Data storage
        self._training_data: list[dict] = []
        self._models_trained = False

        # Initialize models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize ML models with default configuration."""
        # Category classification pipeline
        self.category_classifier = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=self.config["models"]["tfidf"]["max_features"],
                        ngram_range=self.config["models"]["tfidf"]["ngram_range"],
                        lowercase=True,
                        stop_words="english",
                    ),
                ),
                ("nb", MultinomialNB(alpha=self.config["models"]["naive_bayes_alpha"])),
            ]
        )

        # Enum classification pipeline (similar structure)
        self.enum_classifier = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=self.config["models"]["tfidf"]["max_features"],
                        ngram_range=self.config["models"]["tfidf"]["ngram_range"],
                        lowercase=True,
                        stop_words="english",
                    ),
                ),
                ("nb", MultinomialNB(alpha=self.config["models"]["naive_bayes_alpha"])),
            ]
        )

    def suggest_category(self, transaction: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Suggest transaction categories based on ML analysis."""
        suggestions = []

        # Extract features
        features = self.feature_extractor.combine_features(transaction)
        description = str(transaction.get("description", ""))

        # 1. Try similarity-based suggestions first
        similarity_suggestions = self._get_similarity_category_suggestions(transaction)
        suggestions.extend(similarity_suggestions)

        # 2. Try ML model predictions if available
        if self._models_trained and self.category_classifier:
            ml_suggestions = self._get_ml_category_suggestions(description)
            suggestions.extend(ml_suggestions)

        # 3. Try pattern-based suggestions
        pattern_suggestions = self._get_pattern_category_suggestions(features)
        suggestions.extend(pattern_suggestions)

        # Combine and rank suggestions
        ranked_suggestions = self._rank_suggestions(suggestions)

        # Return top suggestions
        max_suggestions = self.config.get("max_suggestions", 5)
        return ranked_suggestions[:max_suggestions]

    def suggest_enum_name(self, transaction: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Suggest enum names based on transaction patterns."""
        suggestions = []
        description = str(transaction.get("description", ""))

        # Extract meaningful patterns
        patterns = self.feature_extractor.extract_text_patterns(description)

        for pattern in patterns:
            # Simple heuristic: use the first meaningful word as enum name
            if len(pattern) >= 3 and pattern.isalpha():
                confidence = 0.7  # Base confidence
                suggestions.append((pattern.upper(), confidence))

        # If no good patterns, suggest based on description
        if not suggestions:
            words = description.lower().split()
            for word in words:
                if len(word) >= 4 and word.isalpha():
                    suggestions.append((word.upper(), 0.5))
                    break

        return suggestions[:3]  # Return top 3

    def suggest_regex_pattern(self, descriptions: List[str]) -> Optional[str]:
        """Suggest regex pattern based on similar descriptions."""
        return self.similarity_engine.suggest_regex_pattern(descriptions)

    def suggest_reason(self, transaction: Dict[str, Any], category: str) -> List[Tuple[str, float]]:
        """Suggest transaction reasons based on context."""
        suggestions = []
        description = str(transaction.get("description", "")).lower()
        _amount = float(transaction.get("debit_amount") or transaction.get("credit_amount") or 0)

        # Template-based reason generation
        reason_templates = {
            "food": [
                f"Food delivery from {self._extract_merchant_name(description)}",
                f"Restaurant payment - {self._extract_merchant_name(description)}",
                f"Food expenses - {category}",
            ],
            "transport": [
                f"Transportation via {self._extract_merchant_name(description)}",
                f"Travel expense - {category}",
                "Commute cost",
            ],
            "shopping": [
                f"Online purchase from {self._extract_merchant_name(description)}",
                f"Shopping expense - {category}",
                "Retail purchase",
            ],
            "utility": [
                "Utility bill payment",
                f"Service payment - {category}",
                "Monthly utility expense",
            ],
        }

        # Get category-specific templates
        templates = reason_templates.get(
            category.lower(),
            [
                f"Payment for {category}",
                f"Expense related to {category}",
                f"Transaction - {category}",
            ],
        )

        for template in templates:
            confidence = 0.6  # Base confidence for template-based reasons
            suggestions.append((template, confidence))

        return suggestions[:3]

    def learn_from_feedback(
        self,
        transaction: Dict[str, Any],
        suggestion_type: str,
        suggested_value: str,
        user_action: str,
        *,
        final_value: Optional[str] = None,
    ):
        """Learn from user feedback to improve future suggestions."""
        if not self.db_manager:
            return

        # Store feedback in database
        feedback_data = {
            "transaction_hash": self._create_transaction_hash(transaction),
            "suggestion_type": suggestion_type,
            "suggested_value": suggested_value,
            "user_action": user_action,
            "final_value": final_value,
            "confidence_score": 0.0,  # Will be calculated
            "features_used": json.dumps(self.feature_extractor.combine_features(transaction)),
        }

        # Update internal learning data
        self._update_learning_data(feedback_data)

        # Retrain models if we have enough new feedback
        if len(self._training_data) % 10 == 0:  # Retrain every 10 feedbacks
            self._retrain_models()

    def get_confidence_score(
        self, transaction: Dict[str, Any], suggestion: str, suggestion_type: str
    ) -> float:
        """Calculate confidence score for a suggestion."""
        base_confidence = 0.5

        # Factors that increase confidence
        factors = []

        # 1. Historical success rate
        historical_confidence = self._get_historical_confidence(
            transaction, suggestion, suggestion_type
        )
        factors.append(historical_confidence)

        # 2. Feature strength
        features = self.feature_extractor.combine_features(transaction)
        feature_confidence = self._calculate_feature_confidence(features)
        factors.append(feature_confidence)

        # 3. Similarity to known patterns
        similarity_confidence = self._calculate_similarity_confidence(transaction, suggestion)
        factors.append(similarity_confidence)

        # Combine factors
        if factors:
            final_confidence = float(np.mean(factors))
        else:
            final_confidence = float(base_confidence)

        return min(1.0, max(0.1, final_confidence))

    def _get_similarity_category_suggestions(
        self, transaction: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """Get category suggestions based on similarity to historical data."""
        suggestions: list[tuple[str, float]] = []

        if not self.db_manager:
            return suggestions

        _description = str(transaction.get("description", ""))

        # Find similar transactions from database
        # This would require database query implementation
        # For now, return empty list

        return suggestions

    def _get_ml_category_suggestions(self, description: str) -> List[Tuple[str, float]]:
        """Get category suggestions from trained ML model."""
        suggestions: list[tuple[str, float]] = []

        if not self.category_classifier or not self._models_trained:
            return suggestions

        try:
            # Predict probabilities
            probabilities = self.category_classifier.predict_proba([description])[0]
            classes = self.category_classifier.classes_

            # Get top predictions
            top_indices = np.argsort(probabilities)[::-1]

            for idx in top_indices:
                confidence = probabilities[idx]
                if confidence >= self.config["confidence_threshold"]:
                    suggestions.append((classes[idx], confidence))

        except (ValueError, AttributeError):
            # Model not ready or other error
            pass

        return suggestions

    def _get_pattern_category_suggestions(
        self, features: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """Get category suggestions based on feature patterns."""
        suggestions = []

        # Rule-based suggestions based on features
        if features.get("is_food", False):
            suggestions.append(("food", 0.8))
        if features.get("is_transport", False):
            suggestions.append(("transport", 0.8))
        if features.get("is_shopping", False):
            suggestions.append(("shopping", 0.8))
        if features.get("is_utility", False):
            suggestions.append(("utility", 0.8))
        if features.get("is_medical", False):
            suggestions.append(("medical", 0.8))
        if features.get("is_entertainment", False):
            suggestions.append(("entertainment", 0.8))

        # Amount-based suggestions
        amount = features.get("amount", 0)
        if amount > 10000:
            suggestions.append(("investment", 0.6))
        elif amount < 100:
            suggestions.append(("miscellaneous", 0.6))

        return suggestions

    def _rank_suggestions(self, suggestions: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Rank and deduplicate suggestions."""
        # Group by suggestion text and take max confidence
        suggestion_dict: dict[str, float] = {}
        for suggestion, confidence in suggestions:
            if suggestion in suggestion_dict:
                suggestion_dict[suggestion] = max(suggestion_dict[suggestion], confidence)
            else:
                suggestion_dict[suggestion] = confidence

        # Convert back to list and sort by confidence
        ranked = list(suggestion_dict.items())
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def _extract_merchant_name(self, description: str) -> str:
        """Extract merchant name from transaction description."""
        # Simple extraction - could be enhanced
        words = description.split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                return word.title()
        return "merchant"

    def _create_transaction_hash(self, transaction: Dict[str, Any]) -> str:
        """Create hash for transaction (similar to existing implementation)."""
        # Simplified version - should match the existing hash implementation
        description = str(transaction.get("description", ""))
        amount = str(transaction.get("debit_amount") or transaction.get("credit_amount") or 0)
        date = str(transaction.get("transaction_date", ""))

        hash_string = f"{description}_{amount}_{date}"
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _update_learning_data(self, feedback_data: Dict[str, Any]):
        """Update internal learning data with new feedback."""
        self._training_data.append(feedback_data)

    def _retrain_models(self):
        """Retrain ML models with accumulated feedback data."""
        if len(self._training_data) < 5:  # Need minimum data
            return

        # Prepare training data
        descriptions = []
        categories = []

        for data in self._training_data:
            if data["user_action"] == "accepted" and data["suggestion_type"] == "category":
                # Extract description from features
                _features = json.loads(data["features_used"])
                # For now, skip complex feature reconstruction
                continue

        # Train if we have enough data
        if len(descriptions) >= 5:
            try:
                self.category_classifier.fit(descriptions, categories)
                self._models_trained = True
            except (ValueError, AttributeError):
                # Training failed
                pass

    def _get_historical_confidence(
        self, _transaction: Dict[str, Any], _suggestion: str, _suggestion_type: str
    ) -> float:
        """Get confidence based on historical success."""
        # Default implementation - would query database in real implementation
        return 0.5

    def _calculate_feature_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence based on feature strength."""
        # Simple heuristic based on feature completeness
        total_features = len(features)
        non_zero_features = sum(
            1 for value in features.values() if value and value != 0 and value is not False
        )

        if total_features == 0:
            return 0.5

        completeness_ratio = non_zero_features / total_features
        return min(1.0, 0.3 + completeness_ratio * 0.7)

    def _calculate_similarity_confidence(
        self, _transaction: Dict[str, Any], _suggestion: str
    ) -> float:
        """Calculate confidence based on similarity to known patterns."""
        # Default implementation
        return 0.5
