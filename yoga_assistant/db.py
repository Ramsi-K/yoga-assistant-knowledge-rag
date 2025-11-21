"""
Database module for Yoga Assistant system.

This module handles all database operations including:
- Connection management
- Conversation logging
- Feedback storage
- Data retrieval for monitoring
"""

import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

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
        error_msg = f"Failed to connect to database: {str(e)}"
        raise psycopg2.Error(error_msg)


def log_conversation(
    question: str,
    answer: str,
    model: str,
    retrieved_docs: List[Dict],
    response_time_ms: int,
    tokens_used: int,
    conversation_id: Optional[str] = None,
    relevance: Optional[str] = None,
    cost_usd: Optional[float] = None,
) -> str:
    """
    Log a conversation to the database.

    Args:
        question: User's question
        answer: Generated answer
        model: LLM model used
        retrieved_docs: List of retrieved pose documents
        response_time_ms: Response time in milliseconds
        tokens_used: Number of tokens used
        conversation_id: UUID string (generated if not provided)
        relevance: Relevance score (RELEVANT/PARTLY_RELEVANT/NON_RELEVANT)
        cost_usd: Cost in USD (optional)

    Returns:
        conversation_id (UUID string)

    Note:
        Handles errors gracefully - logs to console but doesn't raise
        exceptions
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (
                id, timestamp, question, answer, model,
                retrieved_docs, relevance, response_time_ms,
                tokens_used, cost_usd, feedback
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                conversation_id,
                datetime.now(),
                question,
                answer,
                model,
                Json(retrieved_docs),
                relevance,
                response_time_ms,
                tokens_used,
                cost_usd,
                None,
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error logging conversation: {str(e)}")

    return conversation_id


def update_feedback(conversation_id: str, feedback: int) -> bool:
    """
    Update feedback for a conversation.

    Args:
        conversation_id: UUID of the conversation
        feedback: 1 for thumbs up, -1 for thumbs down

    Returns:
        True if update successful, False otherwise

    Note:
        Handles errors gracefully - returns False on failure
    """
    if feedback not in [1, -1]:
        print(f"Invalid feedback value: {feedback}. Must be 1 or -1.")
        return False

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET feedback = %s
            WHERE id = %s
            """,
            (feedback, conversation_id),
        )

        conn.commit()
        rows_updated = cursor.rowcount
        cursor.close()
        conn.close()

        return rows_updated > 0

    except Exception as e:
        print(f"Error updating feedback: {str(e)}")
        return False


def get_recent_conversations(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve recent conversations for monitoring dashboard.

    Args:
        limit: Number of conversations to retrieve (default: 5)

    Returns:
        List of conversation dictionaries

    Note:
        Returns empty list on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                id, timestamp, question, answer, model,
                retrieved_docs, relevance, response_time_ms,
                tokens_used, cost_usd, feedback
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            (limit,),
        )

        conversations = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(conv) for conv in conversations]

    except Exception as e:
        print(f"Error retrieving conversations: {str(e)}")
        return []


def get_feedback_stats() -> Dict[str, int]:
    """
    Get feedback statistics for monitoring.

    Returns:
        Dictionary with positive, negative, and total counts

    Note:
        Returns zeros on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN feedback = 1 THEN 1 END) as positive,
                COUNT(CASE WHEN feedback = -1 THEN 1 END) as negative,
                COUNT(*) as total
            FROM conversations
            WHERE feedback IS NOT NULL
            """
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return {
            "positive": result[0] or 0,
            "negative": result[1] or 0,
            "total": result[2] or 0,
        }

    except Exception as e:
        print(f"Error getting feedback stats: {str(e)}")
        return {"positive": 0, "negative": 0, "total": 0}


def get_relevance_stats() -> Dict[str, Any]:
    """
    Get relevance statistics for monitoring.

    Returns:
        Dictionary with relevance counts and percentages

    Note:
        Returns zeros on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                COUNT(CASE WHEN relevance = 'RELEVANT'
                    THEN 1 END) as relevant,
                COUNT(CASE WHEN relevance = 'PARTLY_RELEVANT'
                    THEN 1 END) as partly_relevant,
                COUNT(CASE WHEN relevance = 'NON_RELEVANT'
                    THEN 1 END) as non_relevant,
                COUNT(*) as total
            FROM conversations
            WHERE relevance IS NOT NULL
            """

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        total = result[3] or 0
        relevant = result[0] or 0

        return {
            "relevant": relevant,
            "partly_relevant": result[1] or 0,
            "non_relevant": result[2] or 0,
            "total": total,
            "relevant_percentage": (
                (relevant / total * 100) if total > 0 else 0
            ),
        }

    except Exception as e:
        print(f"Error getting relevance stats: {str(e)}")
        return {
            "relevant": 0,
            "partly_relevant": 0,
            "non_relevant": 0,
            "total": 0,
            "relevant_percentage": 0,
        }


def get_cost_over_time(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get cost metrics over time for monitoring.

    Args:
        days: Number of days to retrieve (default: 7)

    Returns:
        List of dictionaries with date and cost

    Note:
        Returns empty list on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                SUM(cost_usd) as total_cost,
                COUNT(*) as conversation_count
            FROM conversations
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            AND cost_usd IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """,
            (days,),
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error getting cost over time: {str(e)}")
        return []


def get_token_usage_over_time(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get token usage metrics over time for monitoring.

    Args:
        days: Number of days to retrieve (default: 7)

    Returns:
        List of dictionaries with date and token usage

    Note:
        Returns empty list on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                SUM(tokens_used) as total_tokens,
                AVG(tokens_used) as avg_tokens,
                COUNT(*) as conversation_count
            FROM conversations
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """,
            (days,),
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error getting token usage over time: {str(e)}")
        return []


def get_response_time_stats(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get response time statistics for monitoring.

    Args:
        days: Number of days to retrieve (default: 7)

    Returns:
        List of dictionaries with date and response time stats

    Note:
        Returns empty list on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                AVG(response_time_ms) as avg_response_time,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                COUNT(*) as conversation_count
            FROM conversations
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """,
            (days,),
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error getting response time stats: {str(e)}")
        return []


def get_model_usage_stats() -> List[Dict[str, Any]]:
    """
    Get model usage statistics for monitoring.

    Returns:
        List of dictionaries with model and usage count

    Note:
        Returns empty list on error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                model,
                COUNT(*) as usage_count,
                AVG(response_time_ms) as avg_response_time,
                AVG(tokens_used) as avg_tokens
            FROM conversations
            GROUP BY model
            ORDER BY usage_count DESC
            """
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error getting model usage stats: {str(e)}")
        return []
