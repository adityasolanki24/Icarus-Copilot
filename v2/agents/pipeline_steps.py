"""Deterministic pipeline steps - no LLM calls, pure Python logic.

These import the v1 utility modules (coverage_calculator, mission_repo,
ros_config_agent functions, documentation_agent functions) which are
already provider-agnostic.
"""

from __future__ import annotations

import json
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.coverage_calculator import compute_coverage
from mission_db.mission_repo import init_db, create_mission_with_spec
from agents.ros_config_agent import generate_ros_waypoints, generate_ros_config
from agents.documentation_agent import create_mission_brief

from v2.core.pipeline import PipelineStep, PipelineContext


class DBSaveStep(PipelineStep):
    """Save the mission spec to SQLite and store the mission_id in context."""

    name = "db_saver"

    async def execute(self, ctx: PipelineContext) -> None:
        init_db()
        mission_spec = ctx.get("mission_spec")

        mission_id = create_mission_with_spec(
            user_request=ctx.user_request,
            mission_spec=mission_spec,
            name="Mission from v2 pipeline",
        )

        ctx.set("mission_id", mission_id)
        print(f"    Saved mission #{mission_id} to database")


class CoverageStep(PipelineStep):
    """Compute lawnmower coverage pattern (pure geometry, no LLM)."""

    name = "coverage_calculator"

    async def execute(self, ctx: PipelineContext) -> None:
        mission_spec = ctx.get("mission_spec")
        coverage = compute_coverage(mission_spec)
        ctx.set("coverage_plan", coverage)

        summary = coverage.get("coverage_summary", {})
        print(
            f"    Coverage: {summary.get('num_legs', 0)} legs, "
            f"{summary.get('total_path_length_m', 0):.0f}m total, "
            f"{summary.get('total_flight_time_min', 0):.1f} min"
        )


class ROSConfigStep(PipelineStep):
    """Generate ROS2 waypoints + config and write to missions/<id>/."""

    name = "ros_config"

    async def execute(self, ctx: PipelineContext) -> None:
        coverage_plan = ctx.get("coverage_plan")
        mission_spec = ctx.get("mission_spec")
        mission_id = ctx.get("mission_id", 0)

        waypoints = generate_ros_waypoints(coverage_plan, mission_spec)
        config = generate_ros_config(mission_spec, coverage_plan)

        ctx.set("ros_waypoints", waypoints)
        ctx.set("ros_config", config)

        if mission_id:
            output_dir = f"missions/{mission_id}"
            os.makedirs(output_dir, exist_ok=True)

            with open(f"{output_dir}/ros_waypoints.json", "w") as f:
                json.dump(waypoints, f, indent=2)
            with open(f"{output_dir}/ros_config.json", "w") as f:
                json.dump(config, f, indent=2)

            print(f"    ROS config saved to missions/{mission_id}/")


class DocumentationStep(PipelineStep):
    """Generate the mission brief markdown and write to missions/<id>/."""

    name = "documentation"

    async def execute(self, ctx: PipelineContext) -> None:
        mission_spec = ctx.get("mission_spec")
        coverage_plan = ctx.get("coverage_plan")
        mission_id = ctx.get("mission_id", 0)

        coverage_summary = coverage_plan.get("coverage_summary", {})

        brief = create_mission_brief(
            mission_spec_json=json.dumps(mission_spec),
            coverage_summary_json=json.dumps(coverage_summary),
            mission_id=mission_id,
        )

        ctx.set("mission_brief", brief)
        print(f"    Mission brief saved to missions/{mission_id}/mission_brief.md")
