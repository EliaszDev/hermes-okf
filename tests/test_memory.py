"""Tests for hermes_okf.memory."""

import tempfile

from hermes_okf.memory import HermesMemory


class TestHermesMemory:
    def test_start_end_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            sid = mem.start_session("test-123")
            assert "test-123" in sid
            mem.end_session("test-123")
            log = mem.bundle.read_log()
            assert "Session started" in log
            assert "Session ended" in log

    def test_record_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            concept = mem.record_decision(
                "Use ONNX Runtime",
                rationale="Better ROCm support",
                tags=["gpu"],
            )
            assert concept.type == "Decision"
            assert "ONNX" in concept.title
            assert "gpu" in concept.tags

    def test_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            mem.register_project("alpha", "Alpha Pipeline", "Data processing pipeline")
            mem.record_decision("Use Python", tags=["alpha"])
            results = mem.recall("Python")
            assert len(results) > 0

    def test_recall_by_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            mem.register_project("alpha", "Alpha", tags=["alpha"])
            mem.register_project("beta", "Beta", tags=["beta"])
            alpha = mem.recall_by_tag("alpha")
            assert len(alpha) == 1
            assert alpha[0].title == "Alpha"

    def test_recall_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            mem.register_project("alpha_pipeline", "Alpha Pipeline")
            project = mem.recall_project("Alpha Pipeline")
            assert project is not None
            assert project.title == "Alpha Pipeline"

    def test_get_recent_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = HermesMemory(tmp, agent_id="test-agent")
            mem.bundle.append_log("Line 1")
            mem.bundle.append_log("Line 2")
            recent = mem.get_recent_log(n_lines=10)
            assert "Line 2" in recent
