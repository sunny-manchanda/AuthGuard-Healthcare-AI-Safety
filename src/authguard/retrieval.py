from __future__ import annotations

import math
import re
from collections import Counter

from .schemas import PolicyEvidence


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class PolicyRetriever:
    """Small, auditable BM25-style retriever for synthetic policy evidence."""

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.documents = [tokenize(item["text"]) for item in chunks]
        self.lengths = [len(tokens) for tokens in self.documents]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1)
        document_frequency: Counter[str] = Counter()
        for tokens in self.documents:
            document_frequency.update(set(tokens))
        total = len(self.documents)
        self.idf = {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def search(self, query: str, limit: int = 3) -> list[PolicyEvidence]:
        query_terms = tokenize(query)
        results: list[PolicyEvidence] = []
        k1, b = 1.5, 0.75
        for index, (chunk, tokens) in enumerate(zip(self.chunks, self.documents)):
            counts = Counter(tokens)
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + k1 * (
                    1 - b + b * self.lengths[index] / max(self.average_length, 1)
                )
                score += self.idf.get(term, 0.0) * frequency * (k1 + 1) / denominator
            if score > 0:
                results.append(
                    PolicyEvidence(
                        evidence_id=chunk["evidence_id"],
                        policy_id=chunk["policy_id"],
                        title=chunk["title"],
                        section=chunk["section"],
                        text=chunk["text"],
                        score=round(score, 3),
                        required_documents=chunk.get("required_documents", []),
                    )
                )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

