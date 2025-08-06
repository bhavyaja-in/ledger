#!/usr/bin/env python3
"""
Demo script for ML-powered transaction categorization.

This script demonstrates the ML capabilities implemented for
contextual transaction categorization with continuous learning.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ml.ml_service import MLSuggestionService
from src.ml.utils.ml_config import MLConfig


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_feature_extraction():
    """Demonstrate feature extraction capabilities."""
    print_separator("🔍 FEATURE EXTRACTION DEMO")

    from src.ml.features.transaction_features import TransactionFeatures

    feature_extractor = TransactionFeatures()

    sample_transaction = {
        "description": "UPI-SWIGGY-DELIVERY-9876543210@paytm",
        "debit_amount": 250.50,
        "transaction_date": datetime(2024, 1, 15, 12, 30),
        "reference_number": "REF123456789",
    }

    print("📝 Sample Transaction:")
    print(f"   Description: {sample_transaction['description']}")
    print(f"   Amount: ₹{sample_transaction['debit_amount']}")
    print(f"   Date: {sample_transaction['transaction_date']}")

    # Extract features
    features = feature_extractor.combine_features(sample_transaction)

    print("\n🎯 Extracted Features:")
    print(f"   Description Length: {features['description_length']}")
    print(f"   Word Count: {features['word_count']}")
    print(f"   Amount (log): {features['amount_log']:.2f}")
    print(f"   Day of Week: {features['day_of_week']} (Monday=0)")
    print(f"   Is Food Merchant: {features['is_food']}")
    print(f"   Has Numbers: {features['has_numbers']}")

    print("\n🔤 Text Patterns Detected:")
    for pattern in features["text_patterns"][:5]:
        print(f"   • {pattern}")


def demo_similarity_engine():
    """Demonstrate similarity engine capabilities."""
    print_separator("🔗 SIMILARITY ENGINE DEMO")

    from src.ml.models.similarity_engine import SimilarityEngine

    engine = SimilarityEngine()

    target = "UPI-SWIGGY-DELIVERY-NEW-ORDER"
    candidates = [
        "UPI-SWIGGY-FOOD-DELIVERY",
        "UPI-ZOMATO-ORDER-PAYMENT",
        "UPI-SWIGGY-RESTAURANT-BILL",
        "BANK-TRANSFER-TO-FRIEND",
        "UPI-UBER-RIDE-BOOKING",
    ]

    print("🎯 Target Transaction:")
    print(f"   {target}")

    print("\n📋 Candidate Transactions:")
    for i, candidate in enumerate(candidates, 1):
        print(f"   {i}. {candidate}")

    # Find similar descriptions
    similar = engine.find_similar_descriptions(target, candidates)

    print("\n🔍 Similarity Results:")
    for desc, score in similar:
        print(f"   • {desc} (similarity: {score:.2f})")

    # Suggest regex pattern
    similar_descriptions = [target] + [desc for desc, _ in similar[:2]]
    pattern = engine.suggest_regex_pattern(similar_descriptions)

    if pattern:
        print("\n🎨 Suggested Regex Pattern:")
        print(f"   {pattern}")


def demo_ml_suggestions():
    """Demonstrate ML-powered suggestions."""
    print_separator("🤖 ML SUGGESTION DEMO")

    config = MLConfig.get_default_config()
    ml_service = MLSuggestionService(None, config)

    sample_transactions = [
        {
            "description": "UPI-SWIGGY-DELIVERY-ORDER-12345@paytm",
            "debit_amount": 350.00,
            "transaction_date": "2024-01-15 13:30:00",
        },
        {
            "description": "UPI-UBER-RIDE-BOOKING-AIRPORT@paytm",
            "debit_amount": 450.00,
            "transaction_date": "2024-01-15 18:00:00",
        },
        {
            "description": "AMAZON-PURCHASE-ELECTRONICS-ORDER",
            "debit_amount": 2999.00,
            "transaction_date": "2024-01-16 10:15:00",
        },
    ]

    for i, transaction in enumerate(sample_transactions, 1):
        print(f"\n🏷️  Transaction {i}:")
        print(f"   Description: {transaction['description']}")
        print(f"   Amount: ₹{transaction['debit_amount']}")

        # Get comprehensive suggestions
        summary = ml_service.get_suggestion_summary(transaction)

        print(f"   Overall Confidence: {summary['confidence_overall']:.2f}")

        # Category suggestions
        if summary["suggestions"]["category"]:
            print("   🎯 Category Suggestions:")
            for suggestion in summary["suggestions"]["category"][:3]:
                print(
                    f"      • {suggestion['category'].title()} "
                    f"({suggestion['confidence']:.2f} confidence)"
                )
                print(f"        Reason: {suggestion['reasoning']}")

        # Enum category suggestions
        if summary["suggestions"]["enum_category"]:
            print("   🏷️  Enum Category Suggestions:")
            for suggestion in summary["suggestions"]["enum_category"][:2]:
                print(
                    f"      • {suggestion['category'].title()} "
                    f"({suggestion['confidence']:.2f} confidence)"
                )

        # Regex pattern suggestion
        if summary["suggestions"]["regex_pattern"]:
            pattern_info = summary["suggestions"]["regex_pattern"]
            print("   🎨 Regex Pattern Suggestion:")
            print(f"      Pattern: {pattern_info['pattern']}")
            print(f"      Confidence: {pattern_info['confidence']:.2f}")


def demo_learning_simulation():
    """Demonstrate continuous learning simulation."""
    print_separator("🧠 LEARNING SIMULATION DEMO")

    config = MLConfig.get_default_config()
    ml_service = MLSuggestionService(None, config)

    print("📚 Simulating User Feedback Learning...")

    # Simulate training data
    training_scenarios = [
        {
            "transaction": {
                "description": "UPI-SWIGGY-DELIVERY-123@paytm",
                "debit_amount": 200.0,
                "transaction_date": "2024-01-15",
            },
            "feedback": {
                "suggestion_type": "category",
                "suggested_value": "food",
                "user_action": "accepted",
                "final_value": "food",
            },
        },
        {
            "transaction": {
                "description": "UPI-UBER-TRIP-456@paytm",
                "debit_amount": 180.0,
                "transaction_date": "2024-01-15",
            },
            "feedback": {
                "suggestion_type": "category",
                "suggested_value": "transport",
                "user_action": "accepted",
                "final_value": "transport",
            },
        },
        {
            "transaction": {
                "description": "AMAZON-SHOPPING-789",
                "debit_amount": 1500.0,
                "transaction_date": "2024-01-16",
            },
            "feedback": {
                "suggestion_type": "category",
                "suggested_value": "shopping",
                "user_action": "modified",
                "final_value": "electronics",
            },
        },
    ]

    print("   Processing feedback scenarios:")
    for i, scenario in enumerate(training_scenarios, 1):
        transaction = scenario["transaction"]
        feedback = scenario["feedback"]

        print(f"   {i}. {transaction['description'][:30]}...")
        print(f"      User Action: {feedback['user_action']}")
        print(f"      Final Category: {feedback['final_value']}")

        # Provide feedback to ML system
        ml_service.provide_feedback(transaction=transaction, **feedback)

    print("\n🔮 Testing Learned Patterns:")

    # Test similar transactions
    test_transaction = {
        "description": "UPI-SWIGGY-NEW-ORDER-999@paytm",
        "debit_amount": 220.0,
        "transaction_date": "2024-01-17",
    }

    suggestions = ml_service.suggest_transaction_category(test_transaction)

    print(f"   New Transaction: {test_transaction['description']}")
    print("   ML Suggestions:")
    for suggestion in suggestions[:3]:
        print(
            f"      • {suggestion['category'].title()} "
            f"({suggestion['confidence']:.2f} confidence)"
        )


def demo_configuration():
    """Demonstrate ML configuration options."""
    print_separator("⚙️  CONFIGURATION DEMO")

    default_config = MLConfig.get_default_config()

    print("🔧 Default ML Configuration:")
    print(f"   Enabled: {default_config['ml']['enabled']}")
    print(f"   Confidence Threshold: {default_config['ml']['confidence_threshold']}")
    print(f"   Max Suggestions: {default_config['ml']['max_suggestions']}")
    print(f"   Fuzzy Match Threshold: {default_config['ml']['similarity']['fuzzy_threshold']}")
    print(
        f"   Min Pattern Length: {default_config['ml']['feature_extraction']['min_pattern_length']}"
    )

    # Show custom configuration example
    print("\n🎛️  Custom Configuration Example:")
    custom_config = {
        "ml": {
            "enabled": True,
            "confidence_threshold": 0.8,  # Higher threshold
            "max_suggestions": 3,  # Fewer suggestions
            "similarity": {"fuzzy_threshold": 0.9, "cosine_threshold": 0.8},  # Stricter matching
            "models": {
                "naive_bayes_alpha": 1.0,
                "tfidf": {
                    "max_features": 500,  # Reduced features
                    "min_df": 2,
                    "max_df": 0.8,
                    "ngram_range": [1, 2],
                },
            },
        }
    }

    print("   ```yaml")
    print("   ml:")
    print("     enabled: true")
    print("     confidence_threshold: 0.8")
    print("     max_suggestions: 3")
    print("     similarity:")
    print("       fuzzy_threshold: 0.9")
    print("   ```")

    # Test with custom config
    custom_config = MLConfig.get_default_config()
    custom_config["ml"]["confidence_threshold"] = 0.8
    custom_config["ml"]["max_suggestions"] = 3
    custom_config["ml"]["similarity"]["fuzzy_threshold"] = 0.9

    custom_service = MLSuggestionService(None, custom_config)

    test_transaction = {
        "description": "UPI-UNKNOWN-MERCHANT",
        "debit_amount": 100.0,
        "transaction_date": "2024-01-15",
    }

    default_suggestions = len(
        MLSuggestionService(None, default_config).suggest_transaction_category(test_transaction)
    )
    custom_suggestions = len(custom_service.suggest_transaction_category(test_transaction))

    print("\n📊 Suggestion Comparison:")
    print(f"   Default Config: {default_suggestions} suggestions")
    print(f"   Custom Config: {custom_suggestions} suggestions")


def main():
    """Run the complete ML demo."""
    print("🤖 ML-Powered Transaction Categorization Demo")
    print("   Demonstrating intelligent transaction processing with continuous learning")

    try:
        demo_feature_extraction()
        demo_similarity_engine()
        demo_ml_suggestions()
        demo_learning_simulation()
        demo_configuration()

        print_separator("✅ DEMO COMPLETE")
        print("🎉 All ML features demonstrated successfully!")
        print("\n📚 Key Capabilities Shown:")
        print("   • Intelligent feature extraction from transaction data")
        print("   • Fuzzy matching and semantic similarity analysis")
        print("   • AI-powered category and pattern suggestions")
        print("   • Continuous learning from user feedback")
        print("   • Flexible configuration options")
        print("   • Robust error handling and fallbacks")

        print("\n🚀 Ready for production use with the ICICI Bank transformer!")

    except Exception as error:
        print(f"\n❌ Demo failed with error: {error}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
