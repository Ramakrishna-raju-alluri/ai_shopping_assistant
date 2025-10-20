from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from backend_bedrock.routes.auth import get_current_user
from backend_bedrock.agents.orchestrator import orchestrator_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class GroceryListRequest(BaseModel):
    ingredients: List[str]
    max_budget: Optional[float] = None


class SubstitutionRequest(BaseModel):
    unavailable_items: List[str]


@router.post("/chat")
async def chat_endpoint(
    payload: ChatRequest, 
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("user_id", "default_user")
    print(f"🔍 CHAT ENDPOINT - user_id: {user_id}, message: {payload.message}")
    
    combined_prompt = f"User ID: {user_id}. Request: {payload.message}"
    result = orchestrator_agent(combined_prompt)
    
    if hasattr(result, 'message') and hasattr(result.message, 'content'):
        actual_text = result.message.content[0].text if result.message.content else str(result)
    else:
        actual_text = str(result)

    return {
        "message": payload.message,
        "reply": actual_text,  # Simple string instead of complex object
        "assistant_message": actual_text,  # What frontend expects
        "user_id": user_id,
        "session_id": payload.session_id,
    }


