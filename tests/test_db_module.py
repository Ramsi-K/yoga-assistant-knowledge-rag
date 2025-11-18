"""
Test script for database module.

Note: This test requires a running PostgreSQL database with credentials
configured in .env file. It will not run in CI without database setup.
"""

import sys
from pathlib import Path

# Add yoga_assistant to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing database module...\n")
print("Note: This requires PostgreSQL to be running with credentials in .env")
print()

# Test 1: Database connection
print("=" * 60)
print("Test 1: Database Connection")
print("=" * 60)

try:
    from yoga_assistant.db import get_db_connection

    conn = get_db_connection()
    print("✓ Database connection successful")

    # Test connection is working
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"✓ PostgreSQL version: {version[:50]}...")

    cursor.close()
    conn.close()
    print("✓ Connection closed successfully")

except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print("\nMake sure:")
    print("  1. PostgreSQL is running")
    print("  2. .env file has correct POSTGRES_* variables")
    print("  3. Database 'yoga_rag' exists")
    sys.exit(1)

print()

# Test 2: Schema verification
print("=" * 60)
print("Test 2: Schema Verification")
print("=" * 60)

try:
    from yoga_assistant.db_prep import verify_schema

    if verify_schema():
        print("✓ Database schema is valid")
    else:
        print("✗ Schema verification failed")
        print("\nRun: python yoga_assistant/db_prep.py")
        sys.exit(1)

except Exception as e:
    print(f"✗ Schema verification failed: {e}")
    sys.exit(1)

print()

# Test 3: Conversation logging
print("=" * 60)
print("Test 3: Conversation Logging")
print("=" * 60)

try:
    from yoga_assistant.db import log_conversation

    test_conversation = {
        "question": "What is downward dog?",
        "answer": "Downward dog is a foundational yoga pose...",
        "model": "test-model",
        "retrieved_docs": [{"id": 1, "pose_name": "Downward-Facing Dog"}],
        "response_time_ms": 1500,
        "tokens_used": 150,
        "relevance": "RELEVANT",
        "cost_usd": 0.001,
    }

    conversation_id = log_conversation(**test_conversation)
    print(f"✓ Logged conversation with ID: {conversation_id}")

except Exception as e:
    print(f"✗ Conversation logging failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Feedback storage
print("=" * 60)
print("Test 4: Feedback Storage")
print("=" * 60)

try:
    from yoga_assistant.db import update_feedback

    success = update_feedback(conversation_id, 1)
    if success:
        print("✓ Feedback updated successfully")
    else:
        print("✗ Feedback update failed")
        sys.exit(1)

except Exception as e:
    print(f"✗ Feedback storage failed: {e}")
    sys.exit(1)

print()

# Test 5: Data retrieval
print("=" * 60)
print("Test 5: Data Retrieval for Monitoring")
print("=" * 60)

try:
    from yoga_assistant.db import (
        get_recent_conversations,
        get_feedback_stats,
        get_relevance_stats,
        get_model_usage_stats,
    )

    # Get recent conversations
    conversations = get_recent_conversations(limit=5)
    print(f"✓ Retrieved {len(conversations)} recent conversations")

    # Get feedback stats
    feedback_stats = get_feedback_stats()
    print(f"✓ Feedback stats: {feedback_stats}")

    # Get relevance stats
    relevance_stats = get_relevance_stats()
    print(f"✓ Relevance stats: {relevance_stats}")

    # Get model usage stats
    model_stats = get_model_usage_stats()
    print(f"✓ Model usage stats: {len(model_stats)} models tracked")

except Exception as e:
    print(f"✗ Data retrieval failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✓ ALL DATABASE TESTS PASSED")
print("=" * 60)
print("\nDatabase module is ready!")
