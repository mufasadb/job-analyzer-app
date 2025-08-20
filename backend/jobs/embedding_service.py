"""
Embedding service for generating vector embeddings from text content.
Uses OpenAI's embedding model for semantic similarity matching.
"""

import openai
import numpy as np
from typing import List, Optional, Dict, Any
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        # Get API key from environment or use OpenRouter
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        # Configure OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Default model for embeddings
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to generate_embedding")
            return None
            
        try:
            # Clean and prepare text
            clean_text = self._preprocess_text(text)
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=clean_text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in a single API call.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (same order as input)
        """
        if not texts:
            return []
            
        try:
            # Clean and prepare texts
            clean_texts = [self._preprocess_text(text) for text in texts]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=clean_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            return [None] * len(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1, higher = more similar)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            magnitude1 = np.linalg.norm(vec1)
            magnitude2 = np.linalg.norm(vec2)
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
                
            similarity = dot_product / (magnitude1 * magnitude2)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the most similar embeddings to a query embedding.
        
        Args:
            query_embedding: The reference embedding
            candidate_embeddings: List of embeddings to compare against
            top_k: Number of top matches to return
            
        Returns:
            List of dicts with 'index' and 'similarity' keys, sorted by similarity
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                if candidate is not None:
                    similarity = self.calculate_similarity(query_embedding, candidate)
                    similarities.append({'index': i, 'similarity': similarity})
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {str(e)}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and prepare text for embedding generation.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Basic cleaning
        clean_text = text.strip()
        
        # Remove excessive whitespace
        clean_text = " ".join(clean_text.split())
        
        # Truncate if too long (OpenAI has token limits)
        max_length = 8000  # Conservative limit
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."
            logger.warning(f"Text truncated to {max_length} characters")
        
        return clean_text


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get a singleton instance of the embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service