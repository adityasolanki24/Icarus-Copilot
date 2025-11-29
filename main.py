"""
UAV Mission Planning System - Multi-Agent Orchestrator
Following ADK Sequential/Parallel Agent Patterns from Kaggle Notebooks

Pipeline:
  mission_planner → coverage_agent → [ros_config_agent || documentation_agent]
                                            (parallel)
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import specialized agents and tools
from agents.mission_planner import mission_planner
from agents.coverage_agent import run_coverage_agent
from agents.ros_config_agent import generate_ros_waypoints, generate_ros_config
from agents.documentation_agent import create_mission_brief
from mission_db.mission_repo import init_db, create_mission_with_spec

load_dotenv()

# Verify API key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Add it to your .env file.")


# === STEP 1: Database Saver Agent ===
# This agent saves mission specs to the database
def save_mission_to_db(mission_spec_json: str, user_request: str) -> str:
    """Save mission specification to database."""
    import json
    
    # Extract JSON if it contains extra text
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    mission_id = create_mission_with_spec(
        user_request=user_request,
        mission_spec=mission_spec,
        name=f"Mission from pipeline"
    )
    
    return json.dumps({
        "mission_id": mission_id,
        "status": "saved",
        "message": f"Mission #{mission_id} saved successfully"
    })


db_saver_agent = Agent(
    name="db_saver_agent",
    model="gemini-2.5-flash-lite",
    description="Saves mission specifications to database",
    instruction="""You receive mission_spec: {mission_spec}

Call save_mission_to_db with the mission spec JSON and confirm it was saved.""",
    tools=[FunctionTool(save_mission_to_db)],
    output_key="db_result",
)


# === STEP 2: Coverage Agent (as ADK Agent) ===
def calculate_coverage(mission_spec_json: str) -> str:
    """Calculate coverage plan from mission spec."""
    import json
    
    # Extract JSON if it contains extra text
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    result = run_coverage_agent(mission_spec)
    return json.dumps(result)


coverage_agent = Agent(
    name="coverage_agent",
    model="gemini-2.5-flash-lite",
    description="Calculates flight coverage patterns",
    instruction="""You receive mission_spec: {mission_spec}

Call calculate_coverage with the mission spec JSON.
Present the coverage summary clearly.""",
    tools=[FunctionTool(calculate_coverage)],
    output_key="coverage_plan",
)


# === STEP 3: ROS Config Agent (as ADK Agent) ===
def generate_ros_package(mission_spec_json: str, coverage_plan_json: str) -> str:
    """Generate ROS2 waypoints and config."""
    import json
    
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    try:
        coverage_plan = json.loads(coverage_plan_json)
    except json.JSONDecodeError:
        start = coverage_plan_json.find("{")
        end = coverage_plan_json.rfind("}") + 1
        coverage_plan = json.loads(coverage_plan_json[start:end])
    
    waypoints = generate_ros_waypoints(coverage_plan, mission_spec)
    config = generate_ros_config(mission_spec, coverage_plan)
    
    ros_package = {
        "waypoints": waypoints,
        "config": config,
        "total_waypoints": len(waypoints),
    }
    
    from mission_db.mission_repo import list_missions
    missions = list_missions()
    if missions:
        mission_id = missions[0]["id"]
        output_dir = f"missions/{mission_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/ros_waypoints.json", "w") as f:
            json.dump(waypoints, f, indent=2)
        
        with open(f"{output_dir}/ros_config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    return json.dumps(ros_package)


ros_config_agent = Agent(
    name="ros_config_agent",
    model="gemini-2.5-flash-lite",
    description="Generates ROS2 configuration files",
    instruction="""You receive:
- mission_spec: {mission_spec}
- coverage_plan: {coverage_plan}

Call generate_ros_package with both JSONs.
Confirm ROS config was generated successfully.""",
    tools=[FunctionTool(generate_ros_package)],
    output_key="ros_config",
)


# === STEP 4: Documentation Agent (as ADK Agent) ===
def generate_mission_brief(mission_spec_json: str, coverage_plan_json: str) -> str:
    """Generate mission briefing document."""
    import json
    
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    try:
        coverage_plan = json.loads(coverage_plan_json)
    except json.JSONDecodeError:
        start = coverage_plan_json.find("{")
        end = coverage_plan_json.rfind("}") + 1
        coverage_plan = json.loads(coverage_plan_json[start:end])
    
    coverage_summary = coverage_plan.get("coverage_summary", {})
    
    from mission_db.mission_repo import list_missions
    missions = list_missions()
    mission_id = missions[0]["id"] if missions else 0
    
    brief = create_mission_brief(
        mission_spec_json=mission_spec_json,
        coverage_summary_json=json.dumps(coverage_summary),
        mission_id=mission_id,
    )
    
    return brief


documentation_agent = Agent(
    name="documentation_agent",
    model="gemini-2.5-flash-lite",
    description="Creates mission briefing documents",
    instruction="""You receive:
- mission_spec: {mission_spec}
- coverage_plan: {coverage_plan}

Call generate_mission_brief with both JSONs.
Confirm the brief was created successfully.""",
    tools=[FunctionTool(generate_mission_brief)],
    output_key="mission_brief",
)


# === MULTI-AGENT PIPELINE ===
# Following the notebook pattern: Sequential → Parallel

# Parallel team for ROS config and documentation (independent tasks)
parallel_output_team = ParallelAgent(
    name="ParallelOutputTeam",
    sub_agents=[
        ros_config_agent,
        documentation_agent,
    ],
)

# Main sequential pipeline
uav_pipeline = SequentialAgent(
    name="UAV_Mission_Pipeline",
    sub_agents=[
        mission_planner,         # Step 1: Generate mission spec with regulations
        db_saver_agent,          # Step 2: Save to database
        coverage_agent,          # Step 3: Calculate coverage
        parallel_output_team,    # Step 4: Generate ROS config + docs in parallel
    ],
)


async def main():
    """Main entry point"""
    
    # Initialize database
    init_db()
    
    # Get user request
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        user_request = (
            "I want to map a 500m x 300m field at 70m altitude for crop health "
            "with a 78 degree FOV camera. I wanna fly it in Delhi"
        )
    
    print("=" * 70)
    print("UAV MISSION PLANNING SYSTEM")
    print("Multi-Agent Pipeline (Sequential + Parallel)")
    print("=" * 70)
    print(f"\nUser Request: {user_request}\n")
    print("Running pipeline: mission_planner → db_saver → coverage → [ros_config || docs]\n")
    
    # Run the entire pipeline
    runner = InMemoryRunner(agent=uav_pipeline)
    response = await runner.run_debug(user_request)
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print("\nAll agents executed successfully!")
    print("- Mission specification generated")
    print("- Mission saved to database")
    print("- Coverage plan calculated")
    print("- ROS config generated (parallel)")
    print("- Mission brief created (parallel)")


if __name__ == "__main__":
    asyncio.run(main())
