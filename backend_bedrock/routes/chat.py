from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from routes.auth import get_current_user

# Try to import orchestrator, fallback if it fails
try:
    from agents.orchestrator import orchestrator_agent
    ORCHESTRATOR_AVAILABLE = True
    print("✅ Orchestrator agent loaded successfully")
except Exception as e:
    print(f"⚠️ Orchestrator agent failed to load: {e}")
    print(f"⚠️ Chat route will work with fallback responses")
    ORCHESTRATOR_AVAILABLE = False
    orchestrator_agent = None

print(f"🔍 Chat route module loaded, orchestrator available: {ORCHESTRATOR_AVAILABLE}")

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
    
    if not ORCHESTRATOR_AVAILABLE:
        # Fallback response when orchestrator is not available
        fallback_response = (
            f"Hello! I received your message: '{payload.message}'. "
            "However, the AI orchestrator is currently unavailable. "
            "Please check the server configuration and try again later."
        )
        return {
            "message": payload.message,
            "reply": fallback_response,
            "assistant_message": fallback_response,
            "user_id": user_id,
            "session_id": payload.session_id,
            "status": "fallback_mode"
        }
    
    try:
        combined_prompt = f"User ID: {user_id}. Request: {payload.message}"
        result = orchestrator_agent(combined_prompt)
        
        if hasattr(result, 'message') and hasattr(result.message, 'content'):
            actual_text = result.message.content[0].text if result.message.content else str(result)
        else:
            actual_text = str(result)

        return {
            "message": payload.message,
            "reply": actual_text,
            "assistant_message": actual_text,
            "user_id": user_id,
            "session_id": payload.session_id,
        }
    except Exception as e:
        print(f"❌ Error in orchestrator_agent: {e}")
        error_response = (
            f"I received your message: '{payload.message}', but encountered an error "
            f"while processing it. Error: {str(e)}"
        )
        return {
            "message": payload.message,
            "reply": error_response,
            "assistant_message": error_response,
            "user_id": user_id,
            "session_id": payload.session_id,
            "status": "error",
            "error": str(e)
        }


