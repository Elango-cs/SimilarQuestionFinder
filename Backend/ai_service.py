import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

class AIService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # We use a lightweight and powerful local embedding model.
            # Downloads once on startup and caches locally.
            print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Model loaded successfully!")
        return cls._model

    def __init__(self):
        # Trigger model loading
        self.model = self.get_model()

    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text."""
        if not text.strip():
            return [0.0] * 384  # MiniLM dimension is 384
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        dot_product = np.dot(a, b)
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)
