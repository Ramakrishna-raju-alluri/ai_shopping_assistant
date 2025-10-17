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
    from backend_bedrock.agents import meal_planner_agent, simple_query_agent, health_planner_agent
except ImportError:
    try:
        from agents import meal_planner_agent, simple_query_agent, health_planner_agent
    except ImportError:
        import meal_planner_agent
        import simple_query_agent
        import health_planner_agent

ORCHESTRATOR_PROMPT = """
You are an orchestrator agent that routes user requests to specialized agents based on the request type.

ROUTING GUIDELINES:
- For meal planning, recipe creation, grocery lists, and food-related requests → use `meal_planner_agent`
- For nutrition tracking, calorie counting, daily meal logging, and health goals → use `health_planner_agent`  
- For product availability, stock checks, store information, and simple catalog queries → use `simple_query_agent`
- For general questions not requiring specialized tools, handle directly with your knowledge

If user's query requires multiple 'agents', use any combination of the above to answer.
If two agents are required to answer the user's query, do NOT CALL THEM PARALLELY unless they are independent.

Always pass the user_id and the complete user query to the selected agent.
"""
orchestrator_agent = Agent(
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[
        meal_planner_agent.meal_planner_agent,
        health_planner_agent.health_planner_agent,
        simple_query_agent.simple_query_agent
        ]
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