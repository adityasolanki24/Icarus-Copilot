"""
Shared UAV Mission Planning Pipeline
Used by both main.py and chat.py
"""
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import FunctionTool
import json


# Import all agent components
from agents.mission_planner import mission_planner
from agents.coverage_agent import run_coverage_agent
from agents.ros_config_agent import run_ros_config_agent
from agents.documentation_agent import create_mission_brief
from mission_db.mission_repo import create_mission_with_spec


# === SHARED PIPELINE TOOLS ===

def save_mission_to_db(mission_spec_json: str, user_request: str) -> str:
    """Save mission specification to database."""
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
        name="Automated mission"
    )
    
    # Store mission_id globally so other functions can access it
    import os
    os.environ['CURRENT_MISSION_ID'] = str(mission_id)
    
    return json.dumps({"mission_id": mission_id, "status": "saved"})


def calculate_coverage(mission_spec_json: str) -> str:
    """Calculate coverage plan from mission spec."""
    # Extract JSON if it contains extra text
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    coverage_result = run_coverage_agent(mission_spec)
    return json.dumps(coverage_result)


def generate_ros_package(mission_spec_json: str, coverage_plan_json: str, db_save_result: str = None) -> str:
    """Generate ROS2 waypoints and config."""
    # Extract mission_id from db_save_result if provided
    mission_id = 0
    if db_save_result:
        try:
            db_result = json.loads(db_save_result)
            mission_id = db_result.get("mission_id", 0)
        except:
            pass
    
    # Fallback to environment variable
    if mission_id == 0:
        import os
        mission_id = int(os.environ.get('CURRENT_MISSION_ID', 0))
    
    # Extract JSON from mission_spec if it contains extra text
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    # Extract JSON from coverage_plan if it contains extra text
    try:
        coverage_plan = json.loads(coverage_plan_json)
    except json.JSONDecodeError:
        start = coverage_plan_json.find("{")
        end = coverage_plan_json.rfind("}") + 1
        coverage_plan = json.loads(coverage_plan_json[start:end])
    
    from agents.ros_config_agent import generate_ros_waypoints, generate_ros_config
    import os
    
    waypoints = generate_ros_waypoints(coverage_plan, mission_spec)
    config = generate_ros_config(mission_spec, coverage_plan)
    
    if mission_id > 0:
        output_dir = f"missions/{mission_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/ros_waypoints.json", "w") as f:
            json.dump(waypoints, f, indent=2)
        
        with open(f"{output_dir}/ros_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        return f"ROS config files created successfully in missions/{mission_id}/"
    else:
        return "ERROR: Could not determine mission_id. Files not saved."


def generate_mission_brief(mission_spec_json: str, coverage_plan_json: str, db_save_result: str = None) -> str:
    """Generate mission briefing document."""
    # Extract mission_id from db_save_result if provided
    mission_id = 0
    if db_save_result:
        try:
            db_result = json.loads(db_save_result)
            mission_id = db_result.get("mission_id", 0)
        except:
            pass
    
    # Fallback to environment variable
    if mission_id == 0:
        import os
        mission_id = int(os.environ.get('CURRENT_MISSION_ID', 0))
    
    # Extract JSON from mission_spec if it contains extra text
    try:
        mission_spec = json.loads(mission_spec_json)
    except json.JSONDecodeError:
        start = mission_spec_json.find("{")
        end = mission_spec_json.rfind("}") + 1
        mission_spec = json.loads(mission_spec_json[start:end])
    
    # Extract JSON from coverage_plan if it contains extra text
    try:
        coverage_plan = json.loads(coverage_plan_json)
    except json.JSONDecodeError:
        start = coverage_plan_json.find("{")
        end = coverage_plan_json.rfind("}") + 1
        coverage_plan = json.loads(coverage_plan_json[start:end])
    
    import os
    
    if mission_id == 0:
        return json.dumps({"status": "error", "message": "No mission_id found"})
    
    output_dir = f"missions/{mission_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    coverage_summary = coverage_plan.get("coverage_summary", {})
    
    brief_content = f"""# Mission {mission_id} Brief

## Mission Specifications
- Area: {mission_spec['area']['length_m']}m x {mission_spec['area']['width_m']}m
- Altitude: {mission_spec['altitude_m']}m
- Camera FOV: {mission_spec['camera_fov_deg']}°

## Coverage Summary
- Flight Legs: {coverage_summary.get('num_legs', 0)}
- Total Distance: {coverage_summary.get('total_path_length_m', 0)}m
- Flight Time: {coverage_summary.get('total_flight_time_min', 0)} min

## Regulatory Information
{json.dumps(mission_spec.get('regulatory', {}), indent=2)}
"""
    
    with open(f"{output_dir}/mission_brief.md", "w") as f:
        f.write(brief_content)
    
    return json.dumps({
        "status": "success",
        "mission_id": mission_id,
        "file_created": f"missions/{mission_id}/mission_brief.md"
    })


# === BUILD PIPELINE AGENTS ===

db_saver_agent = Agent(
    name="db_saver_agent",
    model="gemini-2.5-flash-lite",
    description="Saves mission to database",
    instruction="""Save the mission: {mission_spec}
    
User request was: {user_request}

Call save_mission_to_db with both parameters.
IMPORTANT: Return the JSON response from the function - it contains the mission_id!""",
    tools=[FunctionTool(save_mission_to_db)],
    output_key="db_save_result",
)

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

ros_config_agent = Agent(
    name="ros_config_agent",
    model="gemini-2.5-flash-lite",
    description="Generates ROS2 waypoint files",
    instruction="""You receive:
- mission_spec: {mission_spec}
- coverage_plan: {coverage_plan}
- db_save_result: {db_save_result}

Call generate_ros_package and pass ALL THREE parameters:
generate_ros_package(mission_spec_json=mission_spec, coverage_plan_json=coverage_plan, db_save_result=db_save_result)""",
    tools=[FunctionTool(generate_ros_package)],
    output_key="ros_config_output",
)

documentation_agent = Agent(
    name="documentation_agent",
    model="gemini-2.5-flash-lite",
    description="Creates mission documentation",
    instruction="""You receive:
- mission_spec: {mission_spec}
- coverage_plan: {coverage_plan}
- db_save_result: {db_save_result}

Call generate_mission_brief and pass ALL THREE parameters:
generate_mission_brief(mission_spec_json=mission_spec, coverage_plan_json=coverage_plan, db_save_result=db_save_result)""",
    tools=[FunctionTool(generate_mission_brief)],
    output_key="mission_brief_output",
)

# Define parallel outputs (ROS + Docs)
parallel_outputs_agent = ParallelAgent(
    name="ParallelOutputs",
    sub_agents=[ros_config_agent, documentation_agent],
)

# Define the complete pipeline
uav_pipeline = SequentialAgent(
    name="UAV_Mission_Pipeline",
    sub_agents=[
        mission_planner,
        db_saver_agent,
        coverage_agent,
        parallel_outputs_agent,
    ],
)

