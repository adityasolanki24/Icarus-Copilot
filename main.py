import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search

load_dotenv()  # Load .env

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Add it to your .env file.")

MODEL_NAME = "gemini-2.5-pro"
PROJECT_NAME = "Agents Intensive Capstone"

root_agent = Agent(
    name="helpful_assistant",
    model="gemini-2.5-flash-lite",
    description="A simple agent that can answer general questions.",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search],
)

async def main():
    runner = InMemoryRunner(agent=root_agent)
    response = await runner.run_debug(
        "Who is a good boy"
    )

# Run the async main() function
asyncio.run(main())
