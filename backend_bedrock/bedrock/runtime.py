"""
AWS Bedrock Runtime client for agent interactions.
Handles Converse API calls with tool use and memory management.
"""

import json
import boto3
import os
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError


class BedrockRuntimeClient:
    """Client for AWS Bedrock Runtime with tool use support."""
    
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize Bedrock Runtime client."""
        self.region_name = region_name
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # Updated to your specified model
        
    def converse_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Send a conversation with tool use to Bedrock.
        
        Args:
            messages: List of conversation messages
            tools: List of available tools
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Bedrock response with content and tool calls
        """
        try:
            # Prepare the request
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_body["system"] = system_prompt
            
            # Add tools if provided
            if tools:
                request_body["tools"] = tools
            
            # Make the API call
            response = self.client.converse(
                modelId=self.model_id,
                messages=request_body["messages"],
                system=request_body.get("system"),
                tools=request_body.get("tools"),
                maxTokens=request_body["max_tokens"],
                temperature=request_body["temperature"]
            )
            
            return {
                "success": True,
                "response": response,
                "content": self._extract_content(response),
                "tool_calls": self._extract_tool_calls(response)
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS Bedrock error: {str(e)}",
                "error_code": e.response.get("Error", {}).get("Code", "Unknown")
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Runtime error: {str(e)}"
            }
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """Extract text content from Bedrock response."""
        content = ""
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
        return content
    
    def _extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from Bedrock response."""
        tool_calls = []
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input", {})
                })
        return tool_calls
    
    def create_message(self, role: str, content: str) -> Dict[str, Any]:
        """Create a message for the conversation."""
        return {
            "role": role,
            "content": [{"type": "text", "text": content}]
        }
    
    def create_tool_result_message(self, tool_call_id: str, content: str) -> Dict[str, Any]:
        """Create a tool result message."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": [{"type": "text", "text": content}]
                }
            ]
        }


class AgentMemory:
    """Simple in-memory conversation history for agents."""
    
    def __init__(self, max_history: int = 50):
        """Initialize memory with max history length."""
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": [{"type": "text", "text": content}]
        }
        
        self.conversations[session_id].append(message)
        
        # Trim history if too long
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def add_tool_result(self, session_id: str, tool_call_id: str, result: str):
        """Add a tool result to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": [{"type": "text", "text": result}]
                }
            ]
        }
        
        self.conversations[session_id].append(message)
    
    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]


# Global instances
bedrock_client = BedrockRuntimeClient()
agent_memory = AgentMemory()
