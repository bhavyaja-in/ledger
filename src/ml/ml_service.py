"""
ML suggestion service for transaction categorization.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .models.transaction_classifier import TransactionClassifier
from .utils.ml_config import MLConfig


__all__ = ["MLSuggestionService"]


class MLSuggestionService:
    """Service that provides ML-powered suggestions for transaction categorization."""

    def __init__(self, db_manager=None, config=None):
        """Initialize ML suggestion service."""
        self.db_manager = db_manager
        self.config = config or {}

        # Check if ML is enabled
        self.ml_enabled = self.config.get("ml", {}).get("enabled", True)

        if self.ml_enabled:
            # Initialize ML classifier
            ml_config = self.config.get("ml", MLConfig.get_default_config()["ml"])
            self.classifier = TransactionClassifier(db_manager, ml_config)
        else:
            self.classifier = None

    def suggest_regex_pattern(
        self, description: str, similar_descriptions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Suggest regex pattern for transaction description."""
        if not self.ml_enabled or not self.classifier:
            return None

        descriptions = [description]
        if similar_descriptions:
            descriptions.extend(similar_descriptions)

        pattern = self.classifier.similarity_engine.suggest_regex_pattern(descriptions)

        if pattern:
            confidence = self._calculate_pattern_confidence(pattern, descriptions)
            return {
                "pattern": pattern,
                "confidence": confidence,
                "reasoning": f"Pattern derived from {len(descriptions)} similar transaction(s)",
                "source": "ml_analysis",
            }

        return None

    def suggest_enum_category(
        self, description: str, existing_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Suggest enum category based on transaction description."""
        if not self.ml_enabled or not self.classifier:
            return []

        # Extract meaningful patterns
        patterns = self.classifier.feature_extractor.extract_text_patterns(description)

        suggestions = []

        # Use pattern-based suggestions
        for pattern in patterns[:3]:  # Top 3 patterns
            if len(pattern) >= 3:
                confidence = 0.7 if len(pattern) > 5 else 0.5
                suggestions.append(
                    {
                        "category": self._infer_category_from_pattern(pattern),
                        "confidence": confidence,
                        "reasoning": f"Pattern '{pattern}' extracted from transaction description",
                        "source": "pattern_analysis",
                    }
                )

        # Use similarity-based suggestions if we have existing patterns
        if existing_patterns:
            similar_matches = self.classifier.similarity_engine.find_similar_descriptions(
                description, existing_patterns
            )

            for match, similarity in similar_matches[:2]:  # Top 2 matches
                suggestions.append(
                    {
                        "category": self._infer_category_from_pattern(match),
                        "confidence": similarity * 0.8,  # Reduce confidence for similarity-based
                        "reasoning": f"Similar to existing pattern '{match}' ({similarity:.2f} similarity)",
                        "source": "similarity_analysis",
                    }
                )

        def _sort_key(suggestion: Dict[str, Any]) -> float:
            return float(suggestion["confidence"])

        return sorted(suggestions, key=_sort_key, reverse=True)[:3]

    def suggest_transaction_category(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest transaction category based on complete transaction context."""
        if not self.ml_enabled or not self.classifier:
            return []

        category_suggestions = self.classifier.suggest_category(transaction)

        suggestions = []
        for category, confidence in category_suggestions:
            suggestions.append(
                {
                    "category": category,
                    "confidence": confidence,
                    "reasoning": self._generate_category_reasoning(transaction, category),
                    "source": "ml_classification",
                }
            )

        return suggestions

    def suggest_transaction_reason(
        self, transaction: Dict[str, Any], category: str
    ) -> List[Dict[str, Any]]:
        """Suggest transaction reason based on context and category."""
        if not self.ml_enabled or not self.classifier:
            return []

        reason_suggestions = self.classifier.suggest_reason(transaction, category)

        suggestions = []
        for reason, confidence in reason_suggestions:
            suggestions.append(
                {
                    "reason": reason,
                    "confidence": confidence,
                    "reasoning": f"Generated based on transaction context and '{category}' category",
                    "source": "template_generation",
                }
            )

        return suggestions

    def provide_feedback(
        self,
        transaction: Dict[str, Any],
        suggestion_type: str,
        suggested_value: str,
        user_action: str,
        *,
        final_value: Optional[str] = None,
    ):
        """Provide feedback to ML system for continuous learning."""
        if not self.ml_enabled or not self.classifier:
            return

        self.classifier.learn_from_feedback(
            transaction=transaction,
            suggestion_type=suggestion_type,
            suggested_value=suggested_value,
            user_action=user_action,
            final_value=final_value,
        )

    def suggest_category(self, transaction: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Suggest categories for transaction (simplified interface)."""
        suggestions = self.suggest_transaction_category(transaction)
        return [(s["category"], s["confidence"]) for s in suggestions]

    def get_suggestion_summary(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive ML suggestions for a transaction."""
        summary = {
            "ml_enabled": self.ml_enabled,
            "suggestions": {
                "category": [],
                "reason": [],
                "enum_category": [],
                "regex_pattern": None,
            },
            "confidence_overall": 0.0,
        }

        if not self.ml_enabled:
            return summary

        description = str(transaction.get("description", ""))

        # Get category suggestions
        category_suggestions = self.suggest_transaction_category(transaction)
        summary["suggestions"]["category"] = category_suggestions

        # Get enum category suggestions
        enum_suggestions = self.suggest_enum_category(description)
        summary["suggestions"]["enum_category"] = enum_suggestions

        # Get regex pattern suggestion
        pattern_suggestion = self.suggest_regex_pattern(description)
        summary["suggestions"]["regex_pattern"] = pattern_suggestion

        # Get reason suggestions for top category if available
        if category_suggestions:
            top_category = category_suggestions[0]["category"]
            reason_suggestions = self.suggest_transaction_reason(transaction, top_category)
            summary["suggestions"]["reason"] = reason_suggestions

        # Calculate overall confidence
        all_confidences = []
        for suggestions in [category_suggestions, enum_suggestions]:
            if suggestions:
                all_confidences.extend([s["confidence"] for s in suggestions])

        if pattern_suggestion:
            all_confidences.append(pattern_suggestion["confidence"])

        if all_confidences:
            summary["confidence_overall"] = sum(all_confidences) / len(all_confidences)

        return summary

    def _calculate_pattern_confidence(self, pattern: str, descriptions: List[str]) -> float:
        """Calculate confidence for a regex pattern."""
        try:
            # Test pattern against descriptions
            matches = 0
            for desc in descriptions:
                if re.search(pattern, desc.lower()):
                    matches += 1

            match_ratio = matches / len(descriptions) if descriptions else 0

            # Base confidence on match ratio and pattern complexity
            pattern_complexity = len(pattern.replace(".*", "").replace("|", ""))
            complexity_bonus = min(0.2, pattern_complexity * 0.01)

            confidence = match_ratio * 0.8 + complexity_bonus
            return min(1.0, max(0.1, confidence))

        except (ValueError, TypeError, re.error):
            return 0.3  # Default low confidence for invalid patterns

    def _infer_category_from_pattern(self, pattern: str) -> str:
        """Infer category from pattern using enhanced contextual analysis."""
        pattern_lower = pattern.lower().strip()

        # Enhanced category keywords mapping with priority scoring
        category_keywords = {
            "food": {
                "high": ["swiggy", "zomato", "dominos", "mcdonalds", "kfc", "subway", "pizzahut"],
                "medium": ["food", "restaurant", "cafe", "kitchen", "meal", "dining", "bakery"],
                "low": ["pizza", "burger", "coffee"],
            },
            "transport": {
                "high": ["uber", "ola", "rapido", "metro", "petrol", "diesel"],
                "medium": ["taxi", "auto", "bus", "train", "fuel", "parking"],
                "low": ["travel", "trip"],
            },
            "shopping": {
                "high": ["amazon", "flipkart", "myntra", "nykaa", "bigbasket"],
                "medium": ["mall", "store", "shopping", "market", "supermarket"],
                "low": ["purchase", "buy", "shop"],
            },
            "utility": {
                "high": ["electricity", "bses", "adani", "tata", "airtel", "jio", "vodafone"],
                "medium": ["water", "gas", "phone", "internet", "wifi", "broadband"],
                "low": ["bill", "payment"],
            },
            "medical": {
                "high": ["apollo", "fortis", "max", "pharmacy", "medplus"],
                "medium": ["hospital", "clinic", "doctor", "medical", "health"],
                "low": ["medicine", "checkup"],
            },
            "entertainment": {
                "high": ["netflix", "spotify", "hotstar", "prime", "youtube"],
                "medium": ["movie", "cinema", "pvr", "inox", "music"],
                "low": ["game", "fun", "entertainment"],
            },
            "finance": {
                "high": ["loan", "emi", "sip", "mutual", "insurance", "policy"],
                "medium": ["bank", "investment", "trading", "zerodha", "groww"],
                "low": ["finance", "money"],
            },
            "education": {
                "high": ["byju", "unacademy", "vedantu", "coursera"],
                "medium": ["school", "college", "university", "course", "fees"],
                "low": ["education", "learning", "study"],
            },
            "salary": {
                "high": ["salary", "payroll", "wages"],
                "medium": ["income", "company", "employer"],
                "low": ["work"],
            },
        }

        # Calculate category scores based on pattern matching
        category_scores = {}
        for category, priority_keywords in category_keywords.items():
            score = 0
            for priority, keywords in priority_keywords.items():
                for keyword in keywords:
                    if keyword in pattern_lower:
                        # Higher scores for exact matches and higher priority keywords
                        base_score = 3 if priority == "high" else 2 if priority == "medium" else 1
                        if pattern_lower == keyword:  # Exact match
                            score += base_score * 2
                        elif keyword in pattern_lower:  # Partial match
                            score += base_score
            if score > 0:
                category_scores[category] = score

        # Return category with highest score, or fallback analysis
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category

        # Fallback analysis for common patterns
        if any(keyword in pattern_lower for keyword in ["transfer", "friend", "family"]):
            return "transfer"
        if any(keyword in pattern_lower for keyword in ["atm", "withdrawal", "cash"]):
            return "cash"

        return "miscellaneous"

    def _generate_category_reasoning(self, transaction: Dict[str, Any], category: str) -> str:
        """Generate enhanced reasoning for why a category was suggested."""
        description = str(transaction.get("description", "")).lower()
        amount = float(transaction.get("debit_amount") or transaction.get("credit_amount") or 0)

        reasons = []

        # Enhanced description-based reasoning with specific brand/service detection
        category_detectors = {
            "food": {
                "swiggy": "Swiggy food delivery service",
                "zomato": "Zomato food delivery service",
                "dominos": "Domino's pizza order",
                "mcdonalds": "McDonald's restaurant",
                "kfc": "KFC restaurant",
                "restaurant": "restaurant transaction",
                "food": "food-related transaction",
            },
            "transport": {
                "uber": "Uber ride booking",
                "ola": "Ola cab service",
                "metro": "metro/subway transportation",
                "petrol": "fuel purchase",
                "diesel": "fuel purchase",
                "parking": "parking payment",
            },
            "shopping": {
                "amazon": "Amazon online purchase",
                "flipkart": "Flipkart online shopping",
                "myntra": "Myntra fashion purchase",
                "bigbasket": "BigBasket grocery order",
                "mall": "shopping mall purchase",
            },
            "utility": {
                "electricity": "electricity bill payment",
                "airtel": "Airtel telecom service",
                "jio": "Jio telecom service",
                "vodafone": "Vodafone telecom service",
                "bses": "BSES electricity bill",
                "adani": "Adani utilities payment",
            },
            "entertainment": {
                "netflix": "Netflix subscription",
                "spotify": "Spotify music streaming",
                "hotstar": "Disney+ Hotstar subscription",
                "prime": "Amazon Prime subscription",
                "movie": "movie/cinema ticket",
            },
            "medical": {
                "apollo": "Apollo Hospitals",
                "fortis": "Fortis Healthcare",
                "pharmacy": "pharmacy purchase",
                "medplus": "MedPlus medical store",
            },
            "finance": {
                "loan": "loan payment",
                "emi": "EMI payment",
                "sip": "mutual fund SIP",
                "insurance": "insurance premium",
                "zerodha": "Zerodha trading platform",
            },
        }

        # Check for specific brand/service mentions
        if category in category_detectors:
            for keyword, reason in category_detectors[category].items():
                if keyword in description:
                    reasons.append(reason + " identified")
                    break

        # Amount-based contextual reasoning
        if amount > 50000:
            reasons.append("high-value transaction suggests major expense")
        elif amount > 10000:
            reasons.append("significant amount indicates important purchase")
        elif amount > 1000:
            reasons.append("moderate amount suggests regular expense")
        elif amount > 100:
            reasons.append("small to medium transaction")
        elif amount > 0:
            reasons.append("micro-transaction or minimal expense")

        # Transaction type reasoning
        if transaction.get("debit_amount"):
            reasons.append("outgoing payment")
        elif transaction.get("credit_amount"):
            reasons.append("incoming payment")

        # Time-based reasoning could be added here (weekday vs weekend, time of day)

        # Pattern-based reasoning
        if "upi" in description:
            reasons.append("UPI digital payment")
        if any(term in description for term in ["transfer", "friend", "family"]):
            reasons.append("personal transfer detected")

        # Default reasoning with confidence indication
        if not reasons:
            reasons.append(f"ML pattern analysis suggests {category} category")

        return "; ".join(reasons).capitalize()
