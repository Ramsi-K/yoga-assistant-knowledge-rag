"""
Retrieval module for Yoga RAG system.

This module implements the best retrieval approach found through experimentation:
Weighted Product Hybrid Search (BM25 + Vector) with alpha=0.4

Based on experiments in notebooks/03-retrieval-experiments.ipynb:
- Hit Rate: 76.0%
- MRR: 66.0%
- Configuration: alpha=0.4 (40% BM25, 60% Vector)
"""

import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def simple_tokenize(text: str) -> List[str]:
    """
    Simple tokenization: lowercase and split on non-alphanumeric characters.

    Args:
        text: Input text to tokenize

    Returns:
        List of tokens
    """
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return tokens


class BM25Search:
    """
    BM25-based text search for yoga poses.
    """

    def __init__(self, pose_dict: Dict[int, Dict], fields: List[str] = None):
        """
        Initialize BM25 search with pose data.

        Args:
            pose_dict: Dictionary mapping pose IDs to pose data
            fields: List of fields to index (default: all searchable fields)
        """
        self.pose_dict = pose_dict
        self.pose_ids = list(pose_dict.keys())

        # Default fields to index (best configuration from experiments)
        if fields is None:
            self.fields = [
                "pose_name",
                "sanskrit_name",
                "category",
                "difficulty_level",
                "benefits",
                "contraindications",
                "instructions",
            ]
        else:
            self.fields = fields

        # Create documents for indexing
        self.documents = []
        for pose_id in self.pose_ids:
            pose = pose_dict[pose_id]
            doc_text = self._create_document_text(pose)
            self.documents.append(doc_text)

        # Tokenize documents
        tokenized_docs = [simple_tokenize(doc) for doc in self.documents]

        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)

    def _create_document_text(self, pose: Dict) -> str:
        """
        Create searchable text from specified fields.
        """
        parts = []
        for field in self.fields:
            value = pose.get(field, "")
            if pd.notna(value):
                parts.append(str(value))
        return " ".join(parts)

    def search(self, query: str, top_k: int = 5) -> List[int]:
        """
        Search for poses matching the query.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of pose IDs ranked by relevance
        """
        # Tokenize query
        tokenized_query = simple_tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Return pose IDs
        return [self.pose_ids[i] for i in top_indices]


