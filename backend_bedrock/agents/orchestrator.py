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
    from backend_bedrock.agents import health_planner_agent, simple_query_agent
except ImportError:
    try:
        from agents import health_planner_agent, simple_query_agent
    except ImportError:
        import health_planner_agent
        import simple_query_agent

ORCHESTRATOR_PROMPT = """
You are an orchestrator agent. Choose exactly ONE tool unless the user explicitly requests multiple distinct tasks.

Tool selection:
- If the query is about product availability/stock in the store, use `simple_query_agent_tool`.
- If the query is about calories remaining, daily targets, logging meals, or fetching a day plan, use `health_planner_agent`.
- If the query is ambiguous between product vs health, ask a brief clarification FIRST rather than calling any tool.
- Otherwise, answer directly without tools.

Hard constraints:
- Never use the product tool for health/nutrition questions.
- Never use the health tool for store product/stock questions.
- Use at most one tool call per user message unless the user clearly asked for multiple different actions.
- Answer once concisely and do not repeat tool output verbatim.
"""


@tool
def simple_query_agent_tool(query: str) -> str:
    """ONLY for product availability/stock questions via simple_query_agent. Never use for health/nutrition queries."""
    response = simple_query_agent.agent(query)
    try:
        return response.message['content'][0]['text']
    except Exception:
        return str(response)

def main():
    orchestrator = Agent(
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[health_planner_agent.health_planner_agent, simple_query_agent_tool]
    )

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="Are bananas in stock? My user ID is 'user-123'.")
    args = parser.parse_args()
    response = orchestrator(args.query)
    print(response)

if __name__ == "__main__":
    main()