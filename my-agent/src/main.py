"""
Main entry point for the Coles Shopping Assistant Agent - Orchestrator
"""
import json
import logging
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp
from .agents.product_agent import product_agent
from .agents.nutrition_agent import nutrition_agent
from .agents.meal_planning_agent import meal_planning_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AgentCore app
app = BedrockAgentCoreApp()

ORCHESTRATOR_PROMPT = """
You are the Coles Shopping Assistant orchestrator that coordinates between specialized agents to provide comprehensive grocery shopping, nutrition tracking, and meal planning assistance.

Your specialized agents are:
1. **product_agent**: Handles product stock checks, availability, and product information queries
2. **nutrition_agent**: Handles calorie tracking, meal logging, nutrition goals, and daily targets
3. **meal_planning_agent**: Handles meal suggestions, recipe generation, and cost calculations

Guidelines for using your agents:
- Use **product_agent** for questions about: product availability, stock status, product information
- Use **nutrition_agent** for questions about: calories, meal logging, nutrition targets, daily tracking
- Use **meal_planning_agent** for questions about: meal suggestions, recipes, meal planning, cost calculations
- You can use multiple agents together for comprehensive assistance
- Always provide a cohesive summary that combines insights from multiple agents when applicable
- Maintain a helpful, conversational tone

When a user asks a question:
1. Determine which agent(s) are most appropriate for the query
2. Call the relevant agent(s) with focused queries including user_id
3. Synthesize the responses into a coherent, comprehensive answer
4. Provide actionable next steps when possible

Important:
- Always extract and pass the user_id to agents when making calls
- If user_id is not provided, ask the user for it or use "default-user"
- Be helpful and provide clear, actionable responses
"""

# Initialize the orchestrator agent with specialized agents as tools
agent = Agent(
    model_id="amazon.nova-pro-v1:0" ,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[
        product_agent,
        nutrition_agent,
        meal_planning_agent
    ]
)


@app.entrypoint
def invoke(payload):
    """
    AgentCore entry point for the agent
    
    Args:
        payload: The input payload containing user query and metadata
    
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


def main():
    """Local testing entry point"""
    user_query = "Are bananas in stock? My user ID is 'test-user-123'."
    response = agent(user_query)
    print(response)


if __name__ == "__main__":
    app.run()
