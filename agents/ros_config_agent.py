import os
import sys
import json
from typing import Dict, Any, List


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mission_db.mission_repo import get_mission_by_id
from agents.coverage_agent import run_coverage_agent


def generate_ros_waypoints(
    coverage_plan: Dict[str, Any],
    mission_spec: Dict[str, Any],
    origin_lat: float = 28.6139,  # Default: Delhi
    origin_lon: float = 77.2090,
) -> List[Dict[str, Any]]:
    """
    Convert coverage legs to ROS2 GPS waypoints.
    
    Args:
        coverage_plan: Coverage plan from coverage_agent
        mission_spec: Mission specification with altitude
        origin_lat: Reference latitude for the mission area
        origin_lon: Reference longitude for the mission area
        
    Returns:
        List of waypoint dictionaries with GPS coordinates
    """
    waypoints = []
    legs = coverage_plan.get("legs", [])
    altitude = mission_spec.get("altitude_m", 50.0)
    
    # Approximate conversion: 1 meter ≈ 0.00001 degrees (rough estimate)
    # For more accurate conversion, use proper geodetic calculations
    meters_to_lat = 1.0 / 111320.0  # 1 degree latitude ≈ 111.32 km
    meters_to_lon = 1.0 / (111320.0 * abs(origin_lat / 90.0))  # Adjusted for latitude
    
    for leg in legs:
        # Start waypoint
        waypoints.append({
            "id": len(waypoints) + 1,
            "type": "waypoint",
            "latitude": origin_lat + (leg["y_start_m"] * meters_to_lat),
            "longitude": origin_lon + (leg["x_start_m"] * meters_to_lon),
            "altitude": altitude,
            "leg_id": leg["leg_id"],
            "position": "start",
        })
        
        # End waypoint
        waypoints.append({
            "id": len(waypoints) + 1,
            "type": "waypoint",
            "latitude": origin_lat + (leg["y_end_m"] * meters_to_lat),
            "longitude": origin_lon + (leg["x_end_m"] * meters_to_lon),
            "altitude": altitude,
            "leg_id": leg["leg_id"],
            "position": "end",
        })
    
    return waypoints


def generate_ros_config(
    mission_spec: Dict[str, Any],
    coverage_plan: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate ROS2 configuration parameters.
    
    Args:
        mission_spec: Mission specification
        coverage_plan: Coverage plan with flight details
        
    Returns:
        ROS2 configuration dictionary
    """
    summary = coverage_plan.get("coverage_summary", {})
    
    config = {
        "mission_parameters": {
            "altitude_m": mission_spec.get("altitude_m", 50.0),
            "cruise_speed_mps": summary.get("cruise_speed_mps", 8.0),
            "camera_fov_deg": mission_spec.get("camera_fov_deg", 78.0),
            "overlap": mission_spec.get("overlap", {}),
        },
        "flight_parameters": {
            "num_waypoints": len(coverage_plan.get("legs", [])) * 2,
            "total_distance_m": summary.get("total_path_length_m", 0),
            "estimated_flight_time_min": summary.get("total_flight_time_min", 0),
            "num_battery_segments": summary.get("num_battery_segments", 1),
        },
        "safety_parameters": {
            "no_fly_buffer_m": mission_spec.get("constraints", {}).get("no_fly_buffer_m", 100),
            "battery_reserve_percent": mission_spec.get("constraints", {}).get("battery_reserve_percent", 20),
            "max_wind_speed_mps": 10.0,
            "return_to_home_altitude_m": mission_spec.get("altitude_m", 50.0) + 20,
        },
        "regulatory": mission_spec.get("regulatory", {}),
    }
    
    return config


def run_ros_config_agent(
    mission_spec: Dict[str, Any],
    coverage_plan: Dict[str, Any],
    origin_lat: float = 28.6139,
    origin_lon: float = 77.2090,
) -> Dict[str, Any]:
    """
    Generate complete ROS2 mission package.
    
    Args:
        mission_spec: Mission specification
        coverage_plan: Coverage plan from coverage_agent
        origin_lat: Mission origin latitude
        origin_lon: Mission origin longitude
        
    Returns:
        Complete ROS2 package with waypoints and config
    """
    waypoints = generate_ros_waypoints(
        coverage_plan=coverage_plan,
        mission_spec=mission_spec,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
    )
    
    config = generate_ros_config(
        mission_spec=mission_spec,
        coverage_plan=coverage_plan,
    )
    
    ros_package = {
        "waypoints": waypoints,
        "config": config,
        "metadata": {
            "total_waypoints": len(waypoints),
            "origin": {
                "latitude": origin_lat,
                "longitude": origin_lon,
            },
            "coordinate_system": "WGS84",
        }
    }
    
    return ros_package


if __name__ == "__main__":
    # Get mission spec from database
    mission_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    
    mission_data = get_mission_by_id(mission_id)
    if not mission_data:
        print(f"Mission #{mission_id} not found in database.")
        sys.exit(1)
    
    print(f"Processing mission #{mission_id}: {mission_data['name']}")
    print(f"Request: {mission_data['user_request']}\n")
    
    mission_spec = mission_data["mission_spec"]
    
    # Generate coverage plan
    print("Step 1: Generating coverage plan...")
    coverage_plan = run_coverage_agent(mission_spec)
    
    # Generate ROS config
    print("Step 2: Generating ROS2 configuration...\n")
    ros_package = run_ros_config_agent(
        mission_spec=mission_spec,
        coverage_plan=coverage_plan,
        origin_lat=28.6139,  # Delhi coordinates (default)
        origin_lon=77.2090,
    )
    
    print("=" * 70)
    print("ROS2 MISSION PACKAGE")
    print("=" * 70)
    print(json.dumps(ros_package, indent=2))
    
    # Optionally save to file
    output_dir = f"missions/{mission_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/ros_waypoints.json", "w") as f:
        json.dump(ros_package["waypoints"], f, indent=2)
    
    with open(f"{output_dir}/ros_config.json", "w") as f:
        json.dump(ros_package["config"], f, indent=2)
    
    print(f"\nFiles saved to {output_dir}/")
    print("  - ros_waypoints.json")
    print("  - ros_config.json")

