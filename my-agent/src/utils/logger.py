"""
Logging utilities for the agent
"""
import logging
import json
from typing import Any, Dict
from datetime import datetime


class AgentLogger:
    """Custom logger for agent operations"""
    
    def __init__(self, name: str = "coles_agent"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def log_query(self, user_id: str, query: str, query_type: str):
        """Log incoming user query"""
        self.logger.info(f"Query received - User: {user_id}, Type: {query_type}, Query: {query}")
    
    def log_tool_usage(self, tool_name: str, parameters: Dict[str, Any], result: Any):
        """Log tool usage"""
        self.logger.info(f"Tool used - {tool_name} with params: {json.dumps(parameters, default=str)}")
        self.logger.debug(f"Tool result: {json.dumps(result, default=str)}")
    
    def log_response(self, user_id: str, response: str, response_time: float):
        """Log agent response"""
        self.logger.info(f"Response sent - User: {user_id}, Time: {response_time:.2f}s, Length: {len(response)} chars")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors"""
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)


# Global logger instance
agent_logger = AgentLogger()
