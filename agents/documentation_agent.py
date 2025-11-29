import os
import sys
import json
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def create_mission_brief(
    mission_spec_json: str,
    coverage_summary_json: str,
    mission_id: int = 0,
) -> str:
    """
    Create a comprehensive mission brief document.
    
    Args:
        mission_spec_json: Mission specification as JSON string
        coverage_summary_json: Coverage summary as JSON string  
        mission_id: Mission ID number
        
    Returns:
        Mission brief content as string
    """
    mission_spec = json.loads(mission_spec_json)
    coverage_summary = json.loads(coverage_summary_json)
    
    # Build mission brief
    brief = f"""# UAV Mission Brief - Mission #{mission_id:03d}

## Mission Overview

**Area**: {mission_spec['area']['length_m']}m x {mission_spec['area']['width_m']}m
**Altitude**: {mission_spec['altitude_m']}m AGL
**Camera FOV**: {mission_spec['camera_fov_deg']}°

## Flight Parameters

**Number of Legs**: {coverage_summary['num_legs']}
**Leg Length**: {coverage_summary['leg_length_m']}m
**Total Distance**: {coverage_summary['total_path_length_m']}m
**Estimated Flight Time**: {coverage_summary['total_flight_time_min']} minutes
**Battery Segments**: {coverage_summary['num_battery_segments']}
**Sweep Direction**: {coverage_summary['sweep_direction']}

## Coverage Details

**Swath Width**: {coverage_summary['swath_width_m']}m
**Leg Spacing**: {coverage_summary['leg_spacing_m']}m
**Cruise Speed**: {coverage_summary['cruise_speed_mps']} m/s

**Overlap**:
- Front Overlap: {mission_spec['overlap']['frontlap_percent']}%
- Side Overlap: {mission_spec['overlap']['sidelap_percent']}%

## Safety Constraints

**No-Fly Buffer**: {mission_spec.get('constraints', {}).get('no_fly_buffer_m', 'N/A')}m
**Battery Reserve**: {mission_spec.get('constraints', {}).get('battery_reserve_percent', 'N/A')}%

## Regulatory Information

**Country**: {mission_spec.get('regulatory', {}).get('country', 'N/A')}
**Authority**: {mission_spec.get('regulatory', {}).get('authority', 'N/A')}

**Summary**: {mission_spec.get('regulatory', {}).get('summary', 'N/A')}

**Notes**:
"""
    
    # Add regulatory notes
    for note in mission_spec.get('regulatory', {}).get('notes', []):
        brief += f"- {note}\n"
    
    brief += "\n## Mission Notes\n\n"
    
    # Add mission notes
    for note in mission_spec.get('notes', []):
        brief += f"- {note}\n"
    
    # Save to file
    output_dir = f"missions/{mission_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/mission_brief.md", "w") as f:
        f.write(brief)
    
    return brief


# ADK Agent for documentation
documentation_agent = Agent(
    name="documentation_agent",
    model="gemini-2.5-flash-lite",
    description="Creates comprehensive mission briefing documents",
    instruction="""You are a documentation specialist for UAV missions.

You receive:
- mission_spec: {mission_spec}
- coverage_plan: {coverage_plan}

Your task:
1. Extract the mission_spec and coverage_summary from coverage_plan
2. Call create_mission_brief with the JSON strings
3. Present a summary of the brief created

Format your response professionally.""",
    tools=[FunctionTool(create_mission_brief)],
    output_key="mission_brief",
)

