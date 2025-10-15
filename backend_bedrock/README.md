# Backend (AWS Bedrock Edition)

A fresh backend focused on AWS services (Bedrock, Agents for Amazon Bedrock, DynamoDB). It mirrors the existing API categories and prepares for agentic orchestration.

## Structure

```
backend_bedrock/
  main.py                 # FastAPI app factory and wiring
  requirements.txt        # Python deps
  routes/                 # Categorized API routers
    __init__.py
    auth.py               # Signup/login/profile
    products.py           # Catalog queries
    profile_setup.py      # Onboarding & preferences
  agents/                 # Orchestrator and domain agents
  dynamo/                 # DynamoDB client and queries
  tools/                  # Reusable tools (catalog, pricing, etc.)
```

## Run (dev)

```bash
pip install -r requirements.txt
uvicorn backend_bedrock.main:app --reload --port 8100
```

## Notes
- Auth and profile endpoints use DynamoDB like the original backend for compatibility.
- Chat and agent endpoints will be added next, integrating Bedrock models and Agents for Amazon Bedrock.
- Configure credentials via environment variables or your AWS profile.
