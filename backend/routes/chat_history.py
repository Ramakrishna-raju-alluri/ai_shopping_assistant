from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import authentication
from routes.auth import get_current_user

# Import chat history service
from services.chat_history_service import chat_history_service

router = APIRouter()

# Pydantic models
class CreateChatSessionRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional custom title for the chat session")

class AddMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to add message to")
    message: Dict[str, Any] = Field(..., description="Message data to add")

class UpdateTitleRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to update")
    title: str = Field(..., description="New title for the session")

class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str
    is_active: bool

class ChatSessionDetailResponse(BaseModel):
    session_id: str
    title: str
    messages: List[Dict[str, Any]]
    message_count: int
    created_at: str
    updated_at: str
    is_active: bool

class ChatHistoryListResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    total_count: int

@router.post("/chat-history/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateChatSessionRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new chat session for the authenticated user
    Automatically maintains the 5 session limit per user
    """
    try:
        user_id = current_user["user_id"]
        
        # Create new session
        session_data = chat_history_service.create_chat_session(
            user_id=user_id,
            title=request.title
        )
        
        return ChatSessionResponse(
            session_id=session_data["session_id"],
            title=session_data["title"],
            message_count=session_data["message_count"],
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"],
            is_active=session_data["is_active"]
        )
        
    except Exception as e:
        print(f"❌ Error creating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

@router.get("/chat-history/sessions", response_model=ChatHistoryListResponse)
async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
    """
    Get all chat sessions for the authenticated user (up to 5 sessions)
    Returns sessions sorted by most recently updated
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user's chat sessions
        sessions = chat_history_service.get_user_chat_sessions(user_id)
        
        # Convert to response format
        session_responses = [
            ChatSessionResponse(
                session_id=session["session_id"],
                title=session["title"],
                message_count=session.get("message_count", 0),
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                is_active=session.get("is_active", True)
            )
            for session in sessions
        ]
        
        return ChatHistoryListResponse(
            sessions=session_responses,
            total_count=len(session_responses)
        )
        
    except Exception as e:
        print(f"❌ Error retrieving chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat sessions: {str(e)}")

@router.get("/chat-history/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(
    session_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific chat session with all its messages
    """
    try:
        user_id = current_user["user_id"]
        
        # Get session details
        session = chat_history_service.get_chat_session(user_id, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return ChatSessionDetailResponse(
            session_id=session["session_id"],
            title=session["title"],
            messages=session.get("messages", []),
            message_count=session.get("message_count", 0),
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            is_active=session.get("is_active", True)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat session: {str(e)}")

@router.post("/chat-history/sessions/{session_id}/messages")
async def add_message_to_session(
    session_id: str,
    request: AddMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a message to an existing chat session
    """
    try:
        user_id = current_user["user_id"]
        
        # Add message to session
        success = chat_history_service.add_message_to_session(
            user_id=user_id,
            session_id=session_id,
            message=request.message
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found or failed to add message")
        
        return {"message": "Message added successfully", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding message to session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.put("/chat-history/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateTitleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the title of a chat session
    """
    try:
        user_id = current_user["user_id"]
        
        # Update session title
        success = chat_history_service.update_session_title(
            user_id=user_id,
            session_id=session_id,
            new_title=request.title
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found or failed to update title")
        
        return {"message": "Session title updated successfully", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating session title: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session title: {str(e)}")

@router.delete("/chat-history/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a chat session
    """
    try:
        user_id = current_user["user_id"]
        
        # Delete session
        success = chat_history_service.delete_chat_session(user_id, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found or failed to delete")
        
        return {"message": "Chat session deleted successfully", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")

@router.get("/chat-history/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of a chat session (metadata only, no messages)
    """
    try:
        user_id = current_user["user_id"]
        
        # Get session summary
        summary = chat_history_service.get_session_summary(user_id, session_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session summary: {str(e)}")

# Health check endpoint for chat history service
@router.get("/chat-history/health")
async def chat_history_health_check():
    """
    Health check endpoint for chat history service
    """
    try:
        # Simple check to see if DynamoDB is accessible
        # This will be implemented based on your specific needs
        return {
            "status": "healthy",
            "service": "chat_history",
            "timestamp": datetime.now().isoformat(),
            "table": "chat-history-coles"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Chat history service unhealthy: {str(e)}") 