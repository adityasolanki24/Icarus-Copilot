# Project Icarus — Mission Copilot

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E.svg)](https://docs.ros.org/)

> **AI-Driven Autonomous Drone Mission Planner**  
> *Automating mission planning, trajectory generation, and ROS2 configuration for UAV operations*

---

## Overview

**Mission Copilot** is an AI-powered mission-planning system built with the **Google Agent Development Kit (ADK)** that generates complete, flight-ready mission packages for autonomous UAV operations. Developed as part of the **Google × Kaggle Agents Intensive Capstone**, this system eliminates manual mission planning by transforming natural language descriptions into structured, executable flight plans.

Mission Copilot directly supports **Project Icarus**, my broader engineering initiative focused on building a fully autonomous drone platform capable of real-time mapping, computer vision tasks, and advanced mission execution.

### Key Features

- **Natural Language Mission Planning** — Describe missions in plain English
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

Mission Copilot uses a **multi-agent architecture** built on Google ADK. The system consists of specialized agents working together:

```
User Input (Natural Language)
    ↓
Mission Planner Agent
    → Generates mission specification
    → Looks up regulatory requirements
    → Calculates estimated flight parameters
    ↓
Database Persistence
    → Saves mission to SQLite
    → Returns mission_id
    ↓
Coverage Agent
    → Calculates optimal flight path (lawnmower pattern)
    → Determines leg spacing and swath width
    → Estimates flight time and battery segments
    ↓
Mission Package Complete
```

### Agent Breakdown

| Agent | Responsibility |
|-------|----------------|
| **Mission Planner Agent** | Interprets natural-language mission descriptions, searches for local regulations using Google Search, and creates structured mission specifications with area dimensions, altitude, camera parameters, and regulatory compliance notes |
| **Coverage Agent** | Calculates flight coverage patterns using camera FOV and altitude to determine swath width, generates lawnmower flight paths with specified overlap percentages, and estimates total flight distance and time |
| **Database Repository** | Persists mission specifications to SQLite database, maintains mission history, and enables retrieval for further processing |

---

## Repository Structure

```
Capstone-agent/
├── main.py                     # Simple demo agent
├── test_connection.py          # Network connectivity diagnostics
├── agents/                     # Agent definitions and configurations
│   ├── __init__.py
│   ├── mission_planner.py      # Mission planning with regulatory lookup
│   └── coverage_agent.py       # Flight path coverage calculation
├── tools/                      # Custom calculation tools
│   ├── __init__.py
│   └── coverage_calculator.py  # Lawnmower pattern generation
├── mission_db/                 # Database persistence layer
│   ├── __init__.py
│   └── mission_repo.py         # SQLite database operations
├── missions/                   # Generated mission outputs (future)
├── .env                        # Environment variables (not in repo)
├── .gitignore
└── README.md                   # This file
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Google Cloud API Key** (for Gemini models via ADK)
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

```bash
pip install google-adk python-dotenv
```

4. **Set up environment variables**

Create a `.env` file in the root directory:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### Configuration

The system uses the following default settings:

```python
MODEL_NAME = "gemini-2.5-flash-lite"
DATABASE_PATH = "missions.db"
```

---

## Usage

### Running the Mission Planner

```bash
python agents/mission_planner.py
```

This will:
1. Generate a mission specification from the default user request
2. Search for local drone regulations using Google Search
3. Save the complete mission spec to the database
4. Display the mission ID for reference

### Running the Coverage Agent

```bash
python agents/coverage_agent.py <mission_id>
```

This will:
1. Load the mission spec from the database
2. Calculate optimal flight paths with specified overlap
3. Output coverage summary including:
   - Number of flight legs
   - Total path distance
   - Estimated flight time
   - Battery segments required

### Example Mission Request

The default mission in `mission_planner.py`:

```python
user_request = """
I want to map a 500m x 300m field at 70m altitude for crop health 
with a 78° FOV camera. I wanna fly it in Delhi
"""
```

### Expected Output

**From Mission Planner:**
```
Mission #5 saved to missions.db
(Use this mission_id for coverage, ROS config, etc.)
```

**From Coverage Agent:**
```
Processing mission #5: Delhi crop health survey
Request: I want to map a 500m x 300m field at 70m altitude...

{
  "coverage_summary": {
    "sweep_direction": "along_length",
    "swath_width_m": 147.3,
    "leg_spacing_m": 51.6,
    "num_legs": 6,
    "leg_length_m": 500.0,
    "total_path_length_m": 3000.0,
    "total_flight_time_min": 6.25,
    "num_battery_segments": 1
  },
  "legs": [...]
}
```

---

## Technical Stack

| Category | Technology |
|----------|-----------|
| **AI Framework** | Google Agent Development Kit (ADK) |
| **LLM** | Gemini 2.5 Flash Lite |
| **Language** | Python 3.11+ |
| **Database** | SQLite 3 |
| **Async Framework** | asyncio |
| **Environment Management** | python-dotenv |
| **Tools** | google_search (via ADK) |

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

#### 3. `GOOGLE_API_KEY not found`

**Solution:** Ensure `.env` file exists in the project root with a valid API key from Google AI Studio.

#### 4. Database file not found

**Solution:** The database is created automatically on first run. Ensure you have write permissions in the project directory.

---

## Roadmap

- [x] Mission specification generation with regulatory lookup
- [x] Flight path coverage calculation
- [x] Database persistence layer
- [ ] ROS2 waypoint file generation
- [ ] Obstacle avoidance planning integration


---


## Contact

**Project Maintainer:** Aditya Solanki  
**Project Link:** [https://github.com/adityasolanki24/Icarus-Copilot](https://github.com/adityasolanki24/Icarus-Copilot)  
**Project Icarus:** [https://github.com/adityasolanki24/Project-Icarus](https://github.com/adityasolanki24/Project-Icarus)

---

*Built for autonomous UAV mission planning as part of the Google × Kaggle Agents Intensive Capstone Project*