class VectorSearch:
    """
    Vector-based semantic search for yoga poses using sentence-transformers.
    """

    def __init__(
        self,
        pose_dict: Dict[int, Dict],
        embedding_model: str = "all-mpnet-base-v2",
        fields: List[str] = None,
    ):
        """
        Initialize vector search with pose data and embedding model.

        Args:
            pose_dict: Dictionary mapping pose IDs to pose data
            embedding_model: Name of the sentence-transformers model to use
            fields: List of fields to embed (default: all searchable fields)
        """
        self.pose_dict = pose_dict
        self.pose_ids = list(pose_dict.keys())
        self.embedding_model_name = embedding_model

        # Default fields to embed (best configuration from experiments)
        if fields is None:
            self.fields = [
                "pose_name",
                "sanskrit_name",
                "category",
                "difficulty_level",
                "benefits",
                "contraindications",
                "instructions",
            ]
        else:
            self.fields = fields

        # Load the sentence-transformers model
        print(f"Loading embedding model: {embedding_model}...")
        self.model = SentenceTransformer(embedding_model)
        print(
            f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}"
        )

        # Create documents for embedding
        self.documents = []
        for pose_id in self.pose_ids:
            pose = pose_dict[pose_id]
            doc_text = self._create_document_text(pose)
            self.documents.append(doc_text)

        # Generate embeddings for all documents
        print(f"Generating embeddings for {len(self.documents)} poses...")
        self.doc_embeddings = self.model.encode(
            self.documents, show_progress_bar=True, convert_to_numpy=True
        )
        print(f"Embeddings generated. Shape: {self.doc_embeddings.shape}")

    def _create_document_text(self, pose: Dict) -> str:
        """
        Create searchable text from specified fields.
        """
        parts = []
        for field in self.fields:
            value = pose.get(field, "")
            if pd.notna(value):
                parts.append(str(value))
        return " ".join(parts)

    def search(self, query: str, top_k: int = 5) -> List[int]:
        """
        Search for poses matching the query using semantic similarity.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of pose IDs ranked by semantic similarity
        """
        # Get query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Calculate cosine similarity with all documents
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1), self.doc_embeddings
        )[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return pose IDs
        return [self.pose_ids[i] for i in top_indices]


class HybridSearch:
    """
    Hybrid search combining BM25 text search and vector semantic search.

    Uses Weighted Product combination with alpha=0.4 (best configuration from experiments).
    """

    def __init__(
        self,
        bm25_search: BM25Search,
        vector_search: VectorSearch,
    ):
        """
        Initialize hybrid search with both search engines.

        Args:
            bm25_search: BM25 search instance
            vector_search: Vector search instance
        """
        self.bm25_search = bm25_search
        self.vector_search = vector_search

    def search(
        self, query: str, top_k: int = 5, alpha: float = 0.4
    ) -> List[int]:
        """
        Search using Weighted Product hybrid approach.

        This is the best performing method from experiments:
        - Hit Rate: 76.0%
        - MRR: 66.0%
        - Alpha: 0.4 (40% BM25, 60% Vector)

        Final score = (norm_bm25_score ^ alpha) * (norm_vector_score ^ (1-alpha))

        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for BM25 (default 0.4 from experiments)

        Returns:
            List of pose IDs ranked by hybrid score
        """
        # Get raw scores
        tokenized_query = simple_tokenize(query)
        bm25_scores_raw = self.bm25_search.bm25.get_scores(tokenized_query)

        query_embedding = self.vector_search.model.encode(
            [query], convert_to_numpy=True
        )[0]
        vector_scores_raw = cosine_similarity(
            query_embedding.reshape(1, -1), self.vector_search.doc_embeddings
        )[0]

        # Normalize scores to [0, 1]
        def normalize_scores(scores):
            min_score = np.min(scores)
            max_score = np.max(scores)
            if max_score - min_score == 0:
                return np.ones_like(scores) * 0.5  # Avoid zero product
            return (scores - min_score) / (
                max_score - min_score
            ) + 0.01  # Add small epsilon

        bm25_scores_norm = normalize_scores(bm25_scores_raw)
        vector_scores_norm = normalize_scores(vector_scores_raw)

        # Combine with weighted product
        combined_scores = {}
        for i, pose_id in enumerate(self.bm25_search.pose_ids):
            combined_scores[pose_id] = (bm25_scores_norm[i] ** alpha) * (
                vector_scores_norm[i] ** (1 - alpha)
            )

        # Sort and return top-k
        sorted_results = sorted(
            combined_scores.items(), key=lambda x: x[1], reverse=True
        )
        return [pose_id for pose_id, _ in sorted_results[:top_k]]


def create_retrieval_system(pose_dict: Dict[int, Dict]) -> HybridSearch:
    """
    Create the complete retrieval system with best configuration from experiments.

    This is a convenience function that sets up:
    - BM25 search with all 7 fields
    - Vector search with all-mpnet-base-v2 model
    - Hybrid search with Weighted Product (alpha=0.4)

    Args:
        pose_dict: Dictionary mapping pose IDs to pose data

    Returns:
        HybridSearch instance ready to use
    """
    print("Creating retrieval system with best configuration...")
    print("- BM25: all 7 fields")
    print("- Vector: all-mpnet-base-v2")
    print("- Hybrid: Weighted Product (alpha=0.4)")
    print()

    # Create BM25 search
    bm25_search = BM25Search(pose_dict)

    # Create Vector search
    vector_search = VectorSearch(
        pose_dict, embedding_model="all-mpnet-base-v2"
    )

    # Create Hybrid search
    hybrid_search = HybridSearch(bm25_search, vector_search)

    print("✓ Retrieval system ready!")
    return hybrid_search
