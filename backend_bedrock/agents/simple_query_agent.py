from strands import Agent, tool
import argparse
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(
    model_id=model_id,
)
agent = Agent(
    model=model,
    system_prompt="You're a recipe generator, you can help with their meal plannign queries"
)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke agent with payload
    """
    user_input = payload.get("prompt")
    print(f"User input: {user_input}")
    response = agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=str)
    args = parser.parse_args()
    payload = {"prompt": args.prompt}
    response = strands_agent_bedrock(payload)
    print(response)
    #app.run()