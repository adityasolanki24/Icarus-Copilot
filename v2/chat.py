"""
UAV Mission Copilot v2 - Provider-Agnostic Chat Interface

Usage:
    python -m v2.chat [session_id]

    LLM_PROVIDER=openai python -m v2.chat
"""

import os
import sys
import json
import asyncio

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from v2 import config
from v2.providers import create_provider
from v2.core.agent import Agent, ChatSession
from v2.core.tool import Tool
from v2.core.pipeline import PipelineContext
from mission_db.mission_repo import init_db, list_missions, get_mission_by_id

COPILOT_PROMPT = """\
You are an intelligent UAV Mission Planning Copilot assistant.

You help pilots:
- CREATE new missions from natural language descriptions
- Review past missions
- Query mission specifications
- Answer questions about regulatory requirements

Available tools:
- create_new_mission: Create a complete new mission (runs the full planning pipeline)
- get_all_missions: List all missions in the database
- get_mission_details: Get full details of a specific mission by ID

When users want to plan/create/map something NEW:
- Use create_new_mission with their description
- Example: "Map 300m x 600m at 50m in Sydney" -> call create_new_mission

When they ask about EXISTING missions:
- Use get_all_missions or get_mission_details

Be conversational, helpful, and professional.\
"""

_provider = None


async def create_new_mission(user_request: str) -> str:
    """Create a complete new mission by running the full planning pipeline.

    Args:
        user_request: Natural language description of the mission
    """
    try:
        from v2.main import build_pipeline

        pipeline = build_pipeline(_provider)
        ctx = PipelineContext(user_request=user_request)
        await pipeline.run(ctx)

        mission_id = ctx.get("mission_id")
        if mission_id:
            return json.dumps(
                {
                    "status": "success",
                    "mission_id": mission_id,
                    "message": f"Mission {mission_id} created successfully!",
                    "files": [
                        f"missions/{mission_id}/mission_brief.md",
                        f"missions/{mission_id}/ros_waypoints.json",
                        f"missions/{mission_id}/ros_config.json",
                    ],
                },
                indent=2,
            )
        return json.dumps({"status": "error", "message": "No mission_id produced"})

    except Exception as e:
        import traceback

        return json.dumps(
            {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
            indent=2,
        )


def get_all_missions(max_results: int = 10) -> str:
    """Get list of all missions from database.

    Args:
        max_results: Maximum number of missions to return
    """
    missions = list_missions()
    return json.dumps(missions[:max_results], indent=2)


def get_mission_details(mission_id: int) -> str:
    """Get detailed information about a specific mission.

    Args:
        mission_id: The mission ID to look up
    """
    mission = get_mission_by_id(mission_id)
    if not mission:
        return json.dumps({"error": f"Mission {mission_id} not found"})
    return json.dumps(mission, indent=2)


async def chat_session(session_id: str = "default"):
    global _provider

    provider_name = config.LLM_PROVIDER
    model_name = config.get_model()

    print("=" * 70)
    print("UAV MISSION COPILOT v2 - CHAT INTERFACE")
    print(f"Provider: {provider_name} | Model: {model_name}")
    print("=" * 70)
    print(f"\nSession: {session_id}")
    print("Type 'exit' to end the conversation\n")
    print("-" * 70)

    _provider = create_provider()

    copilot = Agent(
        provider=_provider,
        system_prompt=COPILOT_PROMPT,
        tools=[
            Tool(create_new_mission),
            Tool(get_all_missions),
            Tool(get_mission_details),
        ],
        name="MissionCopilot",
    )

    session = ChatSession(copilot)

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print("\nCopilot: Goodbye! Fly safe!")
            break

        print("\nCopilot: ", end="", flush=True)

        response = await session.send(user_input)

        if response:
            print(response)
        else:
            print("[No response]")


async def main():
    init_db()
    session_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    await chat_session(session_id)


if __name__ == "__main__":
    asyncio.run(main())
