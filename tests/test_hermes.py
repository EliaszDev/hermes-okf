"""Tests for hermes_okf.hermes.HermesAgent."""

import tempfile

from hermes_okf.hermes import HermesAgent


class TestHermesAgent:
    def test_agent_init_creates_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent")
            assert agent.current_session_id is not None
            assert agent.memory.bundle.read_concept("config/agent") is not None
            sessions = agent.list_sessions()
            assert len(sessions) >= 1

    def test_register_and_list_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent")
            agent.register_tool("test_tool", "A test tool", schema={"type": "object"})
            tools = agent.list_tools()
            assert "tools/test_tool" in tools
            tool = agent.get_tool("test_tool")
            assert tool is not None
            assert tool.title == "test_tool"

    def test_create_and_complete_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent")
            plan_id = agent.create_plan("Test plan", ["Step 1", "Step 2"])
            assert plan_id is not None
            agent.complete_step(0, result="Done step 1")
            plan = agent.memory.bundle.read_concept(plan_id)
            assert plan is not None
            assert "[x]" in plan.body
            assert plan.metadata.get("progress", 0) == 50

    def test_snapshot_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent", model="gpt-4o")
            agent.create_plan("Snapshot plan", ["A"])
            agent.snapshot(note="before restore")
            # Simulate state change
            agent.model = "changed"
            # Restore from last snapshot
            meta = agent.restore()
            assert meta.get("model") == "gpt-4o"

    def test_build_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent")
            agent.register_tool("calc", "Calculator")
            agent.memory.record_decision("Use Python", tags=["lang"])
            ctx = agent.build_context("What tool should I use?")
            assert "Calculator" in ctx
            assert "Use Python" in ctx or "Decision" in ctx

    def test_end_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = HermesAgent(tmp, agent_id="test-agent")
            sid = agent.current_session_id
            agent.end_session()
            session = agent.memory.bundle.read_concept(f"sessions/{sid}")
            assert session is not None
            assert session.metadata.get("status") == "completed"
