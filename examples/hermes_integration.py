from hermes_okf.agent import HermesMemoryMixin

class MyAgent(HermesMemoryMixin):
    def __init__(self):
        super().__init__("./agent_knowledge", agent_id="my-agent-v1")
        self.start_session()
        # Apply memory wrappers after super().__init__
        self.choose_model = self.wrap_decision(self.choose_model)
        self.scrape_data = self.wrap_tool(self.scrape_data)

    def choose_model(self, task: str) -> str:
        """Pick an LLM model based on the task."""
        if "code" in task.lower():
            return "anthropic/claude-3.5-sonnet"
        return "openai/gpt-4o"

    def scrape_data(self, url: str) -> dict:
        """Simulate a web scraping tool."""
        return {"url": url, "items": 42}

    def run(self):
        model = self.choose_model("Write a Python script")
        print(f"Selected model: {model}")

        data = self.scrape_data("https://example.com")
        print(f"Scraped: {data}")

        # Recall relevant context
        context = self.with_context("python script", top_k=3)
        print(f"Recalled {len(context)} relevant concepts")

        self.end_session("session-001")

if __name__ == "__main__":
    agent = MyAgent()
    agent.run()
