
import math
from typing import Dict, Any


def compute_coverage(
    mission_spec: Dict[str, Any],
    cruise_speed_mps: float = 8.0,
    max_flight_time_min: float = 20.0,
) -> Dict[str, Any]:
    """
    Compute coverage pattern (lawnmower) for a rectangular field.

    mission_spec is the JSON produced by mission_planner:
    {
      "area": { "length_m": ..., "width_m": ... },
      "altitude_m": ...,
      "camera_fov_deg": ...,
      "overlap": {
        "frontlap_percent": ...,
        "sidelap_percent": ...
      },
      "constraints": { ... }
    }
    """

    #Extract inputs 
    area = mission_spec.get("area", {})
    length_m = float(area.get("length_m", 0.0))   # X direction
    width_m = float(area.get("width_m", 0.0))     # Y direction

    altitude_m = float(mission_spec.get("altitude_m", 50.0))
    fov_deg = float(mission_spec.get("camera_fov_deg", 78.0))

    overlap = mission_spec.get("overlap", {})
    frontlap_percent = float(overlap.get("frontlap_percent", 75.0))
    sidelap_percent = float(overlap.get("sidelap_percent", 65.0))

    #Ground swath width from FOV and altitude
    #swath = 2 * h * tan(FOV/2)
    fov_rad = math.radians(fov_deg)
    swath_width_m = 2 * altitude_m * math.tan(fov_rad / 2)

    #Leg spacing from sidelap
    sidelap_fraction = sidelap_percent / 100.0
    leg_spacing_m = swath_width_m * (1.0 - sidelap_fraction)

    #Choose sweep direction: along length or along width
    #Option A: legs run along length (X axis), spacing along width (Y axis)
    num_legs_along_length = math.ceil(width_m / leg_spacing_m) if leg_spacing_m > 0 else 1
    path_length_along_length = num_legs_along_length * length_m

    #Option B: legs run along width (Y axis), spacing along length (X axis)
    num_legs_along_width = math.ceil(length_m / leg_spacing_m) if leg_spacing_m > 0 else 1
    path_length_along_width = num_legs_along_width * width_m

    if path_length_along_length <= path_length_along_width:
        sweep_direction = "along_length"
        num_legs = num_legs_along_length
        leg_length_m = length_m
        field_span_m = width_m
    else:
        sweep_direction = "along_width"
        num_legs = num_legs_along_width
        leg_length_m = width_m
        field_span_m = length_m

    #Recompute spacing for selected direction to fit nicely
    if num_legs > 1:
        leg_spacing_m = field_span_m / (num_legs - 1)
    else:
        leg_spacing_m = 0.0

    total_path_length_m = num_legs * leg_length_m

    #Time and battery segments
    total_flight_time_min = (total_path_length_m / cruise_speed_mps) / 60.0
    num_battery_segments = max(1, math.ceil(total_flight_time_min / max_flight_time_min))

    #Generate legs in local coordinates
    #(x, y) in metres with origin at bottom-left corner
    legs = []
    for i in range(num_legs):
        leg_id = i + 1
        offset = i * leg_spacing_m

        if sweep_direction == "along_length":
            # X: 0 -> length_m, Y: alternating
            if i % 2 == 0:
                x_start, y_start = 0.0, offset
                x_end, y_end = leg_length_m, offset
            else:
                x_start, y_start = leg_length_m, offset
                x_end, y_end = 0.0, offset
        else:
            # along_width
            if i % 2 == 0:
                x_start, y_start = offset, 0.0
                x_end, y_end = offset, leg_length_m
            else:
                x_start, y_start = offset, leg_length_m
                x_end, y_end = offset, 0.0

        legs.append(
            {
                "leg_id": leg_id,
                "x_start_m": round(x_start, 3),
                "y_start_m": round(y_start, 3),
                "x_end_m": round(x_end, 3),
                "y_end_m": round(y_end, 3),
            }
        )

    coverage_summary = {
        "sweep_direction": sweep_direction,
        "swath_width_m": round(swath_width_m, 3),
        "leg_spacing_m": round(leg_spacing_m, 3),
        "num_legs": int(num_legs),
        "leg_length_m": round(leg_length_m, 3),
        "total_path_length_m": round(total_path_length_m, 3),
        "cruise_speed_mps": cruise_speed_mps,
        "total_flight_time_min": round(total_flight_time_min, 2),
        "num_battery_segments": int(num_battery_segments),
    }

    return {
        "coverage_summary": coverage_summary,
        "legs": legs,
    }
