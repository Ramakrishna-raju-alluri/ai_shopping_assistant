from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend_bedrock.routes.auth import get_current_user


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    # Placeholder: orchestrator handoff to Bedrock-enabled agents
    return {
        "message": "Acknowledged",
        "reply": "Orchestrator placeholder response.",
        "user_id": current_user.get("user_id"),
        "session_id": payload.session_id,
    }


