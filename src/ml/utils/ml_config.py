"""
ML Configuration for transaction categorization system.
"""

from typing import Dict, Any


class MLConfig:
    """Configuration class for ML features and hyperparameters."""

    # Feature Engineering Settings
    MIN_PATTERN_LENGTH = 3
    MAX_PATTERN_LENGTH = 50
    MIN_DESCRIPTION_LENGTH = 5

    # Similarity Thresholds
    FUZZY_MATCH_THRESHOLD = 0.8
    COSINE_SIMILARITY_THRESHOLD = 0.7

    # Learning Parameters
    CONFIDENCE_THRESHOLD = 0.6
    FEEDBACK_WEIGHT = 1.5
    DECAY_FACTOR = 0.95

    # TF-IDF Parameters
    MAX_FEATURES = 1000
    MIN_DF = 2
    MAX_DF = 0.8
    NGRAM_RANGE = (1, 2)

    # Model Settings
    NAIVE_BAYES_ALPHA = 1.0
    MAX_SUGGESTIONS = 5

    # Temporal Settings
    SHORT_TERM_DAYS = 30
    SEASONAL_PATTERN_MONTHS = 12

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default ML configuration."""
        return {
            "ml": {
                "enabled": True,
                "confidence_threshold": cls.CONFIDENCE_THRESHOLD,
                "max_suggestions": cls.MAX_SUGGESTIONS,
                "feature_extraction": {
                    "min_pattern_length": cls.MIN_PATTERN_LENGTH,
                    "max_pattern_length": cls.MAX_PATTERN_LENGTH,
                    "min_description_length": cls.MIN_DESCRIPTION_LENGTH,
                },
                "similarity": {
                    "fuzzy_threshold": cls.FUZZY_MATCH_THRESHOLD,
                    "cosine_threshold": cls.COSINE_SIMILARITY_THRESHOLD,
                },
                "learning": {
                    "feedback_weight": cls.FEEDBACK_WEIGHT,
                    "decay_factor": cls.DECAY_FACTOR,
                    "short_term_days": cls.SHORT_TERM_DAYS,
                },
                "models": {
                    "naive_bayes_alpha": cls.NAIVE_BAYES_ALPHA,
                    "tfidf": {
                        "max_features": cls.MAX_FEATURES,
                        "min_df": cls.MIN_DF,
                        "max_df": cls.MAX_DF,
                        "ngram_range": cls.NGRAM_RANGE,
                    },
                },
            }
        }
