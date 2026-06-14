"""Tests for hermes_okf.bundle."""

import tempfile
from pathlib import Path

import pytest

from hermes_okf.bundle import OKFBundle
from hermes_okf.concept import Concept


class TestBundleInit:
    def test_creates_bundle_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            assert (bundle.root / "index.md").exists()
            assert (bundle.root / "log.md").exists()
            assert (bundle.root / "projects" / "index.md").exists()
            assert (bundle.root / "decisions" / "index.md").exists()
            assert (bundle.root / "context" / "index.md").exists()

    def test_existing_bundle_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            OKFBundle(tmp)
            # Re-init should not raise
            OKFBundle(tmp)


class TestReadWrite:
    def test_write_and_read_concept(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            concept = bundle.write_concept(
                "projects/my_project",
                body="# My Project\n\nA sample project description.",
                type="Project",
                title="My Project",
                tags=["ml", "data"],
            )
            assert isinstance(concept, Concept)
            assert concept.type == "Project"

            retrieved = bundle.read_concept("projects/my_project")
            assert retrieved is not None
            assert retrieved.title == "My Project"
            assert "data" in retrieved.tags
            assert retrieved.timestamp is not None

    def test_read_missing_concept_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            assert bundle.read_concept("nonexistent") is None

    def test_delete_concept(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("tmp/test", body="tmp", type="Test")
            assert bundle.read_concept("tmp/test") is not None
            assert bundle.delete_concept("tmp/test") is True
            assert bundle.read_concept("tmp/test") is None
            assert bundle.delete_concept("tmp/test") is False

    def test_list_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="a", type="A")
            bundle.write_concept("b", body="b", type="B")
            bundle.write_concept("sub/c", body="c", type="C")
            concepts = bundle.list_concepts()
            assert "a" in concepts
            assert "b" in concepts
            assert "sub/c" in concepts
            assert "index.md" not in concepts

    def test_list_concepts_filtered(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("projects/a", body="a", type="A")
            bundle.write_concept("decisions/b", body="b", type="B")
            assert bundle.list_concepts("projects") == ["projects/a"]


class TestLogging:
    def test_append_and_read_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.append_log("Test entry", category="Test")
            log = bundle.read_log()
            assert "Test entry" in log
            assert "Test" in log


class TestGraphEdges:
    def test_extract_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept(
                "a",
                body="See [b](b.md) and [external](https://example.com).",
                type="A",
            )
            bundle.write_concept("b", body="Body B", type="B")
            edges = bundle.get_graph_edges()
            assert any(e["source"] == "a" and e["target"] == "b" for e in edges)
            assert not any(e["target"].startswith("http") for e in edges)

    def test_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="[b](b.md)", type="A")
            bundle.write_concept("b", body="Body", type="B")
            neighbors = bundle.get_neighbors("a")
            assert any(n["target"] == "b" for n in neighbors)

    def test_to_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("x", body="X", type="X", title="Title X")
            d = bundle.to_dict("x")
            assert d is not None
            assert d["title"] == "Title X"
            assert bundle.to_dict("nonexistent") is None
