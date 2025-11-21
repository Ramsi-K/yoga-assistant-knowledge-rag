"""
Test script for Grafana dashboard.

This script:
1. Generates sample conversation data
2. Verifies database connectivity
3. Checks that all dashboard queries work correctly

Usage:
    python grafana/test_dashboard.py
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path to import yoga_assistant modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yoga_assistant import db

# Load environment variables
load_dotenv()


# Sample data for testing
SAMPLE_QUESTIONS = [
    "What are the benefits of Downward-Facing Dog?",
    "How do I do a proper Tree Pose?",
    "What poses are good for beginners?",
    "Tell me about breathing techniques in yoga",
    "What are contraindications for headstand?",
    "How long should I hold Warrior II?",
    "What modifications exist for Child's Pose?",
    "Which poses help with back pain?",
    "What is the sanskrit name for Mountain Pose?",
    "How do I sequence a morning yoga practice?",
]

SAMPLE_ANSWERS = [
    "Downward-Facing Dog strengthens the arms and legs while stretching the hamstrings and calves. It also helps improve circulation and energizes the body.",
    "To perform Tree Pose, stand on one leg, place the other foot on your inner thigh or calf (not the knee), and bring your hands to prayer position at your chest or overhead.",
    "Great beginner poses include Mountain Pose, Child's Pose, Cat-Cow, and Downward-Facing Dog. These help build foundational strength and flexibility.",
    "Pranayama, or breath control, is essential in yoga. Common techniques include Ujjayi breath (ocean breath), alternate nostril breathing, and three-part breath.",
    "Headstand should be avoided if you have neck injuries, high blood pressure, glaucoma, or are pregnant. Always practice with proper guidance.",
    "Warrior II is typically held for 5-10 breaths (30-60 seconds) on each side. Focus on maintaining proper alignment throughout.",
    "Child's Pose can be modified by placing a bolster under your torso, widening your knees, or using a blanket under your knees for comfort.",
    "Poses that help with back pain include Cat-Cow, Child's Pose, Sphinx Pose, and gentle twists. Always consult a healthcare provider for persistent pain.",
    "The sanskrit name for Mountain Pose is Tadasana. It's a foundational standing pose that improves posture and body awareness.",
    "A morning sequence might include: Sun Salutations, standing poses like Warrior I and II, balancing poses like Tree, and ending with Savasana for relaxation.",
]

SAMPLE_MODELS = [
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-V3",
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
]

RELEVANCE_OPTIONS = [
    "RELEVANT",
    "RELEVANT",
    "RELEVANT",
    "PARTLY_RELEVANT",
    "NON_RELEVANT",
]


def generate_sample_conversations(count: int = 20) -> int:
    """
    Generate sample conversation data for testing.

    Args:
        count: Number of conversations to generate

    Returns:
        Number of conversations successfully created
    """
    print(f"\nGenerating {count} sample conversations...")

    created = 0
    base_time = datetime.now() - timedelta(days=7)

    for i in range(count):
        # Generate random data
        question = random.choice(SAMPLE_QUESTIONS)
        answer = random.choice(SAMPLE_ANSWERS)
        model = random.choice(SAMPLE_MODELS)
        relevance = random.choice(RELEVANCE_OPTIONS)

        # Simulate realistic metrics
        response_time_ms = random.randint(1000, 8000)
        tokens_used = random.randint(200, 1500)
        cost_usd = tokens_used * 0.000001  # Rough estimate

        # Spread timestamps over the last 7 days
        timestamp_offset = timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        # Create sample retrieved docs
        retrieved_docs = [
            {
                "id": random.randint(1, 100),
                "pose_name": "Sample Pose",
                "score": random.uniform(0.7, 1.0),
            }
            for _ in range(random.randint(3, 5))
        ]

        try:
            conversation_id = db.log_conversation(
                question=question,
                answer=answer,
                model=model,
                retrieved_docs=retrieved_docs,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                relevance=relevance,
                cost_usd=cost_usd,
            )

            # Add feedback to some conversations (about 60%)
            if random.random() < 0.6:
                feedback = 1 if random.random() < 0.75 else -1  # 75% positive
                db.update_feedback(conversation_id, feedback)

            created += 1
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{count} conversations...")

        except Exception as e:
            print(f"  Error creating conversation {i + 1}: {str(e)}")

    print(f"✓ Successfully created {created}/{count} conversations")
    return created


def verify_database_queries() -> bool:
    """
    Verify that all database queries used by the dashboard work correctly.

    Returns:
        True if all queries work, False otherwise
    """
    print("\nVerifying database queries...")

    tests_passed = 0
    tests_total = 7

    # Test 1: Recent conversations
    try:
        conversations = db.get_recent_conversations(limit=10)
        if isinstance(conversations, list):
            print(
                f"✓ Recent conversations query works ({len(conversations)} results)"
            )
            tests_passed += 1
        else:
            print("✗ Recent conversations query returned invalid data")
    except Exception as e:
        print(f"✗ Recent conversations query failed: {str(e)}")

    # Test 2: Feedback stats
    try:
        feedback_stats = db.get_feedback_stats()
        if isinstance(feedback_stats, dict) and "positive" in feedback_stats:
            print(
                f"✓ Feedback stats query works (positive: {feedback_stats['positive']}, negative: {feedback_stats['negative']})"
            )
            tests_passed += 1
        else:
            print("✗ Feedback stats query returned invalid data")
    except Exception as e:
        print(f"✗ Feedback stats query failed: {str(e)}")

    # Test 3: Relevance stats
    try:
        relevance_stats = db.get_relevance_stats()
        if (
            isinstance(relevance_stats, dict)
            and "relevant_percentage" in relevance_stats
        ):
            print(
                f"✓ Relevance stats query works ({relevance_stats['relevant_percentage']:.1f}% relevant)"
            )
            tests_passed += 1
        else:
            print("✗ Relevance stats query returned invalid data")
    except Exception as e:
        print(f"✗ Relevance stats query failed: {str(e)}")

    # Test 4: Cost over time
    try:
        cost_data = db.get_cost_over_time(days=7)
        if isinstance(cost_data, list):
            print(
                f"✓ Cost over time query works ({len(cost_data)} data points)"
            )
            tests_passed += 1
        else:
            print("✗ Cost over time query returned invalid data")
    except Exception as e:
        print(f"✗ Cost over time query failed: {str(e)}")

    # Test 5: Token usage over time
    try:
        token_data = db.get_token_usage_over_time(days=7)
        if isinstance(token_data, list):
            print(
                f"✓ Token usage over time query works ({len(token_data)} data points)"
            )
            tests_passed += 1
        else:
            print("✗ Token usage over time query returned invalid data")
    except Exception as e:
        print(f"✗ Token usage over time query failed: {str(e)}")

    # Test 6: Response time stats
    try:
        response_time_data = db.get_response_time_stats(days=7)
        if isinstance(response_time_data, list):
            print(
                f"✓ Response time stats query works ({len(response_time_data)} data points)"
            )
            tests_passed += 1
        else:
            print("✗ Response time stats query returned invalid data")
    except Exception as e:
        print(f"✗ Response time stats query failed: {str(e)}")

    # Test 7: Model usage stats
    try:
        model_stats = db.get_model_usage_stats()
        if isinstance(model_stats, list):
            print(
                f"✓ Model usage stats query works ({len(model_stats)} models)"
            )
            tests_passed += 1
        else:
            print("✗ Model usage stats query returned invalid data")
    except Exception as e:
        print(f"✗ Model usage stats query failed: {str(e)}")

    print(f"\nQuery verification: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def display_summary_stats():
    """
    Display summary statistics from the database.
    """
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    try:
        # Get recent conversations count
        conversations = db.get_recent_conversations(limit=1000)
        print(f"\nTotal conversations: {len(conversations)}")

        # Get feedback stats
        feedback_stats = db.get_feedback_stats()
        print(f"\nFeedback:")
        print(f"  Positive: {feedback_stats['positive']}")
        print(f"  Negative: {feedback_stats['negative']}")
        if feedback_stats["total"] > 0:
            positive_pct = (
                feedback_stats["positive"] / feedback_stats["total"] * 100
            )
            print(f"  Positive rate: {positive_pct:.1f}%")

        # Get relevance stats
        relevance_stats = db.get_relevance_stats()
        print(f"\nRelevance:")
        print(f"  Relevant: {relevance_stats['relevant']}")
        print(f"  Partly relevant: {relevance_stats['partly_relevant']}")
        print(f"  Non-relevant: {relevance_stats['non_relevant']}")
        print(
            f"  Relevant percentage: {relevance_stats['relevant_percentage']:.1f}%"
        )

        # Get model usage
        model_stats = db.get_model_usage_stats()
        print(f"\nModel usage:")
        for model in model_stats:
            print(f"  {model['model']}: {model['usage_count']} queries")

    except Exception as e:
        print(f"Error displaying summary: {str(e)}")


def main():
    """
    Main function to test the Grafana dashboard.

    Steps:
    1. Verify database connection
    2. Generate sample conversation data
    3. Verify all dashboard queries work
    4. Display summary statistics
    """
    print("=" * 60)
    print("Yoga Assistant - Grafana Dashboard Test")
    print("=" * 60)

    # Test database connection
    print("\nTesting database connection...")
    try:
        conn = db.get_db_connection()
        conn.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database schema is initialized (run db_prep.py)")
        print("  3. Environment variables are set correctly")
        sys.exit(1)

    # Generate sample data
    created = generate_sample_conversations(count=20)
    if created == 0:
        print("\n✗ Failed to create any sample conversations")
        sys.exit(1)

    # Verify queries
    if not verify_database_queries():
        print("\n✗ Some dashboard queries failed")
        print("  The dashboard may not display correctly")
        sys.exit(1)

    # Display summary
    display_summary_stats()

    # Success message
    print("\n" + "=" * 60)
    print("✓ Dashboard test complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start Grafana: docker-compose up grafana")
    print("  2. Run init script: python grafana/init.py")
    print("  3. Open dashboard: http://localhost:3000/d/yoga-rag-dashboard")
    print("  4. Login with admin/admin")
    print()


if __name__ == "__main__":
    main()
