"""Mission planner step - the only pipeline step that needs an LLM."""

from __future__ import annotations

import json

from v2.core.agent import Agent
from v2.core.tool import Tool
from v2.core.pipeline import PipelineStep, PipelineContext
from v2.providers.base import LLMProvider
from v2.tools.web_search import web_search

PLANNER_SYSTEM_PROMPT = """\
You are a UAV mission planner agent.
Given a high-level request for mapping/surveying with a drone, \
you must output a mission specification as a single JSON object ONLY.

{
  "area": {
    "length_m": <number>,
    "width_m": <number>
  },
  "altitude_m": <number>,
  "camera_fov_deg": <number>,
  "overlap": {
    "frontlap_percent": <number>,
    "sidelap_percent": <number>
  },
  "estimated_flight": {
    "num_legs": <integer>,
    "total_distance_m": <number>,
    "flight_time_min": <number>
  },
  "constraints": {
    "no_fly_buffer_m": <number>,
    "battery_reserve_percent": <number>
  },
  "regulatory": {
    "country": <string>,
    "authority": <string>,
    "summary": <string>,
    "notes": [<string>, ...]
  },
  "notes": [<string>, ...]
}

Regulations logic:
- If the user mentions a location (city/country), infer the country.
- Use web_search to look up *current* drone/UAS rules for that country.
- Summarise the key requirements in regulatory.summary.
- Add extra details and caveats to regulatory.notes.
- If information is unclear or varies, explicitly say so in regulatory.notes.

General rules:
- Infer reasonable values if the user does not specify something.
- Choose realistic overlaps for mapping (e.g. 70-80 frontlap, 60-70 sidelap).
- Give conservative but realistic flight time estimates.
- Output ONLY raw JSON. No markdown, no ``` fences, no prose.
"""


class MissionPlannerStep(PipelineStep):
    """Uses an LLM + web search to generate a structured mission spec."""

    name = "mission_planner"

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def execute(self, ctx: PipelineContext) -> None:
        search_tool = Tool(web_search)

        agent = Agent(
            provider=self.provider,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            tools=[search_tool],
            name="mission_planner",
        )

        result = await agent.run(ctx.user_request)

        try:
            mission_spec = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                mission_spec = json.loads(result[start:end])
            else:
                raise ValueError(
                    f"Could not parse mission spec from LLM response:\n{result[:300]}"
                )

        ctx.set("mission_spec", mission_spec)
