"""
AgentCore entry point for the Coles Shopping Assistant Agent - Orchestrator
Using the new backend_bedrock agents with DynamoDB integration
"""
import json
import logging
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(__file__))


# # Debug: Print current working directory and file structure
# print("=== DEBUGGING INFO ===")
# print(f"Current working directory: {os.getcwd()}")
# print(f"__file__ location: {__file__}")
# print(f"Directory of __file__: {os.path.dirname(__file__)}")
# print(f"Python path: {sys.path}")

# # List current directory contents
# print("\nContents of current directory:")
# try:
#     for item in os.listdir('.'):
#         item_path = os.path.join('.', item)
#         if os.path.isdir(item_path):
#             print(f"  [DIR]  {item}")
#         else:
#             print(f"  [FILE] {item}")
# except Exception as e:
#     print(f"Error listing current directory: {e}")

# # List directory where main.py is located
# main_dir = os.path.dirname(__file__)
# print(f"\nContents of {main_dir}:")
# try:
#     for item in os.listdir(main_dir):
#         item_path = os.path.join(main_dir, item)
#         if os.path.isdir(item_path):
#             print(f"  [DIR]  {item}")
#         else:
#             print(f"  [FILE] {item}")
# except Exception as e:
#     print(f"Error listing main.py directory: {e}")

# # Check if agents directory exists
# agents_path = os.path.join(os.path.dirname(__file__), 'agents')
# print(f"\nChecking for agents directory at: {agents_path}")
# print(f"Agents directory exists: {os.path.exists(agents_path)}")
# if os.path.exists(agents_path):
#     print("Contents of agents directory:")
#     try:
#         for item in os.listdir(agents_path):
#             print(f"  {item}")
#     except Exception as e:
#         print(f"Error listing agents directory: {e}")

# print("=== END DEBUGGING INFO ===\n")


from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp

# Import the orchestrator from the same src directory
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
    # try:
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
    
    return {"result": response.message}
        
    # except Exception as e:
    #     logger.error(f"Error processing request: {str(e)}", exc_info=True)
    #     return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run()
    # print("hello from main")
    # Test with proper user_id
    # response = agent("User ID: user_101. Query: suggest three meals")
    # print(response)