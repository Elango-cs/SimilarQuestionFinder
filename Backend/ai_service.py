import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List

# A curated vocabulary of common study, academic, and technical terms to represent questions.
# This serves as a lightweight semantic feature vector map, running entirely in CPU memory (< 1MB).
VOCABULARY = [
    # Mathematics & Calculus
    "math", "mathematics", "calculus", "derivative", "derivatives", "integral", "integrals", "equation", "equations", "formula", "formulas", "limit", "limits", "algebra", "geometry", "numbers", "fraction", "matrix", "matrices", "arithmetic", "theorem", "function", "variable", "solve", "multiply", "divide",
    # Physics
    "physics", "gravity", "energy", "motion", "force", "speed", "velocity", "mechanics", "thermodynamics", "quantum", "relativity", "light", "wave", "matter", "acceleration", "mass", "friction", "sound", "optics",
    # Chemistry
    "chemistry", "chemical", "molecule", "atom", "reaction", "periodic", "elements", "compound", "bond", "acid", "base", "gas", "organic", "solution", "electron", "proton", "neutron", "mixture",
    # Biology
    "biology", "photosynthesis", "organism", "cell", "evolution", "ecosystem", "dna", "gene", "plant", "animal", "specie", "bacteria", "genetics", "ecology", "mitosis", "meiosis", "protein", "virus", "habitat",
    # Computer Science & Web Dev
    "computer", "code", "coding", "programming", "software", "algorithm", "database", "python", "javascript", "react", "html", "css", "java", "c++", "query", "frontend", "backend", "developer", "server", "class", "object", "array", "list", "loop", "compile", "debug", "flexbox", "div", "center", "props", "state", "component", "components", "render", "routing", "api", "json", "post", "get", "request", "response",
    # Machine Learning / AI
    "learning", "machine", "deep", "neural", "network", "networks", "weight", "weights", "update", "updates", "training", "train", "backpropagation", "mechanism", "model", "models", "classification", "regression", "supervised", "unsupervised", "loss", "gradient", "descent", "epoch", "batch", "dataset", "data",
    # History
    "history", "civilization", "historical", "ancient", "war", "century", "empire", "revolution", "president", "reign", "archaeology", "world", "king", "queen", "dynasty", "treaty", "conflict", "timeline", "colony",
    # Literature
    "literature", "poetry", "prose", "novel", "novels", "author", "write", "book", "playwright", "shakespeare", "poem", "poems", "essay", "literary", "drama", "fiction", "character", "characters", "theme", "themes", "metaphor", "genre", "biography", "narrative",
    # General academic / question verbs
    "what", "how", "why", "explain", "describe", "definition", "difference", "compare", "solve", "find", "calculate", "method", "concept", "structure", "process", "define", "analyze", "list"
]

# Deduplicate vocabulary list to prevent TfidfVectorizer duplicate terms errors
VOCABULARY = list(dict.fromkeys(VOCABULARY))


class AIService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("Initializing lightweight local Scikit-Learn TfidfVectorizer AI service...")
            vectorizer = TfidfVectorizer(vocabulary=VOCABULARY, lowercase=True)
            vectorizer.fit(VOCABULARY)
            cls._model = vectorizer
            print("TfidfVectorizer initialized successfully!")
        return cls._model

    def __init__(self):
        # Retrieve the static vectorizer instance
        self.vectorizer = self.get_model()

    def get_embedding(self, text: str) -> List[float]:
        """Generate TF-IDF vector embedding for a single text."""
        if not text.strip():
            return [0.0] * len(VOCABULARY)
        # Transform returns a sparse matrix of shape (1, len(VOCABULARY))
        sparse_vec = self.vectorizer.transform([text])
        # Convert to a dense 1D float list
        dense_vec = sparse_vec.toarray()[0]
        return dense_vec.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate TF-IDF vector embeddings for a list of texts."""
        if not texts:
            return []
        sparse_matrix = self.vectorizer.transform(texts)
        dense_matrix = sparse_matrix.toarray()
        return dense_matrix.tolist()

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
