import os
import sys

# Limit PyTorch memory usage and threads to fit in Render's 512MB limit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
import torch
import gc
from sentence_transformers import SentenceTransformer
from typing import List

# Limit threads in PyTorch execution engine
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

class AIService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
            # Disable grad calculation globally to save memory
            torch.set_grad_enabled(False)
            
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Disable grad on model parameters
            for param in cls._model.parameters():
                param.requires_grad = False
                
            # Force garbage collection
            gc.collect()
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
