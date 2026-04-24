"""
Sparse Retrieval using BM25 algorithm.
Selects the most relevant chunk from document chunks based on keyword matching.
"""

import math
import re
from collections import Counter
from typing import List


class BM25Retriever:
    """BM25-based sparse retriever for chunk selection."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[str] = []
        self.doc_tf: List[Counter] = []
        self.doc_len: List[int] = []
        self.df: Counter = Counter()
        self.idf: dict = {}
        self.avgdl: float = 0.0
        self._built: bool = False

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple word-level tokenization: lowercase + split on non-alphanumeric."""
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def build_index(self, chunks: List[str]) -> None:
        """Build BM25 index from a list of text chunks."""
        self.corpus = chunks
        n = len(chunks)

        # Compute term frequency per doc and document lengths
        self.doc_tf = []
        self.doc_len = []
        for chunk in chunks:
            tokens = self._tokenize(chunk)
            tf = Counter(tokens)
            self.doc_tf.append(tf)
            self.doc_len.append(len(tokens))

        # Document frequency: how many docs contain each term
        self.df = Counter()
        for tf in self.doc_tf:
            for term in tf:
                self.df[term] += 1

        # IDF with Robertson–Sparkman formula (standard BM25 IDF)
        self.idf = {}
        for term, df in self.df.items():
            self.idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1.0)

        # Average document length
        total_len = sum(self.doc_len)
        self.avgdl = total_len / n if n > 0 else 1.0
        self._built = True

    def _score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Compute BM25 score for one document given query tokens."""
        score = 0.0
        tf = self.doc_tf[doc_idx]
        dl = self.doc_len[doc_idx]

        for q_term in query_tokens:
            if q_term not in self.idf:
                continue
            freq = tf.get(q_term, 0)
            idf = self.idf[q_term]
            numerator = freq * (self.k1 + 1.0)
            denominator = freq + self.k1 * (1.0 - self.b + self.b * dl / self.avgdl)
            score += idf * numerator / denominator

        return score

    def retrieve(self, query: str, top_k: int = 1) -> List[dict]:
        """
        Retrieve the top-k most relevant chunks for the given query.

        Returns list of dicts: {"chunk": str, "score": float, "index": int}
        sorted by score descending.
        """
        if not self._built:
            raise RuntimeError("Index not built. Call build_index() first.")

        query_tokens = self._tokenize(query)

        scores = []
        for i in range(len(self.corpus)):
            s = self._score(query_tokens, i)
            scores.append((i, s))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = [
            {
                "chunk": self.corpus[idx],
                "score": round(score, 4),
                "index": idx,
            }
            for idx, score in scores[:top_k]
        ]
        return results


def sparse_retrieve(chunks: List[str], query: str, top_k: int = 1) -> str:
    """
    Convenience function: run BM25 sparse retrieval and return the best chunk.

    Args:
        chunks: List of text chunks (document segments).
        query: User query string.
        top_k: Number of top results to return (default 1).

    Returns:
        The best-matching chunk text.
    """
    retriever = BM25Retriever()
    retriever.build_index(chunks)
    results = retriever.retrieve(query, top_k=top_k)
    return results[0]["chunk"] if results else ""
