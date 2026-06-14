"""Tests for hermes_okf.search."""

import tempfile

from hermes_okf.bundle import OKFBundle
from hermes_okf.search import SearchIndex


class TestSearchIndex:
    def test_search_finds_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept(
                "a",
                body="The quick brown fox jumps over the lazy dog.",
                type="A",
                title="Foxes",
            )
            bundle.write_concept(
                "b",
                body="Machine learning is fascinating.",
                type="B",
                title="ML",
            )
            index = SearchIndex(bundle)
            results = index.search("fox", top_k=5)
            assert any(r[0] == "a" for r in results)

    def test_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="A", type="Project", title="Alpha")
            bundle.write_concept("b", body="B", type="Decision", title="Beta")
            index = SearchIndex(bundle)
            projects = index.filter(lambda c: c.type == "Project")
            assert len(projects) == 1
            assert projects[0].title == "Alpha"

    def test_fuzzy_search_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept(
                "a",
                body="A",
                type="A",
                title="Machine Learning Pipeline",
            )
            index = SearchIndex(bundle)
            results = index.fuzzy_search("machine learning", threshold=0.5)
            assert any(r[0] == "a" for r in results)
