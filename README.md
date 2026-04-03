# Project Icarus — Mission Copilot

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-412991.svg)](https://platform.openai.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97757.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E.svg)](https://docs.ros.org/)

> **AI-Driven Autonomous Drone Mission Planner**  
> *Automating mission planning, trajectory generation, and ROS2 configuration for UAV operations*

---

## Overview

**Mission Copilot** is an AI-powered mission-planning system that generates complete, flight-ready mission packages for autonomous UAV operations. Developed as part of the **Google × Kaggle Agents Intensive Capstone**, this system eliminates manual mission planning by transforming natural language descriptions into structured, executable flight plans.

Mission Copilot directly supports **Project Icarus**, my broader engineering initiative focused on building a fully autonomous drone platform capable of real-time mapping, computer vision tasks, and advanced mission execution.

The project ships in two versions:
- **v1** — Built on the Google Agent Development Kit (ADK), tightly integrated with Gemini
- **v2** — Provider-agnostic rewrite that runs on **Google Gemini, OpenAI GPT, or Anthropic Claude** with a single env-var switch

### Key Features

- **Natural Language Mission Planning** — Describe missions in plain English
- **Multi-Provider LLM Support (v2)** — Swap between Gemini, GPT, and Claude via `LLM_PROVIDER`
- **Regulatory Compliance Checking** — Automated lookup of local drone regulations
- **Automated Coverage Path Calculations** — Optimized lawnmower patterns for mapping and surveying
- **Flight Time and Battery Estimation** — Realistic mission feasibility analysis
- **Persistent Mission Storage** — SQLite database for mission history and retrieval
- **Multi-Agent Architecture** — Specialized agents working in coordination

---

## Background: Project Icarus

**Project Icarus** is a long-term personal project where I am building a complete autonomous drone system. More about Project Icarus: https://github.com/adityasolanki24/Project-Icarus

**Mission Copilot fills a critical gap** by providing an automated, engineer-level mission planning system that generates accurate, repeatable, and execution-ready flight plans.

---

## System Architecture

Both v1 and v2 follow the same **multi-agent pipeline**. The key difference is that v1 wraps every step in a Google ADK `Agent` (each making an LLM call), while v2 only uses an LLM for the mission planner — all other steps are direct function calls.

```
User Input (Natural Language)
    ↓
┌─────────────────────────────────────────┐
│   Mission Planner          [LLM]       │
│   → Parses natural language             │
│   → Searches regulations (web search)   │
│   → Generates mission spec JSON         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Database Saver           [function]  │
│   → Saves mission to SQLite             │
│   → Returns mission_id                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Coverage Calculator      [function]  │
│   → Calculates lawnmower pattern        │
│   → Determines swath width & leg spacing│
│   → Estimates flight time & batteries   │
└─────────────────────────────────────────┘
    ↓
┌──────────────────────┬──────────────────────┐
│  ROS Config          │  Documentation       │
│  [function, parallel]│  [function, parallel]│
│  → Waypoints JSON    │  → Mission Brief MD  │
│  → ROS2 config       │  → Flight summary    │
└──────────────────────┴──────────────────────┘
    ↓
Mission Package saved to missions/{mission_id}/
```

### v1 vs v2 Comparison

| Aspect | v1 (Google ADK) | v2 (Provider-agnostic) |
|--------|----------------|----------------------|
| **LLM Providers** | Google Gemini only | Google Gemini, OpenAI GPT, Anthropic Claude |
| **Framework** | Google ADK (`Agent`, `SequentialAgent`, `ParallelAgent`) | Custom lightweight framework — zero vendor lock-in |
| **Pipeline efficiency** | Every step wrapped in an LLM agent | Only mission planner uses LLM; all other steps are direct function calls |
| **Web search** | Google's proprietary `google_search` | DuckDuckGo (free, no API key required) |
| **Chat memory** | ADK `InMemorySessionService` / `InMemoryMemoryService` | `ChatSession` with message history |
| **Tool system** | ADK `FunctionTool` | Auto-generates JSON Schema from Python type hints |

### Pipeline Steps

| Step | Needs LLM? | Responsibility |
|------|-----------|----------------|
| **Mission Planner** | Yes | Interprets natural language requests, searches regulations via web search, generates structured mission specifications (area, altitude, camera FOV, overlap percentages) |
| **Database Saver** | No | Persists mission specs to SQLite, assigns mission_id, enables mission retrieval and history tracking |
| **Coverage Calculator** | No | Calculates optimal flight paths using lawnmower patterns, determines swath width from camera FOV and altitude, estimates total flight time and battery requirements |
| **ROS Config** | No | Generates ROS2-compatible waypoint files and configuration JSON for autonomous flight execution |
| **Documentation** | No | Creates human-readable mission briefs with flight parameters, regulatory notes, and operational summaries |

---

## Repository Structure

```
Capstone-agent/
├── main.py                          # v1 pipeline orchestrator (ADK)
├── chat.py                          # v1 chat interface (ADK)
├── pipeline.py                      # v1 pipeline definition
├── test_connection.py               # Network connectivity diagnostics
├── agents/                          # v1 agent definitions (ADK)
│   ├── mission_planner.py           # Mission spec generation + regulatory lookup
│   ├── coverage_agent.py            # Coverage path calculation wrapper
│   ├── ros_config_agent.py          # ROS2 waypoint & config generation
│   └── documentation_agent.py       # Mission brief creation
├── tools/                           # Shared calculation tools (used by v1 and v2)
│   └── coverage_calculator.py       # Lawnmower pattern algorithms
├── mission_db/                      # Shared database persistence (used by v1 and v2)
│   └── mission_repo.py              # SQLite operations
├── v2/                              # v2 provider-agnostic system
│   ├── main.py                      # v2 pipeline entry point
│   ├── chat.py                      # v2 chat copilot
│   ├── config.py                    # Provider/model configuration
│   ├── requirements.txt             # v2 dependencies
│   ├── core/                        # Framework internals
│   │   ├── types.py                 # Message, ToolCall, ToolDef
│   │   ├── tool.py                  # Tool with JSON-Schema extraction
│   │   ├── agent.py                 # Agent + ChatSession
│   │   └── pipeline.py              # Pipeline, ParallelStep, FunctionStep
│   ├── providers/                   # LLM provider implementations
│   │   ├── base.py                  # Abstract LLMProvider interface
│   │   ├── google_provider.py       # Google Gemini (via google-genai)
│   │   ├── openai_provider.py       # OpenAI GPT (+ compatible APIs)
│   │   └── anthropic_provider.py    # Anthropic Claude
│   ├── agents/                      # Mission-specific steps
│   │   ├── mission_planner.py       # LLM-based mission planning
│   │   └── pipeline_steps.py        # DB, coverage, ROS, docs (pure Python)
│   └── tools/
│       └── web_search.py            # DuckDuckGo search (free, no API key)
├── missions/                        # Generated outputs (gitignored)
│   └── {mission_id}/
│       ├── mission_brief.md
│       ├── ros_waypoints.json
│       └── ros_config.json
├── .env                             # API keys (not in repo)
├── .gitignore
├── missions.db                      # Mission database
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **At least one LLM API key** (see below)
- **pip** or **conda** for package management

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/adityasolanki24/Icarus-Copilot.git
cd Icarus-Copilot
```

2. **Create a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

For **v1** (Google ADK only):
```bash
pip install google-adk python-dotenv
```

For **v2** (multi-provider):
```bash
pip install -r v2/requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the root directory with keys for the providers you want to use:

```bash
# Required for v1, optional for v2
GOOGLE_API_KEY=your_google_api_key_here

# v2 provider selection (default: google)
LLM_PROVIDER=google          # google | openai | anthropic
LLM_MODEL=                   # optional model override

# Add keys for providers you want to use with v2
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

API key sources:
- Google: [Google AI Studio](https://aistudio.google.com/app/apikey)
- OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)
- Anthropic: [Anthropic Console](https://console.anthropic.com/)

### Configuration

Default models per provider (override with `LLM_MODEL`):

| Provider | Default Model |
|----------|--------------|
| `google` | `gemini-2.5-flash` |
| `openai` | `gpt-4o-mini` |
| `anthropic` | `claude-sonnet-4-20250514` |

---

## Usage

### v2 (Recommended — Multi-Provider)

**Chat interface:**
```bash
python -m v2.chat
```

**Pipeline (single run):**
```bash
python -m v2.main "Map 500m x 300m field at 70m altitude in Delhi"
```

**Switch providers on the fly:**
```bash
# Google Gemini (default)
python -m v2.main "Survey a 200m x 200m park in Sydney"

# OpenAI GPT
LLM_PROVIDER=openai python -m v2.main "Map a 1km corridor along a pipeline"

# Anthropic Claude
LLM_PROVIDER=anthropic python -m v2.main "Inspect a 300m bridge"

# Override model
LLM_PROVIDER=openai LLM_MODEL=gpt-4o python -m v2.chat
```

### v1 (Google ADK)

**Chat interface:**
```bash
python chat.py
```

**Pipeline:**
```bash
python main.py
```

**Individual agents:**
```bash
python agents/mission_planner.py
python agents/coverage_agent.py <mission_id>
python agents/ros_config_agent.py <mission_id>
```

### Chat Example

```
You: Create a mission to map a 500m x 300m field at 70m altitude in Sydney
Copilot: [Runs full pipeline, saves to missions/18/]

You: What missions have I created?
Copilot: [Lists all missions from database]

You: Tell me about mission 18
Copilot: [Shows full details including regulatory notes]
```

### Expected Output Structure

Each mission produces three files in `missions/{mission_id}/`:

```
missions/
  ├── 1/
  │   ├── mission_brief.md         # Human-readable flight plan
  │   ├── ros_waypoints.json       # GPS waypoints for ROS2
  │   └── ros_config.json          # Flight parameters for ROS2
  ├── 2/
  │   └── ...
  └── ...
```

Mission metadata is also stored in `missions.db` (SQLite).

---

## Technical Stack

| Category | v1 | v2 |
|----------|----|----|
| **AI Framework** | Google ADK | Custom lightweight agent framework |
| **LLM** | Gemini 2.5 Flash Lite | Gemini / GPT / Claude (configurable) |
| **Web Search** | `google_search` (ADK) | DuckDuckGo (free, no key) |
| **Language** | Python 3.11+ | Python 3.11+ |
| **Database** | SQLite 3 | SQLite 3 |
| **Async** | asyncio | asyncio |
| **Config** | python-dotenv | python-dotenv |

---

## Use Cases

- **Agricultural Surveying** — Crop health monitoring, yield estimation
- **Infrastructure Inspection** — Power lines, pipelines, bridges
- **Mapping and GIS** — Topographic surveys, photogrammetry
- **Search and Rescue** — Coverage planning for large search areas
- **Defense and Security** — Reconnaissance mission planning

---

## Testing

Run connectivity tests to verify your setup:

```bash
python test_connection.py
```

Expected output:
```
Connection successful! Status: 200
```

---

## Deployment to Production

Mission Copilot can be deployed to **Vertex AI Agent Engine** for production use with enterprise-grade infrastructure.

### Quick Deploy

```bash
# Set your Google Cloud project
export PROJECT_ID="your-google-cloud-project-id"
export REGION="us-central1"

# Deploy to Agent Engine
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$REGION \
  . \
  --agent_engine_config_file=.agent_engine_config.json
```

### What You Get

- **Managed Runtime**: Auto-scaling infrastructure
- **Session Management**: Built-in conversation persistence
- **Memory Bank**: Long-term knowledge across sessions
- **Observability**: Integrated logging, tracing, and monitoring
- **Enterprise Security**: VPC-SC, CMEK, IAM support
- **REST API**: Accessible from any application

### Cost Management

- **Free Tier**: Agent Engine offers a monthly free tier
- **Auto-scaling**: `min_instances: 0` scales to zero when idle
- **Pay-per-use**: Only pay for active usage

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete deployment guide.

### Alternative Deployment Options

| Platform | Best For | Documentation |
|----------|----------|---------------|
| **Vertex AI Agent Engine** | Production, enterprise scale | [Deploy to Agent Engine](https://cloud.google.com/agent-builder/agent-development-kit/docs/deploy-agent-engine) |
| **Cloud Run** | Simpler serverless deployment | [Deploy to Cloud Run](https://cloud.google.com/agent-builder/agent-development-kit/docs/deploy-cloud-run) |
| **GKE** | Full containerized control | [Deploy to GKE](https://cloud.google.com/agent-builder/agent-development-kit/docs/deploy-gke) |

## Troubleshooting

### Common Issues

#### 1. `ModuleNotFoundError: No module named 'mission_db'`

**Cause:** Python cannot find the project modules when running scripts directly.

**Solution:** The agents now include path fixes. If the error persists, run from project root:
```bash
python -m agents.mission_planner
```

#### 2. `httpx.ConnectError: All connection attempts failed`

**Cause:** Network/firewall blocking Python's outbound connections.

**Solutions:**
- Flush DNS: `ipconfig /flushdns` (Windows)
- Allow Python through Windows Firewall
- Check VPN/proxy settings
- Update certificates: `pip install --upgrade certifi`

#### 3. `GOOGLE_API_KEY not found` / `API key not found for provider`

**Solution (v1):** Ensure `.env` file exists in the project root with `GOOGLE_API_KEY`.

**Solution (v2):** Set the key for your chosen provider — `GOOGLE_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`. Also set `LLM_PROVIDER` to match.

#### 4. Database file not found

**Solution:** The database is created automatically on first run. Ensure you have write permissions in the project directory.

---

## Roadmap

**Completed:**
- [x] Natural language mission specification generation
- [x] Regulatory compliance lookup (Google Search integration)
- [x] Automated coverage path planning (lawnmower patterns)
- [x] Database persistence with SQLite
- [x] ROS2 waypoint and configuration file generation
- [x] Multi-agent pipeline architecture (Sequential + Parallel)
- [x] Conversational chat interface with session management
- [x] Memory-based mission queries and retrieval
<<<<<<< HEAD
- [x] Integration with actual drone hardware (Project Icarus)
=======
- [x] **v2: Multi-provider support (Gemini, GPT, Claude)**
- [x] **v2: Provider-agnostic agent framework (no ADK dependency)**
- [x] **v2: Free web search via DuckDuckGo**
>>>>>>> dbc09d0 (V2)

**In Progress:**
- [ ] Enhanced input validation and error handling
- [ ] Support for custom polygon survey areas
- [ ] Mission editing and versioning

**Future:**
- [ ] Real-time weather API for flight feasibility
- [ ] Obstacle avoidance integration
- [ ] Mission simulation and 3D visualization
- [ ] Integration with actual drone hardware (Project Icarus)

---


## Contact

**Project Maintainer:** Aditya Solanki  
**Project Link:** [https://github.com/adityasolanki24/Icarus-Copilot](https://github.com/adityasolanki24/Icarus-Copilot)  
**Project Icarus:** [https://github.com/adityasolanki24/Project-Icarus](https://github.com/adityasolanki24/Project-Icarus)

---

*Built for autonomous UAV mission planning as part of the Google × Kaggle Agents Intensive Capstone Project. v2 extends the system with multi-provider LLM support.*
