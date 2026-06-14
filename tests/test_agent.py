"""Tests for hermes_okf.agent decorators."""

import tempfile

from hermes_okf.agent import (
    HermesMemoryMixin,
    memorize_decision,
)


class DummyAgent(HermesMemoryMixin):
    def __init__(self, bundle_path: str):
        super().__init__(bundle_path, agent_id="dummy")
        self.counter = 0
        # Apply wrappers after super().__init__
        self.make_decision = self.wrap_decision(self.make_decision)
        self.observe = self.wrap_observation(self.observe)
        self.run_tool = self.wrap_tool(self.run_tool)

    def make_decision(self, value: int) -> int:
        self.counter += value
        return self.counter

    def observe(self, msg: str) -> str:
        return msg.upper()

    def run_tool(self, name: str) -> str:
        return f"result-of-{name}"


class TestDecorators:
    def test_memorize_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = DummyAgent(tmp)
            agent.make_decision(5)
            decisions = agent.memory.get_decisions()
            assert len(decisions) == 1
            assert "make_decision" in decisions[0].body

    def test_memorize_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = DummyAgent(tmp)
            agent.observe("hello")
            log = agent.memory.get_recent_log(n_lines=10)
            assert "hello" in log.upper() or "Observation" in log

    def test_memorize_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = DummyAgent(tmp)
            agent.run_tool("scraper")
            log = agent.memory.get_recent_log(n_lines=10)
            assert "scraper" in log or "run_tool" in log

    def test_standalone_decorator_with_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            from hermes_okf.memory import HermesMemory

            mem = HermesMemory(tmp, agent_id="standalone")

            @memorize_decision(memory=mem)
            def choose(x: int) -> int:
                return x * 2

            choose(7)
            decisions = mem.get_decisions()
            assert len(decisions) == 1
            assert "choose" in decisions[0].body
