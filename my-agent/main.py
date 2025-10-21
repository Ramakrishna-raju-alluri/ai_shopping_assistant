"""
AgentCore entry point for the Coles Shopping Assistant Agent - Orchestrator
Using the new backend_bedrock agents with DynamoDB integration
"""
import json
import logging
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp

# Import the new orchestrator from backend_bedrock agents
from agents.orchestrator import orchestrator_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the AgentCore Runtime App
app = BedrockAgentCoreApp()  #### AGENTCORE RUNTIME - LINE 2 ####

# Use the orchestrator agent directly
agent = orchestrator_agent
print("hello")

@app.entrypoint  #### AGENTCORE RUNTIME - LINE 3 ####
async def invoke(payload, context=None):
    """
    AgentCore entry point for the agent
    
    Args:
        payload: The input payload containing user query and metadata
        context: Optional context (not used in this implementation)
    
    Returns:
        String response from the agent
    """
    try:
        logger.info(f"Received payload: {json.dumps(payload, default=str)}")
        
        # Extract user input from payload
        user_input = payload.get("prompt", "")
        user_id = payload.get("user_id", "default-user")
        
        if not user_input:
            return "No prompt provided. Please include a 'prompt' in your request."
        
        # Enhance query with context
        enhanced_query = f"User ID: {user_id}. Query: {user_input}"
        
        # Process the request through the agent
        response = agent(enhanced_query)
        
        logger.info(f"Agent response: {response}")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # app.run()
    # Test with proper user_id
    response = agent("User ID: test-user-123. Query: how many calories are there in bananas")
    print(response)