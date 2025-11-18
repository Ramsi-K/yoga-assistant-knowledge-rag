"""
Database preparation module for Yoga Assistant system.

This module handles database schema creation and initialization.
Run this script before starting the application for the first time.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()


def get_db_connection():
    """
    Create and return a database connection using environment variables.

    Returns:
        psycopg2 connection object

    Raises:
        ValueError: If required environment variables are missing
        psycopg2.Error: If connection fails
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "yoga_rag")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise ValueError(
            "POSTGRES_PASSWORD not found in environment variables"
        )

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        return conn
    except psycopg2.Error as e:
        raise psycopg2.Error(f"Failed to connect to database: {str(e)}")


def create_tables():
    """
    Create the conversations table and indices.

    Table schema:
    - id: UUID primary key
    - timestamp: When the conversation occurred
    - question: User's question
    - answer: Generated answer
    - model: LLM model used
    - retrieved_docs: JSON array of retrieved pose documents
    - relevance: RELEVANT/PARTLY_RELEVANT/NON_RELEVANT
    - response_time_ms: Response time in milliseconds
    - tokens_used: Number of tokens used
    - cost_usd: Cost in USD
    - feedback: User feedback (1 for thumbs up, -1 for thumbs down, NULL for no feedback)

    Indices:
    - timestamp (for time-based queries)
    - feedback (for feedback statistics)
    - relevance (for relevance statistics)
    - model (for model usage statistics)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                model TEXT NOT NULL,
                retrieved_docs JSONB,
                relevance TEXT,
                response_time_ms INTEGER,
                tokens_used INTEGER,
                cost_usd DECIMAL(10, 6),
                feedback INTEGER CHECK (feedback IN (-1, 1))
            )
            """
        )

        print("✓ Created conversations table")

        # Create indices for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
            ON conversations(timestamp DESC)
            """
        )
        print("✓ Created index on timestamp")

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_feedback 
            ON conversations(feedback) 
            WHERE feedback IS NOT NULL
            """
        )
        print("✓ Created index on feedback")

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_relevance 
            ON conversations(relevance) 
            WHERE relevance IS NOT NULL
            """
        )
        print("✓ Created index on relevance")

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_model 
            ON conversations(model)
            """
        )
        print("✓ Created index on model")

        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()

        print("\n✓ Database schema initialized successfully!")
        return True

    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        return False


def drop_tables():
    """
    Drop all tables (use with caution - for development/testing only).

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS conversations CASCADE")

        conn.commit()
        cursor.close()
        conn.close()

        print("✓ Dropped all tables")
        return True

    except Exception as e:
        print(f"Error dropping tables: {str(e)}")
        return False


def verify_schema():
    """
    Verify that the database schema is correctly set up.

    Returns:
        True if schema is valid, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if conversations table exists
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'conversations'
            )
            """
        )

        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("✗ Conversations table does not exist")
            cursor.close()
            conn.close()
            return False

        # Check table structure
        cursor.execute(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'conversations'
            ORDER BY ordinal_position
            """
        )

        columns = cursor.fetchall()
        expected_columns = {
            "id",
            "timestamp",
            "question",
            "answer",
            "model",
            "retrieved_docs",
            "relevance",
            "response_time_ms",
            "tokens_used",
            "cost_usd",
            "feedback",
        }

        actual_columns = {col[0] for col in columns}

        if expected_columns != actual_columns:
            print(f"✗ Table structure mismatch")
            print(f"  Expected: {expected_columns}")
            print(f"  Actual: {actual_columns}")
            cursor.close()
            conn.close()
            return False

        cursor.close()
        conn.close()

        print("✓ Database schema is valid")
        return True

    except Exception as e:
        print(f"Error verifying schema: {str(e)}")
        return False


def main():
    """
    Main function to initialize the database.

    Usage:
        python db_prep.py [--drop]

    Options:
        --drop: Drop existing tables before creating (use with caution)
    """
    print("=" * 60)
    print("Yoga Assistant - Database Initialization")
    print("=" * 60)
    print()

    # Check for --drop flag
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        print("WARNING: Dropping existing tables...")
        response = input("Are you sure? (yes/no): ")
        if response.lower() == "yes":
            drop_tables()
            print()
        else:
            print("Aborted.")
            return

    # Create tables
    print("Creating database schema...")
    print()
    success = create_tables()

    if not success:
        print("\n✗ Failed to initialize database")
        sys.exit(1)

    # Verify schema
    print("\nVerifying schema...")
    if verify_schema():
        print("\n✓ Database is ready to use!")
    else:
        print("\n✗ Schema verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
