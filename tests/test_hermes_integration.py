"""Tests for hermes_okf.hermes_integration.HermesOKFProvider."""

import tempfile

from hermes_okf.hermes_integration import HermesOKFConfig, HermesOKFProvider


class TestHermesOKFProvider:
    def test_provider_init_creates_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes")
            provider = HermesOKFProvider(config)
            assert provider.agent.current_session_id is not None
            assert (provider.agent.memory.bundle.root / "hermes" / "sessions").exists()
            assert (provider.agent.memory.bundle.root / "hermes" / "tools").exists()
            assert (provider.agent.memory.bundle.root / "hermes" / "plans").exists()

    def test_session_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes", auto_snapshot=False)
            provider = HermesOKFProvider(config)
            provider.on_session_start("test-session-001")
            assert provider.agent.current_session_id == "test-session-001"
            provider.on_session_end("test-session-001")
            sessions = provider.agent.list_sessions()
            assert any("test-session" in s for s in sessions)

    def test_memory_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes")
            provider = HermesOKFProvider(config)
            provider.on_memory_write("memory", "User prefers Python")
            provider._flush_hot()
            log = provider.agent.memory.bundle.read_log()
            assert "User prefers Python" in log

    def test_tool_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes", log_tool_calls=True)
            provider = HermesOKFProvider(config)
            provider.on_tool_call("search_web", {"query": "test"}, "Found 5 results")
            provider._flush_hot()
            tools = provider.agent.list_tools()
            assert "tools/search_web" in tools

    def test_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes", log_decisions=True)
            provider = HermesOKFProvider(config)
            provider.on_decision("Use Claude", "Better reasoning", tags=["model"])
            provider._flush_hot()
            decisions = provider.agent.memory.bundle.list_concepts("decisions")
            assert len(decisions) > 0

    def test_plan_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes", auto_snapshot=False)
            provider = HermesOKFProvider(config)
            plan_id = provider.on_plan_create("Test plan", ["Step 1", "Step 2"])
            assert plan_id is not None
            provider.on_plan_step_complete(plan_id, 0, "Done step 1")
            plan = provider.agent.memory.bundle.read_concept(plan_id)
            assert plan is not None
            assert "[x]" in plan.body
            provider.on_plan_complete(plan_id)
            archived = provider.agent.memory.bundle.list_concepts("plans/archive")
            assert len(archived) > 0

    def test_snapshot_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = HermesOKFConfig(bundle_path=tmp, agent_id="test-hermes", auto_snapshot=False)
            provider = HermesOKFProvider(config)
            provider.on_decision("Use Python", "It's great", tags=["lang"])
            provider._flush_hot()
            provider.snapshot(note="checkpoint")
            meta = provider.restore()
            assert meta is not None
