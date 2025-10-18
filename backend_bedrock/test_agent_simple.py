#!/usr/bin/env python3
"""
Test the agent with a simple tool to isolate the issue
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strands import Agent, tool
from strands.models import BedrockModel

# Create a simple test tool
@tool
def test_simple_tool(message: str) -> str:
    """A simple test tool that just returns a message"""
    return f"Tool received: {message}"

def test_simple_agent():
    """Test agent with just one simple tool"""
    print("🤖 Testing Simple Agent...")
    print("=" * 50)
    
    try:
        # Create simple agent
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name="us-east-1",
            temperature=0.1,
        )
        
        simple_agent = Agent(
            model=bedrock_model,
            system_prompt="You are a test assistant. Use the test_simple_tool when the user asks you to test something.",
            tools=[test_simple_tool],
        )
        
        # Test the agent
        response = simple_agent("Please test the tool with message 'hello'")
        print(f"Agent response: {response}")
        
        if "Tool received: hello" in str(response):
            print("✅ Simple agent works!")
        else:
            print("❌ Simple agent failed")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_agent()