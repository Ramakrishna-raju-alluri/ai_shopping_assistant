import os
from utils import create_agentcore_role
from dotenv import load_dotenv

load_dotenv()

# Create IAM roles for each agent
orchestrator_agent_name="orchestrator_agent"
orchestrator_iam_role = create_agentcore_role(agent_name=orchestrator_agent_name, region=os.getenv("AWS_DEFAULT_REGION"))
orchestrator_role_arn = orchestrator_iam_role['Role']['Arn']
orchestrator_role_name = orchestrator_iam_role['Role']['RoleName']
print(orchestrator_role_arn)
print(orchestrator_role_name)

from strands import Agent, tool
import argparse
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel


