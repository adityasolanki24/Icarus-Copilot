import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search

# Add project root to path so imports work when running this script directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mission_db.mission_repo import init_db, create_mission_with_spec  # 👈 new import

load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Add it to your .env file.")

mission_planner = Agent(
    name="mission_planner",
    model="gemini-2.5-flash-lite",
    description="Plans autonomous UAV survey missions from high-level user requests.",
    tools=[google_search],
    instruction=(
        "You are a UAV mission planner agent.\n"
        "Given a high-level request for mapping/surveying with a drone, "
        "you must output a mission specification as a single JSON object ONLY.\n\n"
        "{\n"
        '  \"area\": {\n'
        '    \"length_m\": <number>,\n'
        '    \"width_m\": <number>\n'
        "  },\n"
        '  \"altitude_m\": <number>,\n'
        '  \"camera_fov_deg\": <number>,\n'
        '  \"overlap\": {\n'
        '    \"frontlap_percent\": <number>,\n'
        '    \"sidelap_percent\": <number>\n'
        "  },\n"
        '  \"estimated_flight\": {\n'
        '    \"num_legs\": <integer>,\n'
        '    \"total_distance_m\": <number>,\n'
        '    \"flight_time_min\": <number>\n'
        "  },\n"
        '  \"constraints\": {\n'
        '    \"no_fly_buffer_m\": <number>,\n'
        '    \"battery_reserve_percent\": <number>\n'
        "  },\n"
        '  \"regulatory\": {\n'
        '    \"country\": <string>,\n'
        '    \"authority\": <string>,\n'
        '    \"summary\": <string>,\n'
        '    \"notes\": [<string>, ...]\n'
        "  },\n"
        '  \"notes\": [<string>, ...]\n'
        "}\n\n"
        "Regulations logic:\n"
        "- If the user mentions a location (city/country), infer the country.\n"
        "- Use google_search to look up *current* drone/UAS rules for that country.\n"
        "- Summarise the key requirements in regulatory.summary.\n"
        "- Add extra details and caveats to regulatory.notes.\n"
        "- If information is unclear or varies, explicitly say so in regulatory.notes.\n\n"
        "General rules:\n"
        "- Infer reasonable values if the user does not specify something.\n"
        "- Choose realistic overlaps for mapping (e.g. 70–80 frontlap, 60–70 sidelap).\n"
        "- Give conservative but realistic flight time estimates.\n"
        "- Output ONLY raw JSON. No markdown, no ``` fences, no prose.\n"
    ),
)


async def mission_planner_main():
    # make sure DB exists
    init_db()

    runner = InMemoryRunner(agent=mission_planner)

    # later this will come from CLI / UI
    user_request = (
        "I want to map a 500m x 300m field at 70m altitude for crop health "
        "with a 78° FOV camera. I wanna fly it in delhi"
    )

    events = await runner.run_debug(user_request)

    # last event should contain the JSON text
    last = events[-1]
    text = getattr(last, "output", None) or getattr(last, "content", None) or str(last)
    text = str(text)

    json_str = text[text.find("{"): text.rfind("}") + 1]
    mission_spec = json.loads(json_str)

    # store everything in SQLite
    mission_id = create_mission_with_spec(
        user_request=user_request,
        mission_spec=mission_spec,
        name="Delhi crop health survey",
    )

    print(f"\n Saved mission #{mission_id} into missions.db")
    print("(Use this mission_id for coverage, ROS config, etc.)")


if __name__ == "__main__":
    asyncio.run(mission_planner_main())
