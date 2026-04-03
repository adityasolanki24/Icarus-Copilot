"""
UAV Mission Planning System v2 - Provider-Agnostic Pipeline

Supports: Google Gemini, OpenAI GPT, Anthropic Claude

Usage:
    python -m v2.main "Map 500m x 300m field at 70m altitude in Delhi"

    LLM_PROVIDER=openai python -m v2.main "Map a 200m x 200m park"

    LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514 python -m v2.main "Survey 1km field"

Environment variables:
    LLM_PROVIDER : google | openai | anthropic  (default: google)
    LLM_MODEL    : model name override           (default: auto per provider)
    GOOGLE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
"""

import os
import sys
import asyncio
import logging

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from v2 import config
from v2.providers import create_provider
from v2.core.pipeline import Pipeline, ParallelStep, PipelineContext
from v2.agents.mission_planner import MissionPlannerStep
from v2.agents.pipeline_steps import (
    DBSaveStep,
    CoverageStep,
    ROSConfigStep,
    DocumentationStep,
)
from mission_db.mission_repo import init_db


def build_pipeline(provider):
    """Construct the full mission-planning pipeline."""
    return Pipeline(
        name="UAV_Mission_Pipeline_v2",
        steps=[
            MissionPlannerStep(provider),      # LLM: NL → structured spec
            DBSaveStep(),                      # pure fn: spec → SQLite
            CoverageStep(),                    # pure fn: spec → coverage plan
            ParallelStep("outputs", [          # parallel pure fns
                ROSConfigStep(),               #   coverage → ROS waypoints + config
                DocumentationStep(),           #   spec + coverage → mission_brief.md
            ]),
        ],
    )


async def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    init_db()

    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        user_request = (
            "I want to map a 500m x 300m field at 70m altitude for crop health "
            "with a 78 degree FOV camera. I wanna fly it in Delhi"
        )

    provider_name = config.LLM_PROVIDER
    model_name = config.get_model()

    print("=" * 70)
    print("UAV MISSION PLANNING SYSTEM v2")
    print(f"Provider: {provider_name} | Model: {model_name}")
    print("=" * 70)
    print(f"\nUser Request: {user_request}\n")
    print("Running pipeline: planner -> db -> coverage -> [ros_config || docs]\n")

    provider = create_provider()
    pipeline = build_pipeline(provider)

    ctx = PipelineContext(user_request=user_request)
    await pipeline.run(ctx)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    mission_id = ctx.get("mission_id")
    if mission_id:
        print(f"\nMission #{mission_id} created successfully!")
        print(f"  - missions/{mission_id}/mission_brief.md")
        print(f"  - missions/{mission_id}/ros_waypoints.json")
        print(f"  - missions/{mission_id}/ros_config.json")


if __name__ == "__main__":
    asyncio.run(main())
