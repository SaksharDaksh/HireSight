import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class VectorEmbeddingStore:
    """
    Local vector store and embedding engine for semantic retrieval and RAG chunk indexing.
    """

    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            max_features=max_features
        )
        self.documents: List[Dict[str, Any]] = []
        self.doc_vectors: np.ndarray = None
        self.is_fitted = False

    def build_index(self, items: List[Dict[str, Any]]):
        """
        Build index from a collection of documents or chunks.
        Each item should have {'id': ..., 'text': ..., 'metadata': ...}
        """
        self.documents = items
        corpus = [item["text"] for item in items]
        if not corpus:
            return

        self.doc_vectors = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

    def query_similarity(self, query_text: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve top-k most semantically similar documents/chunks.
        Returns [(doc_item, similarity_score), ...]
        """
        if not self.is_fitted or self.doc_vectors is None or len(self.documents) == 0:
            return []

        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()

        # Get sorted indices descending
        ranked_indices = np.argsort(similarities)[::-1]
        results = []

        for idx in ranked_indices[:top_k]:
            results.append((self.documents[idx], float(similarities[idx])))

        return results

    def compute_pair_similarity(self, text_a: str, text_b: str) -> float:
        """Compute direct cosine similarity between two texts."""
        if not text_a or not text_b:
            return 0.0
        
        # If vectorizer fitted, use it; otherwise fit on the pair
        if self.is_fitted:
            vecs = self.vectorizer.transform([text_a, text_b])
        else:
            local_vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            try:
                vecs = local_vec.fit_transform([text_a, text_b])
            except ValueError:
                return 0.0

        sim = cosine_similarity(vecs[0:1], vecs[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))

    def save_index(self, path: str):
        """Persist vectorizer and document index to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "vectorizer": self.vectorizer,
                "documents": self.documents,
                "doc_vectors": self.doc_vectors,
                "is_fitted": self.is_fitted
            }, f)

    def load_index(self, path: str):
        """Load persisted index."""
        if not os.path.exists(path):
            return False
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.documents = data["documents"]
            self.doc_vectors = data["doc_vectors"]
            self.is_fitted = data["is_fitted"]
        return True
