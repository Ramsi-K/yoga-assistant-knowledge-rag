# Database Module Documentation

## Overview

The database module provides PostgreSQL integration for logging conversations, storing user feedback, and retrieving metrics for monitoring.

## Setup

### 1. Configure Environment Variables

Add these to your `.env` file:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=yoga_rag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

### 2. Initialize Database Schema

Run the database preparation script:

```bash
python yoga_assistant/db_prep.py
```

This will:

- Create the `conversations` table
- Add indices for common queries
- Verify the schema

To drop and recreate tables (development only):

```bash
python yoga_assistant/db_prep.py --drop
```

## Usage

### Logging Conversations

```python
from yoga_assistant.db import log_conversation

conversation_id = log_conversation(
    question="What is downward dog?",
    answer="Downward dog is a foundational yoga pose...",
    model="deepseek-ai/DeepSeek-V3",
    retrieved_docs=[
        {"id": 1, "pose_name": "Downward-Facing Dog", "category": "standing"}
    ],
    response_time_ms=1500,
    tokens_used=150,
    relevance="RELEVANT",  # Optional
    cost_usd=0.001  # Optional
)
```

### Storing Feedback

```python
from yoga_assistant.db import update_feedback

# Thumbs up
success = update_feedback(conversation_id, 1)

# Thumbs down
success = update_feedback(conversation_id, -1)
```

### Retrieving Data for Monitoring

```python
from yoga_assistant.db import (
    get_recent_conversations,
    get_feedback_stats,
    get_relevance_stats,
    get_cost_over_time,
    get_token_usage_over_time,
    get_response_time_stats,
    get_model_usage_stats
)

# Get last 10 conversations
conversations = get_recent_conversations(limit=10)

# Get feedback statistics
feedback = get_feedback_stats()
# Returns: {"positive": 45, "negative": 5, "total": 50}

# Get relevance statistics
relevance = get_relevance_stats()
# Returns: {"relevant": 40, "partly_relevant": 8, "non_relevant": 2,
#           "total": 50, "relevant_percentage": 80.0}

# Get cost over last 7 days
cost_data = get_cost_over_time(days=7)

# Get token usage over last 7 days
token_data = get_token_usage_over_time(days=7)

# Get response time statistics
response_times = get_response_time_stats(days=7)

# Get model usage statistics
model_usage = get_model_usage_stats()
```

## Database Schema

### conversations table

| Column           | Type      | Description                           |
| ---------------- | --------- | ------------------------------------- |
| id               | UUID      | Primary key (conversation ID)         |
| timestamp        | TIMESTAMP | When conversation occurred            |
| question         | TEXT      | User's question                       |
| answer           | TEXT      | Generated answer                      |
| model            | TEXT      | LLM model used                        |
| retrieved_docs   | JSONB     | Retrieved pose documents              |
| relevance        | TEXT      | RELEVANT/PARTLY_RELEVANT/NON_RELEVANT |
| response_time_ms | INTEGER   | Response time in milliseconds         |
| tokens_used      | INTEGER   | Number of tokens used                 |
| cost_usd         | DECIMAL   | Cost in USD                           |
| feedback         | INTEGER   | 1 (thumbs up), -1 (thumbs down), NULL |

### Indices

- `idx_conversations_timestamp` - For time-based queries
- `idx_conversations_feedback` - For feedback statistics
- `idx_conversations_relevance` - For relevance statistics
- `idx_conversations_model` - For model usage statistics

## Error Handling

All database functions handle errors gracefully:

- **log_conversation**: Returns conversation_id even if logging fails (prints error to console)
- **update_feedback**: Returns False on failure
- **get\_\* functions**: Return empty lists/dicts with zeros on failure

This ensures the application continues working even if database operations fail.

## Testing

Run the database test suite:

```bash
python tests/test_db_module.py
```

Note: Requires PostgreSQL to be running with correct credentials in `.env`

## Integration with RAG Pipeline

The database module integrates seamlessly with the RAG pipeline:

```python
from yoga_assistant.rag import rag_pipeline
from yoga_assistant.db import log_conversation, update_feedback

# Run RAG pipeline
result = rag_pipeline(
    question="What poses help with flexibility?",
    retrieval_system=retrieval_system,
    pose_dict=pose_dict
)

# Log conversation
conversation_id = log_conversation(
    question=result["question"],
    answer=result["answer"],
    model=result["model"],
    retrieved_docs=result["retrieved_poses"],
    response_time_ms=result["response_time_ms"],
    tokens_used=result["tokens_used"]
)

# Later, when user provides feedback
update_feedback(conversation_id, 1)  # Thumbs up
```

## Grafana Integration

The monitoring functions are designed to work with Grafana dashboards:

- `get_recent_conversations()` → Table panel
- `get_feedback_stats()` → Pie chart
- `get_relevance_stats()` → Gauge chart
- `get_cost_over_time()` → Time series chart
- `get_token_usage_over_time()` → Time series chart
- `get_response_time_stats()` → Time series chart
- `get_model_usage_stats()` → Bar chart

See `grafana/` directory for dashboard configuration.
