"""
Main entry point for the Coles Shopping Assistant Agent
"""
import json
import logging
from typing import Dict, Any
from strands import Agent
from .agent_logic import ColesShoppingAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize our custom agent
coles_agent = ColesShoppingAgent()


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Lambda-style handler for the agent
    
    Args:
        event: The input event containing user query and metadata
        context: Lambda context (optional)
    
    Returns:
        Dict containing the agent's response
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract user input from event
        user_input = event.get("prompt", "")
        user_id = event.get("user_id", "default-user")
        
        if not user_input:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "No prompt provided",
                    "message": "Please provide a prompt in the event"
                })
            }
        
        # Process the request through our agent
        response = coles_agent.process_query(user_input, user_id)
        
        logger.info(f"Agent response: {response}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": response,
                "user_id": user_id,
                "timestamp": event.get("timestamp", "")
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }


def main():
    """Local testing entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coles Shopping Assistant Agent")
    parser.add_argument("--prompt", required=True, help="User query")
    parser.add_argument("--user-id", default="test-user", help="User ID")
    
    args = parser.parse_args()
    
    # Create test event
    test_event = {
        "prompt": args.prompt,
        "user_id": args.user_id,
        "timestamp": "2025-01-18T00:00:00Z"
    }
    
    # Process and print result
    result = handler(test_event)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
