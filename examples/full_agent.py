"""Full Hermes agent example with OKF-native memory.

This demonstrates how a Hermes agent uses OKF as its complete state backend.
Every configuration, session, tool, plan, and decision is stored in the bundle.
The agent can be stopped and resumed at any time.
"""

from hermes_okf.hermes import HermesAgent


def main():
    # Create or resume an agent from its OKF bundle
    agent = HermesAgent(
        bundle_path="./hermes_agent_brain",
        agent_id="hermes-alpha",
        model="anthropic/claude-3.5-sonnet",
    )

    # Register tools the agent can use
    agent.register_tool(
        name="search_web",
        description="Search the web for current information.",
        schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        example='search_web(query="Python 3.12 release date")',
    )
    agent.register_tool(
        name="run_python",
        description="Execute Python code and return the result.",
        schema={
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
        example='run_python(code="print(2 + 2)")',
    )

    # Create a plan for a complex task
    plan_id = agent.create_plan(
        task="Research and summarize AI trends",
        steps=[
            "Search for latest AI news",
            "Summarize key findings",
            "Write a concise report",
        ],
    )
    print(f"Created plan: {plan_id}")

    # Mark steps complete as the agent works
    agent.complete_step(0, result="Found 5 major trends in LLMs and agents")
    agent.complete_step(1, result="Key trend: multi-agent orchestration is growing")
    agent.complete_step(2, result="Report written to output.md")

    # Record a strategic decision
    agent.memory.record_decision(
        "Use Claude for reasoning tasks, GPT-4o for coding tasks",
        rationale="Claude shows better long-context reasoning; GPT-4o is faster for code",
        tags=["model-selection", "architecture"],
    )

    # Build context for an LLM call
    context = agent.build_context(
        query="What model should I use for this task?",
        top_k=3,
    )
    print("\n--- LLM Context ---\n")
    print(context)

    # Save a state snapshot
    agent.snapshot(note="After completing AI trends research")

    # End the session
    agent.end_session()
    print("\nAgent session ended. State preserved in OKF bundle.")

    # --- Later, resume the agent ---
    print("\n--- Resuming agent ---\n")
    resumed = HermesAgent(
        bundle_path="./hermes_agent_brain",
        agent_id="hermes-alpha",
    )
    print(f"Resumed with model: {resumed.model}")
    print(f"Sessions: {resumed.list_sessions()}")
    print(f"Tools: {resumed.list_tools()}")
    print(f"Plans: {resumed.memory.bundle.list_concepts('plans')}")

    # Restore from a specific snapshot if needed
    # resumed.restore("snapshots/...")

    resumed.end_session()


if __name__ == "__main__":
    main()
