# Deploying Mission Copilot to Vertex AI Agent Engine

## Overview

This guide walks you through deploying your UAV Mission Copilot to Google Cloud's Vertex AI Agent Engine for production use.

## Prerequisites

1. **Google Cloud Project** with billing enabled
   - New users get $300 free credits
   - Sign up: https://cloud.google.com/free

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage-component.googleapis.com
   gcloud services enable logging.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable cloudtrace.googleapis.com
   ```

3. **Install Google Cloud SDK**
   - Download: https://cloud.google.com/sdk/docs/install
   - Initialize: `gcloud init`

4. **Install ADK CLI**
   ```bash
   pip install google-adk
   ```

## Deployment Steps

### Step 1: Set Your Project ID

```bash
export PROJECT_ID="your-google-cloud-project-id"
export REGION="us-central1"  # or your preferred region
gcloud config set project $PROJECT_ID
```

### Step 2: Prepare the Agent

The copilot is already configured with:
- `.agent_engine_config.json` - Resource limits and scaling
- `requirements-deploy.txt` - Production dependencies
- `.env.agent_engine` - Environment configuration

### Step 3: Deploy the Chat Interface

```bash
# Deploy the conversational copilot
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$REGION \
  . \
  --agent_engine_config_file=.agent_engine_config.json \
  --entry_point=chat:copilot_agent
```

This will:
- Package your agent code
- Upload to Cloud Storage
- Deploy to Agent Engine
- Return a resource name like: `projects/PROJECT_ID/locations/REGION/reasoningEngines/ENGINE_ID`

### Step 4: Test the Deployed Agent

```python
import vertexai
from vertexai import agent_engines

# Initialize
vertexai.init(project="your-project-id", location="us-central1")

# Get your deployed agent
agents_list = list(agent_engines.list())
remote_agent = agents_list[0]

# Test it
async for response in remote_agent.async_stream_query(
    message="Create a mission to map a 500m x 300m field at 70m altitude in Sydney",
    user_id="user_123"
):
    print(response)
```

### Step 5: Access via API

Once deployed, your agent gets a REST API endpoint:

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://REGION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/reasoningEngines/ENGINE_ID:query \
  -d '{
    "message": "List all my missions",
    "user_id": "user_123"
  }'
```

## Architecture on Agent Engine

```
User Request (API/SDK)
    ↓
Vertex AI Agent Engine Runtime
    ↓
Your Copilot Agent (Containerized)
    ├── Session Management (Agent Engine Sessions)
    ├── Memory Bank (Long-term storage)
    └── Mission Database (Cloud SQL or Firestore)
    ↓
Mission Files → Cloud Storage
```

## Cost Management

**Free Tier:**
- Agent Engine offers a monthly free tier
- Gemini API calls have separate pricing
- See: https://cloud.google.com/vertex-ai/generative-ai/pricing

**To minimize costs:**
- Set `min_instances: 0` (scales to zero when idle)
- Delete test deployments when finished
- Monitor usage in Cloud Console

**Delete your agent:**
```python
agent_engines.delete(resource_name=remote_agent.resource_name, force=True)
```

## Production Enhancements

### 1. Persistent Database

Replace SQLite with Cloud SQL or Firestore:

```python
# Cloud SQL connection
from google.cloud.sql.connector import Connector

connector = Connector()
conn = connector.connect(
    "project:region:instance",
    "pg8000",
    user="postgres",
    password="***",
    db="missions"
)
```

### 2. File Storage

Store mission files in Cloud Storage:

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket("mission-copilot-files")
blob = bucket.blob(f"missions/{mission_id}/mission_brief.md")
blob.upload_from_string(brief_content)
```

### 3. Add Memory Bank

Enable long-term memory across sessions:

```python
from google.adk.tools import preload_memory

copilot_agent = Agent(
    name="MissionCopilot",
    model=Gemini(model="gemini-2.5-flash-lite"),
    tools=[
        create_new_mission,
        get_all_missions,
        preload_memory  # Automatically recalls past conversations
    ]
)
```

### 4. Monitoring

View logs and traces:
- Cloud Logging: https://console.cloud.google.com/logs
- Cloud Trace: https://console.cloud.google.com/traces
- Agent Engine Console: https://console.cloud.google.com/vertex-ai/agent-engine

## Regions

Agent Engine is available in:
- `us-central1`
- `us-east4`
- `us-west1`
- `europe-west1`
- `europe-west4`
- `asia-northeast1`

Full list: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations

## Security

Agent Engine supports:
- **VPC Service Controls** - Data isolation
- **Customer-Managed Encryption Keys (CMEK)** - Your encryption keys
- **Private Service Connect** - Private networking
- **IAM** - Fine-grained access control

## Alternative: Deploy to Cloud Run

For simpler deployment without Agent Engine:

```bash
# Create Dockerfile, then:
gcloud run deploy mission-copilot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

See: https://cloud.google.com/agent-builder/agent-development-kit/docs/deploy-cloud-run

## Troubleshooting

**Issue:** "Permission denied"
**Fix:** Enable required APIs and check IAM roles

**Issue:** "Module not found"
**Fix:** Ensure all dependencies in `requirements-deploy.txt`

**Issue:** "Database locked"
**Fix:** Use Cloud SQL instead of SQLite for production

## Support

- ADK Documentation: https://cloud.google.com/agent-builder/agent-development-kit
- Agent Engine Docs: https://cloud.google.com/agent-builder/agent-engine/overview
- Google Cloud Support: https://cloud.google.com/support

---

**Next Steps:**
1. Set up Google Cloud project
2. Run deployment command
3. Test with API
4. Monitor in Cloud Console
5. Scale as needed!


