import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

# Create IAM roles for each agent
# orchestrator_agent_name="orchestrator_agent"
# orchestrator_iam_role = create_agentcore_role(agent_name=orchestrator_agent_name, region=os.getenv("AWS_DEFAULT_REGION"))
# orchestrator_role_arn = orchestrator_iam_role['Role']['Arn']
# orchestrator_role_name = orchestrator_iam_role['Role']['RoleName']
# print(orchestrator_role_arn)
# print(orchestrator_role_name)

from strands import Agent, tool
import argparse
import json
# from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

from strands import Agent

# Import with flexible import system
try:
    from backend_bedrock.agents import meal_planner_agent
except ImportError:
    try:
        from agents import meal_planner_agent
    except ImportError:
        import meal_planner_agent

ORCHESTRATOR_PROMPT = """
You are an orchestrator agent. Your job is to route user requests to the correct specialized agent.
- For anything related to food, recipes, or meal planning, use the `meal_planner_agent`.
- For other requests, handle them directly.
"""
orchestrator_agent = Agent(
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[meal_planner_agent]
)

# def main():
#     orchestrator_agent = Agent(
#         system_prompt=ORCHESTRATOR_PROMPT,
#         tools=[meal_planner_agent]
#     )

#     user_query = "I need a healthy meal plan for next week. My user ID is 'user-123'."
#     response = orchestrator(user_query)
#     print(response)

# if __name__ == "__main__":
#     main()