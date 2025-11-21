"""
RAG module for Yoga Assistant system.

This module implements the complete RAG pipeline based on experiments:
- Retrieval: Weighted Product Hybrid Search (alpha=0.4)
- Generation: DeepSeek-V3 with structured prompt
- NO query rewriting (experiments showed no benefit)
- NO re-ranking (experiments showed degradation)

Based on experiments in notebooks/04-rag-experiments.ipynb and
notebooks/05-llm-evaluation.ipynb:
- Model: deepseek-ai/DeepSeek-V3
- Prompt: structured
- Quality Score: 95.0%
- Relevance: 90% relevant, 10% partly relevant
"""

import os
import time
import uuid
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_llm_client() -> OpenAI:
    """
    Create OpenAI client configured for Hyperbolic/Nebius API.

    Returns:
        OpenAI client instance
    """
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.hyperbolic.xyz/v1")

    if not api_key:
        raise ValueError("LLM_API_KEY not found in environment variables")

    return OpenAI(api_key=api_key, base_url=base_url)


def assemble_context(
    retrieved_pose_ids: List[int], pose_dict: Dict[int, Dict]
) -> str:
    """
    Format retrieved poses into a context string for the LLM.

    Args:
        retrieved_pose_ids: List of pose IDs from retrieval
        pose_dict: Dictionary mapping pose IDs to pose data

    Returns:
        Formatted context string
    """
    if not retrieved_pose_ids:
        return "No relevant yoga poses found."

    context_parts = []

    for i, pose_id in enumerate(retrieved_pose_ids, 1):
        pose = pose_dict[pose_id]
        context = f"""Pose {i}: {pose['pose_name']} ({pose['sanskrit_name']})
Category: {pose['category']}
Difficulty: {pose['difficulty_level']}
Benefits: {pose['benefits']}
Contraindications: {pose['contraindications']}
Instructions: {pose['instructions']}
Modifications: {pose['modifications']}
"""
        context_parts.append(context)

    return "\n---\n".join(context_parts)


def create_structured_prompt(question: str, context: str) -> str:
    """
    Create structured prompt (best performing from experiments).

    This prompt template achieved:
    - 95.0% quality score with DeepSeek-V3
    - 90% relevant, 10% partly relevant
    - Best overall performance across all combinations

    Args:
        question: User's question
        context: Retrieved yoga pose information

    Returns:
        Formatted prompt string
    """
    prompt = (
        "You are a yoga expert assistant. Answer the question using "
        "the provided information. Structure your answer clearly with "
        "relevant details.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Provide a clear, structured answer:"
    )

    return prompt


def generate_answer(
    question: str,
    context: str,
    client: OpenAI,
    model: str = "deepseek-ai/DeepSeek-V3",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Generate answer using LLM.

    Args:
        question: User's question
        context: Retrieved pose information
        client: OpenAI client instance
        model: LLM model to use (default: DeepSeek-V3)
        temperature: LLM temperature (default: 0.3)
        max_tokens: Maximum tokens in response (default: 500)

    Returns:
        Dictionary with answer, tokens_used, and generation_time_ms
    """
    start_time = time.time()

    # Create prompt using best template
    prompt = create_structured_prompt(question, context)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

    except Exception as e:
        answer = f"Error generating response: {str(e)}"
        tokens_used = 0

    generation_time_ms = int((time.time() - start_time) * 1000)

    return {
        "answer": answer,
        "tokens_used": tokens_used,
        "generation_time_ms": generation_time_ms,
    }


def rag_pipeline(
    question: str,
    retrieval_system,
    pose_dict: Dict[int, Dict],
    client: Optional[OpenAI] = None,
    model: str = "deepseek-ai/DeepSeek-V3",
    top_k: int = 5,
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Complete RAG pipeline: retrieve → assemble context → generate answer.

    This implementation is based on experiments showing:
    - Query rewriting: NO BENEFIT (adds latency, no quality improvement)
    - Re-ranking: DEGRADES PERFORMANCE (removes BM25 signal)
    - Hybrid search: OPTIMAL (alpha=0.4 already tuned)

    Args:
        question: User's question
        retrieval_system: HybridSearch instance
        pose_dict: Dictionary mapping pose IDs to pose data
        client: OpenAI client (created if None)
        model: LLM model to use
        top_k: Number of poses to retrieve
        temperature: LLM temperature
        max_tokens: Maximum tokens in response

    Returns:
        Dictionary with answer, conversation_id, retrieved_poses,
        tokens_used, response_time_ms, and model
    """
    start_time = time.time()

    # Create client if not provided
    if client is None:
        client = create_llm_client()

    # Generate conversation ID
    conversation_id = str(uuid.uuid4())

    # Step 1: Retrieve relevant poses using hybrid search
    # NO query rewriting - experiments showed no benefit
    retrieved_ids = retrieval_system.search(question, top_k=top_k)

    if not retrieved_ids:
        no_results_msg = (
            "I couldn't find any relevant yoga poses for your question. "
            "Could you please rephrase or ask about a specific pose, "
            "category, or benefit?"
        )
        return {
            "answer": no_results_msg,
            "conversation_id": conversation_id,
            "retrieved_poses": [],
            "tokens_used": 0,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "model": model,
        }

    # Step 2: Assemble context
    # NO re-ranking - experiments showed it degrades performance
    context = assemble_context(retrieved_ids, pose_dict)

    # Step 3: Generate answer
    generation_result = generate_answer(
        question, context, client, model, temperature, max_tokens
    )

    # Calculate total response time
    response_time_ms = int((time.time() - start_time) * 1000)

    # Format retrieved poses for response
    retrieved_poses = []
    for pose_id in retrieved_ids:
        retrieved_poses.append(
            {
                "id": pose_id,
                "pose_name": pose_dict[pose_id]["pose_name"],
                "category": pose_dict[pose_id]["category"],
                "difficulty_level": pose_dict[pose_id]["difficulty_level"],
            }
        )

    return {
        "answer": generation_result["answer"],
        "conversation_id": conversation_id,
        "retrieved_poses": retrieved_poses,
        "tokens_used": generation_result["tokens_used"],
        "response_time_ms": response_time_ms,
        "model": model,
    }
