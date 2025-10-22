from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from routes.auth import get_current_user
import os
import re
from agents.orchestrator import orchestrator_agent
from utils.response_filter import clean_response

print("🔍 Chat route module loaded with Bedrock AgentCore integration")

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

    # Clean the response to remove thinking tags and other artifacts
    cleaned_text = clean_response(actual_text)

    return {
        "message": payload.message,
        "reply": cleaned_text,  # Cleaned response
        "assistant_message": cleaned_text,  # What frontend expects
        "user_id": user_id,
        "session_id": payload.session_id,
    }

    # try:
    #     import boto3
    #     import json
        
    #     # Initialize Bedrock AgentCore client with environment variables
    #     import os
    #     client = boto3.client(
    #         'bedrock-agentcore', 
    #         region_name='us-east-1',
    #         aws_access_key_id=os.getenv('BEDROCK_ACCESS_KEY_ID'),
    #         aws_secret_access_key=os.getenv('BEDROCK_SECRET_ACCESS_KEY')
    #     )
        
    #     # Prepare payload for AgentCore
    #     agentcore_payload = json.dumps(
    #         {"prompt": payload.message}
    #     )
        
    #     # Generate a session ID if not provided (must be 33+ chars)
    #     session_id = payload.session_id or f"session-{user_id}-{int(datetime.now().timestamp())}"
    #     if len(session_id) < 33:
    #         session_id = f"session-{user_id}-{int(datetime.now().timestamp())}-extended"
        
    #     print(f"🤖 Calling Bedrock AgentCore with session: {session_id}")
        
    #     # Call Bedrock AgentCore
    #     response = client.invoke_agent_runtime(
    #         agentRuntimeArn=os.getenv("AGENT_RUNTIME_ARN"),
    #         runtimeSessionId=session_id,
    #         payload=agentcore_payload,
    #         qualifier="DEFAULT"
    #     )
        
    #     response_body = response['response'].read()
    #     print(f"🔍 Raw response body: {response_body}")

    #     response_data = json.loads(response_body)
    #     print(f"✅ Parsed AgentCore Response: {response_data}")
        
    #     # Extract the actual response text
    #     if isinstance(response_data, dict):
    #         raw_response = response_data.get('output', {}).get('text', str(response_data))
    #         agent_response = re.sub(r'<thinking>.*?</thinking>\s*', '', raw_response, flags=re.DOTALL).strip()
    #     else:
    #         raw_response = str(response_data)
    #         agent_response = re.sub(r'<thinking>.*?</thinking>\s*', '', raw_response, flags=re.DOTALL).strip()
            
    #     print("Agent response: ",agent_response)
    #     return {
    #         "message": payload.message,
    #         "reply": agent_response,
    #         "assistant_message": agent_response,
    #         "user_id": user_id,
    #         "session_id": session_id,
    #         "status": "success"
    #     }
        
    # except Exception as e:
    #     print(f"❌ Error in Bedrock AgentCore: {e}")
    #     error_response = (
    #         f"I received your message: '{payload.message}', but encountered an error "
    #         f"while processing it with Bedrock AgentCore. Error: {str(e)}"
    #     )
    #     return {
    #         "message": payload.message,
    #         "reply": error_response,
    #         "assistant_message": error_response,
    #         "user_id": user_id,
    #         "session_id": payload.session_id or f"error-session-{user_id}",
    #         "status": "error",
    #         "error": str(e)
    #     }


