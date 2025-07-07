"""
Similarity engine for fuzzy matching and semantic similarity.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..utils.ml_config import MLConfig


class SimilarityEngine:
    """Fuzzy matching and semantic similarity for transaction categorization."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize similarity engine with configuration."""
        self.config = config or MLConfig.get_default_config()["ml"]
        self.fuzzy_threshold = self.config["similarity"]["fuzzy_threshold"]
        self.cosine_threshold = self.config["similarity"]["cosine_threshold"]

        # Initialize TF-IDF vectorizer
        tfidf_config = self.config["models"]["tfidf"]
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=tfidf_config["max_features"],
            min_df=tfidf_config["min_df"],
            max_df=tfidf_config["max_df"],
            ngram_range=tfidf_config["ngram_range"],
            lowercase=True,
            stop_words="english",
        )
        self._tfidf_fitted = False

    def find_similar_descriptions(
        self, target_description: str, candidate_descriptions: List[str]
    ) -> List[Tuple[str, float]]:
        """Find similar descriptions using fuzzy matching."""
        if not target_description or not candidate_descriptions:
            return []

        target_clean = self._clean_description(target_description)
        similarities = []

        for candidate in candidate_descriptions:
            candidate_clean = self._clean_description(candidate)

            # Calculate different similarity scores
            ratio_score = fuzz.ratio(target_clean, candidate_clean) / 100.0
            partial_score = fuzz.partial_ratio(target_clean, candidate_clean) / 100.0
            token_sort_score = fuzz.token_sort_ratio(target_clean, candidate_clean) / 100.0

            # Use the maximum score
            max_score = max(ratio_score, partial_score, token_sort_score)

            if max_score >= self.fuzzy_threshold:
                similarities.append((candidate, max_score))

        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

    def find_similar_merchants(
        self, target_description: str, known_merchants: Dict[str, str]
    ) -> List[Tuple[str, str, float]]:
        """Find similar merchants from known merchant patterns."""
        if not target_description or not known_merchants:
            return []

        target_clean = self._clean_description(target_description)
        similarities = []

        for merchant_pattern, category in known_merchants.items():
            pattern_clean = self._clean_description(merchant_pattern)

            # Check if pattern is contained in description
            if pattern_clean in target_clean:
                similarities.append((merchant_pattern, category, 1.0))
                continue

            # Calculate fuzzy similarity
            ratio_score = fuzz.partial_ratio(pattern_clean, target_clean) / 100.0

            if ratio_score >= self.fuzzy_threshold:
                similarities.append((merchant_pattern, category, ratio_score))

        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[2], reverse=True)
        return similarities

    def compute_semantic_similarity(self, descriptions: List[str]) -> np.ndarray:
        """Compute semantic similarity matrix using TF-IDF and cosine similarity."""
        if len(descriptions) == 0:
            return np.array([]).reshape(0, 0)

        if len(descriptions) == 1:
            return np.array([[1.0]])

        # Clean and prepare descriptions
        clean_descriptions = self._prepare_descriptions_for_similarity(descriptions)

        # Handle identical descriptions
        if len(set(clean_descriptions)) == 1:
            size = len(clean_descriptions)
            return np.ones((size, size))

        # Compute TF-IDF similarity matrix
        return self._compute_tfidf_similarity(clean_descriptions)

    def _prepare_descriptions_for_similarity(self, descriptions: List[str]) -> List[str]:
        """Prepare descriptions for similarity computation."""
        clean_descriptions = [self._clean_description(desc) for desc in descriptions]

        # Handle empty descriptions by padding with placeholder
        padded_descriptions = []
        for desc in clean_descriptions:
            if desc.strip():
                padded_descriptions.append(desc)
            else:
                padded_descriptions.append("empty")

        return padded_descriptions

    def _compute_tfidf_similarity(self, clean_descriptions: List[str]) -> np.ndarray:
        """Compute TF-IDF based similarity matrix."""
        # Fit TF-IDF if needed
        if not self._tfidf_fitted or len(clean_descriptions) > 1:
            try:
                self.tfidf_vectorizer.fit(clean_descriptions)
                self._tfidf_fitted = True
            except ValueError:
                # Handle case where vocabulary is empty
                size = len(clean_descriptions)
                return np.ones((size, size))

        try:
            # Transform descriptions to TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.transform(clean_descriptions)

            # Compute cosine similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Fix any zero diagonals
            for i in range(similarity_matrix.shape[0]):
                if similarity_matrix[i, i] == 0:
                    similarity_matrix[i, i] = 1.0

            return similarity_matrix
        except ValueError:
            # Fallback to identity matrix if TF-IDF fails
            size = len(clean_descriptions)
            return np.eye(size)

    def find_semantic_matches(
        self, target_description: str, candidate_descriptions: List[str]
    ) -> List[Tuple[str, float]]:
        """Find semantically similar descriptions using TF-IDF and cosine similarity."""
        if not target_description or not candidate_descriptions:
            return []

        all_descriptions = [target_description] + candidate_descriptions
        similarity_matrix = self.compute_semantic_similarity(all_descriptions)

        # Extract similarities with target (first row, excluding self-similarity)
        target_similarities = similarity_matrix[0, 1:]

        matches = []
        for i, similarity in enumerate(target_similarities):
            if similarity >= self.cosine_threshold:
                matches.append((candidate_descriptions[i], similarity))

        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def extract_common_patterns(self, descriptions: List[str]) -> List[str]:
        """Extract common patterns from a list of descriptions."""
        if len(descriptions) < 2:
            return []

        # Clean descriptions
        clean_descriptions = [self._clean_description(desc) for desc in descriptions]

        # Find common words
        word_sets = [set(desc.split()) for desc in clean_descriptions]
        common_words = set.intersection(*word_sets) if word_sets else set()

        # Find common patterns using regex
        common_patterns = []

        for desc in clean_descriptions:
            # Extract potential patterns (words with numbers, specific formats)
            patterns = re.findall(r"\b\w*\d+\w*\b", desc)  # Words with numbers
            patterns += re.findall(r"\b[a-z]+@[a-z]+\b", desc)  # Email-like patterns
            common_patterns.extend(patterns)

        # Count pattern occurrences
        pattern_counts = {}
        for pattern in common_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Return patterns that appear in multiple descriptions
        min_occurrences = max(2, len(descriptions) // 2)
        frequent_patterns = [
            pattern for pattern, count in pattern_counts.items() if count >= min_occurrences
        ]

        return list(set(list(common_words) + frequent_patterns))

    def suggest_regex_pattern(self, descriptions: List[str]) -> Optional[str]:
        """Suggest a regex pattern that matches the given descriptions."""
        if not descriptions:
            return None

        common_patterns = self.extract_common_patterns(descriptions)

        if not common_patterns:
            return None

        # Create a simple regex pattern from common elements
        # This is a basic implementation - could be enhanced
        if len(common_patterns) == 1:
            pattern = common_patterns[0]
            # Escape special regex characters
            escaped_pattern = re.escape(pattern.lower())
            return f".*{escaped_pattern}.*"

        # Create an OR pattern for multiple common elements
        escaped_patterns = [re.escape(p.lower()) for p in common_patterns[:3]]  # Limit to 3
        return f".*({'|'.join(escaped_patterns)}).*"

    def _clean_description(self, description: str) -> str:
        """Clean and normalize description text."""
        if not description:
            return ""

        # Convert to lowercase
        clean = description.lower().strip()

        # Remove extra whitespace
        clean = re.sub(r"\s+", " ", clean)

        # Remove common noise words
        noise_words = ["payment", "transaction", "transfer", "upi", "neft", "imps"]
        for noise in noise_words:
            clean = clean.replace(noise, " ")

        # Remove extra whitespace again
        clean = re.sub(r"\s+", " ", clean).strip()

        return clean

    def calculate_merchant_confidence(
        self, _description: str, historical_matches: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for merchant identification based on historical data."""
        if not historical_matches:
            return 0.5  # Default confidence

        # Calculate confidence based on:
        # 1. Number of historical matches
        # 2. Similarity scores
        # 3. Recency of matches

        total_confidence = 0.0
        weight_sum = 0.0

        for match in historical_matches:
            similarity = match.get("similarity", 0.5)
            recency_weight = match.get("recency_weight", 1.0)  # Higher for recent matches
            success_rate = match.get("success_rate", 0.5)

            confidence = similarity * success_rate
            weight = recency_weight

            total_confidence += confidence * weight
            weight_sum += weight

        if weight_sum == 0:
            return 0.5

        final_confidence = total_confidence / weight_sum

        # Boost confidence if we have many matches
        boost_factor = min(1.2, 1.0 + len(historical_matches) * 0.05)
        final_confidence *= boost_factor

        return min(1.0, max(0.1, final_confidence))  # Clamp between 0.1 and 1.0
