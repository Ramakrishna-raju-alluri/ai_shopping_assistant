"""
Output detection utility module for determining when to use structured output.

This module provides functions to detect when user queries require structured output
based on keyword analysis and determine which Pydantic model to use based on agent type.
"""

def should_use_structured_output(query: str) -> bool:
    """
    Detect if query requires structured output based on keywords.
    
    Args:
        query (str): User query string to analyze
        
    Returns:
        bool: True if structured output should be used, False for text response
        
    Requirements: 5.1, 5.2
    """
    if not query or not isinstance(query, str):
        return False
        
    query_lower = query.lower()
    
    # More specific patterns that indicate structured output is needed
    # Use word boundaries and specific phrases to avoid false positives
    structured_patterns = [
        'summary', 'report', 'breakdown', 'analysis', 
        'overview', 'status', 'progress'
    ]
    
    # Special handling for "plan" - only trigger for meal/nutrition planning summaries
    plan_patterns = [
        'meal plan', 'nutrition plan', 'diet plan breakdown',
        'plan summary', 'plan report', 'plan overview'
    ]
    
    # Special handling for "total" - only trigger when asking for totals/summaries
    total_patterns = [
        'total cost', 'total calories', 'total summary',
        'show total', 'give me total', 'cart total'
    ]
    
    # Special handling for "details" - only trigger for summary details
    detail_patterns = [
        'detailed summary', 'detailed report', 'detailed breakdown',
        'detailed analysis', 'summary details'
    ]
    
    # Check basic structured patterns
    for pattern in structured_patterns:
        if pattern in query_lower:
            return True
    
    # Check plan patterns
    for pattern in plan_patterns:
        if pattern in query_lower:
            return True
    
    # Check total patterns
    for pattern in total_patterns:
        if pattern in query_lower:
            return True
    
    # Check detail patterns
    for pattern in detail_patterns:
        if pattern in query_lower:
            return True
    
    return False


def get_output_type(query: str, agent_type: str) -> str:
    """
    Determine which structured output model to use based on agent type and query.
    
    Args:
        query (str): User query string to analyze
        agent_type (str): Type of agent ('health', 'grocery', 'meal', or other)
        
    Returns:
        str: Output type ('health_summary', 'grocery_summary', 'meal_plan', or 'text')
        
    Requirements: 5.2, 5.3
    """
    if not should_use_structured_output(query):
        return 'text'
    
    # Map agent types to their corresponding structured output models
    agent_type_mapping = {
        'health': 'health_summary',
        'grocery': 'grocery_summary',
        'meal': 'meal_plan'
    }
    
    return agent_type_mapping.get(agent_type, 'text')