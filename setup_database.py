"""
Setup script to initialize the PostgreSQL database for Yoga RAG system.

Run this after starting PostgreSQL with docker-compose.
"""

import sys
import time

sys.path.insert(0, "yoga_assistant")

from db_prep import create_tables, verify_schema

if __name__ == "__main__":
    print("=" * 60)
    print("Yoga RAG - Database Setup")
    print("=" * 60)
    print()
    print("Make sure PostgreSQL is running: docker-compose up -d")
    print()

    # Give user a moment to read
    time.sleep(1)

    try:
        print("Creating database schema...")
        print()
        success = create_tables()

        if not success:
            raise Exception("Failed to create tables")

        print("\nVerifying schema...")
        if verify_schema():
            print("\n" + "=" * 60)
            print("✓ Database initialized successfully!")
            print("✓ You can now run: streamlit run yoga_assistant/app.py")
            print("=" * 60)
        else:
            raise Exception("Schema verification failed")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ Failed to initialize database: {e}")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Make sure Docker is running")
        print("2. Run: docker-compose up -d")
        print("3. Wait 10 seconds for PostgreSQL to start")
        print("4. Try running this script again")
        sys.exit(1)
