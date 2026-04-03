"""UAV Mission Copilot - Conversational Interface"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import preload_memory, FunctionTool
from google.genai import types

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mission_db.mission_repo import init_db, list_missions, get_mission_by_id

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Add it to your .env file.")

APP_NAME = "MissionCopilot"
USER_ID = "pilot_1"

def get_all_missions(max_results: int = 10) -> str:
    """Get list of all missions from database."""
    import json
    missions = list_missions()
    return json.dumps(missions[:max_results], indent=2)


def get_mission_details(mission_id: int) -> str:
    """Get detailed information about a specific mission."""
    import json
    mission = get_mission_by_id(mission_id)
    if not mission:
        return json.dumps({"error": f"Mission {mission_id} not found"})
    return json.dumps(mission, indent=2)


async def create_new_mission(user_request: str) -> str:
    """Create complete mission by running pipeline."""
    import json
    
    try:
        from main import uav_pipeline
        
        runner = InMemoryRunner(agent=uav_pipeline)
        response = await runner.run_debug(user_request)
        
        missions = list_missions()
        if missions:
            latest_mission = missions[0]
            
            return json.dumps({
                "status": "success",
                "mission_id": latest_mission["id"],
                "name": latest_mission["name"],
                "message": f"Mission {latest_mission['id']} created successfully!",
                "files": [
                    f"missions/{latest_mission['id']}/mission_brief.md",
                    f"missions/{latest_mission['id']}/ros_waypoints.json",
                    f"missions/{latest_mission['id']}/ros_config.json"
                ]
            }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "Pipeline completed but no mission found in database"
            }, indent=2)
            
    except Exception as e:
        import traceback
        return json.dumps({
            "status": "error",
            "message": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }, indent=2)


async def auto_save_to_memory(callback_context):
    """Auto-save session to memory."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


copilot_agent = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="MissionCopilot",
    instruction="""You are an intelligent UAV Mission Planning Copilot assistant.

You help pilots:
- CREATE new missions from natural language descriptions
- Review past missions
- Query mission specifications
- Answer questions about regulatory requirements

Available tools:
- create_new_mission: Create a complete new mission (auto-generates ID, runs full pipeline)
- get_all_missions: List all missions in the database
- get_mission_details: Get full details of a specific mission

When users want to plan/create/map something NEW:
- Use create_new_mission with their description
- Example: "Map 300m x 600m at 50m in Sydney" → create_new_mission("300m x 600m at 50m in Sydney")

When they ask about EXISTING missions:
- Use get_all_missions or get_mission_details

Be conversational, helpful, and professional.""",
    tools=[
        preload_memory,
        FunctionTool(create_new_mission),
        FunctionTool(get_all_missions),
        FunctionTool(get_mission_details),
    ],
    after_agent_callback=auto_save_to_memory,
)


session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

runner = Runner(
    agent=copilot_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service,
)


async def chat_session(session_id: str = "default"):
    print("=" * 70)
    print("UAV MISSION COPILOT - CHAT INTERFACE")
    print("=" * 70)
    print(f"\nSession: {session_id}")
    print("Type 'exit' to end the conversation\n")
    
    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
        print("  Started new session")
    except:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
        print("  Resumed existing session")
    
    print("\n" + "-" * 70)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\nCopilot: Goodbye! Fly safe!")
            break
        
        query_content = types.Content(role="user", parts=[types.Part(text=user_input)])
        
        print("\nCopilot: ", end="", flush=True)
        
        full_response = ""
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=query_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    full_response = text
                    print(text)
        
        if not full_response:
            print("[No response]")


async def main():
    init_db()
    session_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    await chat_session(session_id)


if __name__ == "__main__":
    asyncio.run(main())
