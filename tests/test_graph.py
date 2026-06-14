"""Tests for hermes_okf.graph."""

import tempfile

from hermes_okf.bundle import OKFBundle
from hermes_okf.graph import GraphExtractor


class TestGraphExtractor:
    def test_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="[b](b.md)", type="A")
            bundle.write_concept("b", body="Body", type="B")
            extractor = GraphExtractor(bundle)
            assert extractor.get_neighbors("a") == ["b"]

    def test_backlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="[b](b.md)", type="A")
            bundle.write_concept("b", body="Body", type="B")
            extractor = GraphExtractor(bundle)
            assert extractor.get_backlinks("b") == ["a"]

    def test_tag_clusters(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="A", type="A", tags=["x"])
            bundle.write_concept("b", body="B", type="B", tags=["x", "y"])
            extractor = GraphExtractor(bundle)
            clusters = extractor.get_tag_clusters()
            assert "x" in clusters
            assert len(clusters["x"]) == 2
            assert len(clusters["y"]) == 1

    def test_traverse(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="[b](b.md)", type="A")
            bundle.write_concept("b", body="[c](c.md)", type="B")
            bundle.write_concept("c", body="Body", type="C")
            extractor = GraphExtractor(bundle)
            tree = extractor.traverse("a", max_depth=2)
            assert tree["id"] == "a"
            assert "children" in tree

    def test_get_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("sub/a", body="A", type="A")
            bundle.write_concept("sub/b", body="B", type="B")
            extractor = GraphExtractor(bundle)
            children = extractor.get_children("sub/a")
            assert "sub/b" in children
