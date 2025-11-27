import os
import sys
import json
from typing import Dict, Any

# Add project root to path so imports work when running this script directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.coverage_calculator import compute_coverage
from mission_db.mission_repo import get_mission_by_id


def run_coverage_agent(
    mission_spec: Dict[str, Any],
    cruise_speed_mps: float = 8.0,
    max_flight_time_min: float = 20.0,
) -> Dict[str, Any]:
    """
    High-level API for the Coverage Agent.

    Takes mission_spec JSON (from mission_planner) and returns
    a coverage plan (summary + legs).
    """
    coverage_result = compute_coverage(
        mission_spec=mission_spec,
        cruise_speed_mps=cruise_speed_mps,
        max_flight_time_min=max_flight_time_min,
    )
    return coverage_result


if __name__ == "__main__":
    # Get mission spec from database
    # Use mission_id from command line arg or default to latest mission
    mission_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2  # default to mission #2
    
    mission_data = get_mission_by_id(mission_id)
    if not mission_data:
        print(f" Mission #{mission_id} not found in database.")
        sys.exit(1)
    
    print(f" Processing mission #{mission_id}: {mission_data['name']}")
    print(f"   Request: {mission_data['user_request']}\n")
    
    mission_spec = mission_data["mission_spec"]
    result = run_coverage_agent(mission_spec)
    print(json.dumps(result, indent=2))
