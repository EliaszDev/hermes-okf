"""Search and indexing utilities.

Lightweight full-text search over OKF bundles using only the standard library.
For heavier loads, the optional RAG integration can be used instead.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from hermes_okf.bundle import OKFBundle
from hermes_okf.concept import Concept


class SearchIndex:
    """Simple in-memory search index for an OKF bundle.

    Builds on first query and can be invalidated when the bundle changes.
    """

    def __init__(self, bundle: OKFBundle) -> None:
        self.bundle = bundle
        self._index: dict[str, list[str]] | None = None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    def _build_index(self) -> dict[str, list[str]]:
        """Build an inverted index: token -> list of concept_ids."""
        index: dict[str, list[str]] = {}
        for concept_id in self.bundle.list_concepts():
            concept = self.bundle.read_concept(concept_id)
            if not concept:
                continue
            text = f"{concept.title} {concept.description} {concept.body}"
            tokens = self._tokenize(text)
            for token in set(tokens):
                index.setdefault(token, []).append(concept_id)
        self._index = index
        return index

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase, alphanumeric tokens."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def invalidate(self) -> None:
        """Clear the in-memory index so it rebuilds on next query."""
        self._index = None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Full-text search returning ``(concept_id, score)`` tuples.

        Score is a simple TF-like count of matching tokens.
        """
        index = self._index if self._index is not None else self._build_index()
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: dict[str, int] = {}
        for token in query_tokens:
            for concept_id in index.get(token, []):
                scores[concept_id] = scores.get(concept_id, 0) + 1

        # Normalise by query length for a simple relevance score
        results = sorted(
            ((cid, score / len(query_tokens)) for cid, score in scores.items()),
            key=lambda x: x[1],
            reverse=True,
        )
        return results[:top_k]

    def search_concepts(self, query: str, top_k: int = 10) -> list[Concept]:
        """Return full ``Concept`` objects for search results."""
        results = self.search(query, top_k=top_k)
        concepts: list[Concept] = []
        for concept_id, _ in results:
            concept = self.bundle.read_concept(concept_id)
            if concept:
                concepts.append(concept)
        return concepts

    def filter(
        self,
        predicate: Callable[[Concept], bool],
    ) -> list[Concept]:
        """Return all concepts matching a custom predicate."""
        matches: list[Concept] = []
        for concept_id in self.bundle.list_concepts():
            concept = self.bundle.read_concept(concept_id)
            if concept and predicate(concept):
                matches.append(concept)
        return matches

    def fuzzy_search(self, query: str, threshold: float = 0.6) -> list[tuple[str, float]]:
        """Fuzzy search using token overlap ratio.

        Requires ``rapidfuzz`` for Levenshtein distance (optional).
        Falls back to simple overlap if not installed.
        """
        try:
            from rapidfuzz import fuzz

            results: list[tuple[str, float]] = []
            for concept_id in self.bundle.list_concepts():
                concept = self.bundle.read_concept(concept_id)
                if not concept:
                    continue
                text = f"{concept.title} {concept.description}"
                score = fuzz.partial_ratio(query.lower(), text.lower()) / 100.0
                if score >= threshold:
                    results.append((concept_id, score))
            return sorted(results, key=lambda x: x[1], reverse=True)

        except ImportError:
            # Fallback to token overlap
            query_tokens = set(self._tokenize(query))
            if not query_tokens:
                return []
            results: list[tuple[str, float]] = []
            for concept_id in self.bundle.list_concepts():
                concept = self.bundle.read_concept(concept_id)
                if not concept:
                    continue
                text_tokens = set(self._tokenize(f"{concept.title} {concept.description}"))
                if not text_tokens:
                    continue
                overlap = len(query_tokens & text_tokens) / len(query_tokens)
                if overlap >= threshold:
                    results.append((concept_id, overlap))
            return sorted(results, key=lambda x: x[1], reverse=True)
