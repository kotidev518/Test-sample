"""
SBERT Embedding Service - Generate and manage vector embeddings for semantic search
Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
"""
import asyncio
import numpy as np
from typing import List, Optional
from bson.binary import Binary
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingService:
    """Service to generate and manage SBERT embeddings"""
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
import threading
import time


class EmbeddingService:
    """Service to generate and manage SBERT embeddings with Lazy Loading"""
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
    def __init__(self):
        """
        Initialize the embedding service. 
        Model is NOT loaded here to save startup time and RAM.
        """
        self._model = None
        self._lock = threading.Lock()
        print(f"EmbeddingService initialized (Lazy Loading mode enabled)")
    
    @property
    def model(self):
        """Public access to the model, triggers lazy loading."""
        return self._get_model()

    def _get_model(self):
        """
        Lazily load the SentenceTransformer model if not already loaded.
        Thread-safe to prevent multiple threads from loading the model simultaneously.
        """
        if self._model is None:
            with self._lock:
                # Check again in case another thread loaded it while we were waiting for the lock
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    print(f"--- LAZY LOADING SBERT MODEL: {self.MODEL_NAME} ---")
                    start_time = time.time()
                    self._model = SentenceTransformer(f'sentence-transformers/{self.MODEL_NAME}')
                    duration = time.time() - start_time
                    print(f"--- SBERT MODEL LOADED SUCCESSFULLY (Time: {duration:.2f}s) ---")
        return self._model

    async def generate_embedding(self, text: str) -> Optional[bytes]:
        """
        Generate normalized SBERT embedding for a single text.
        
        Args:
            text: Input text to embed (will be cleaned and truncated)
        
        Returns:
            Binary embedding data ready for MongoDB storage, or None on failure
        """
        if not text or not text.strip():
            print("Warning: Empty text provided for embedding")
            return None
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            truncated_text = self._truncate_to_tokens(cleaned_text, max_tokens=512)
            
            # Generate embedding in thread pool (SBERT is CPU-bound)
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self._generate_embedding_sync,
                truncated_text
            )
            
            # Normalize using L2 norm
            normalized = self._normalize_embedding(embedding)
            
            # Convert to binary for MongoDB storage
            binary_data = self._embedding_to_binary(normalized)
            
            return binary_data
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[bytes]]:
        """
        Generate embeddings for multiple texts in batch efficiently.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of binary embeddings (same order as input)
        """
        if not texts:
            return []
            
        try:
            # Prepare all texts (clean and truncate)
            prepared_texts = [
                self._truncate_to_tokens(self._clean_text(t), max_tokens=512)
                for t in texts
            ]
            
            # Generate all embeddings in one call to the model
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._generate_embeddings_batch_sync,
                prepared_texts
            )
            
            # Normalize and convert each to binary
            results = []
            for emb in embeddings:
                normalized = self._normalize_embedding(emb)
                results.append(self._embedding_to_binary(normalized))
                
            return results
            
        except Exception as e:
            print(f"Error in batch embedding: {e}")
            return [None] * len(texts)

    def _generate_embeddings_batch_sync(self, texts: List[str]) -> np.ndarray:
        """Synchronous batch encoding using the SBERT model"""
        model = self._get_model()
        return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def chunk_text(self, text: str, chunk_size_chars: int = 3000, overlap_chars: int = 300) -> List[str]:
        """
        Break long text into overlapping chunks.
        
        Args:
            text: Input transcript text
            chunk_size_chars: Target characters per chunk (~500 words)
            overlap_chars: Overlap between chunks to maintain context
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
            
        if len(text) <= chunk_size_chars:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size_chars
            # If not at the end, try to find the last space to avoid cutting words
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space != -1 and last_space > start:
                    end = last_space
            
            chunks.append(text[start:end].strip())
            start = end - overlap_chars
            
            # Prevent infinite loop if something goes wrong
            if start < 0: start = 0
            
        return chunks
    
    def _generate_embedding_sync(self, text: str) -> np.ndarray:
        """
        Synchronously generate embedding using SBERT model.
        This is CPU-bound and should be run in executor.
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding using L2 norm.
        
        Args:
            embedding: Raw embedding vector
        
        Returns:
            L2-normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm
    
    def _embedding_to_binary(self, embedding: np.ndarray) -> bytes:
        """
        Convert numpy embedding to MongoDB Binary format.
        
        Args:
            embedding: Normalized embedding vector
        
        Returns:
            Binary data ready for MongoDB storage
        """
        # Convert to float32 for storage efficiency (half the size of float64)
        return Binary(embedding.astype(np.float32).tobytes())
    
    @staticmethod
    def binary_to_embedding(binary_data: bytes) -> np.ndarray:
        """
        Convert MongoDB Binary data back to numpy array.
        
        Args:
            binary_data: Binary data from MongoDB
        
        Returns:
            Numpy embedding vector
        """
        return np.frombuffer(binary_data, dtype=np.float32)
    
    async def compute_cosine_similarity(
        self, 
        embedding1: bytes, 
        embedding2: bytes
    ) -> float:
        """
        Compute cosine similarity between two binary embeddings.
        
        Args:
            embedding1: First embedding (binary format)
            embedding2: Second embedding (binary format)
        
        Returns:
            Cosine similarity score (0 to 1)
        """
        try:
            # Convert binaries to numpy arrays
            emb1 = self.binary_to_embedding(embedding1).reshape(1, -1)
            emb2 = self.binary_to_embedding(embedding2).reshape(1, -1)
            
            # Compute cosine similarity
            similarity = cosine_similarity(emb1, emb2)[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    async def find_most_similar(
        self,
        query_embedding: bytes,
        candidate_embeddings: List[tuple],  # [(video_id, embedding_binary), ...]
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find top-K most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding (binary format)
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
        
        Returns:
            List of (id, similarity_score) tuples, sorted by similarity (highest first)
        """
        if not candidate_embeddings:
            return []
        
        try:
            # Convert query to numpy
            query_vec = self.binary_to_embedding(query_embedding).reshape(1, -1)
            
            # Compute similarities for all candidates
            similarities = []
            for video_id, emb_binary in candidate_embeddings:
                try:
                    emb_vec = self.binary_to_embedding(emb_binary).reshape(1, -1)
                    sim = cosine_similarity(query_vec, emb_vec)[0][0]
                    similarities.append((video_id, float(sim)))
                except Exception as e:
                    print(f"Error processing embedding for {video_id}: {e}")
                    continue
            
            # Sort by similarity (descending) and return top-K
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error finding similar embeddings: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """
        Clean transcript text for embedding generation.
        
        Args:
            text: Raw transcript text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove special characters that don't add semantic meaning
        # Keep alphanumeric, spaces, and basic punctuation
        import re
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text.strip()
    
    def _truncate_to_tokens(self, text: str, max_tokens: int = 512) -> str:
        """
        Truncate text to maximum number of tokens.
        Uses simple word-based approximation (SBERT uses WordPiece tokenization).
        
        Args:
            text: Input text
            max_tokens: Maximum number of tokens (default: 512)
        
        Returns:
            Truncated text
        """
        # Rough approximation: 1 token ≈ 0.75 words
        max_words = int(max_tokens * 0.75)
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        # Truncate and rejoin
        truncated = " ".join(words[:max_words])
        return truncated


# Singleton instance
embedding_service: EmbeddingService = EmbeddingService()


def init_embedding_service():
    """
    Ensure the global embedding service is initialized.
    No longer requires pre-loaded model.
    """
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service
