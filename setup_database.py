"""
Setup script to initialize the PostgreSQL database for Yoga RAG system.

IMPORTANT: This script is ONLY needed for LOCAL DEVELOPMENT.

If you're using Docker (recommended), database initialization happens
automatically via docker-entrypoint.sh. You don't need this script.

Use this script when:
- Running the app locally (not in Docker)
- PostgreSQL is running in Docker but app is running on your machine

Usage:
    1. Start PostgreSQL: docker-compose up -d postgres
    2. Run this script: python setup_database.py
    3. Start app locally: streamlit run yoga_assistant/app.py
"""

import sys
import time

sys.path.insert(0, "yoga_assistant")

from db_prep import create_tables, verify_schema

if __name__ == "__main__":
    print("=" * 60)
    print("Yoga RAG - Database Setup (Local Development)")
    print("=" * 60)
    print()
    print("NOTE: If using Docker, this script is NOT needed!")
    print("      Database initialization happens automatically.")
    print()
    print("This script is for LOCAL DEVELOPMENT only.")
    print("Make sure PostgreSQL is running: docker-compose up -d postgres")
    print()

    # Give user a moment to read
    time.sleep(2)

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
        print("2. Run: docker-compose up -d postgres")
        print("3. Wait 10 seconds for PostgreSQL to start")
        print("4. Check your .env file has correct database credentials")
        print("5. Try running this script again")
        print()
        print("OR use Docker for everything (recommended):")
        print("   docker-compose up --build")
        sys.exit(1)
