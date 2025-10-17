from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from backend_bedrock.routes.auth import get_current_user
from backend_bedrock.agents.grocery_list_agent import grocery_list_agent


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
async def chat_endpoint(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Main chat endpoint that routes to appropriate agents."""
    try:
        user_id = current_user.get("user_id")
        session_id = payload.session_id or f"session_{user_id}"
        
        # For now, route all grocery-related queries to the grocery list agent
        # In the future, this would go through an orchestrator
        response = grocery_list_agent.process_message(
            user_message=payload.message,
            user_id=user_id,
            session_id=session_id
        )
        
        if response.get("success"):
            return {
                "success": True,
                "message": response["message"],
                "session_id": session_id,
                "user_id": user_id,
                "tool_calls_made": response.get("tool_calls_made", 0)
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": response.get("message", "I'm having trouble processing your request.")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred while processing your request."
        }


@router.post("/chat/grocery-list")
async def create_grocery_list(
    payload: GroceryListRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Create a grocery list from ingredients."""
    try:
        user_id = current_user.get("user_id")
        session_id = f"grocery_{user_id}"
        
        response = grocery_list_agent.create_grocery_list(
            ingredients=payload.ingredients,
            user_id=user_id,
            session_id=session_id,
            max_budget=payload.max_budget
        )
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create grocery list"
        }


@router.post("/chat/substitutions")
async def get_substitutions(
    payload: SubstitutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get substitution suggestions for unavailable items."""
    try:
        user_id = current_user.get("user_id")
        session_id = f"substitutions_{user_id}"
        
        response = grocery_list_agent.suggest_substitutions(
            unavailable_items=payload.unavailable_items,
            user_id=user_id,
            session_id=session_id
        )
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get substitution suggestions"
        }


