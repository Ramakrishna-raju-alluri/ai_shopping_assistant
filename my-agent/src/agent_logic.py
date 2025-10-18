"""
Core agent logic for the Coles Shopping Assistant
"""
import re
from typing import Dict, Any, List
from strands import Agent
from .tools.db_tool import (
    find_product_stock, 
    get_nutrition_plan, 
    set_nutrition_target, 
    append_meal, 
    get_calories_remaining,
    get_user_profile
)
from .tools.model_tool import calculate_calories, calculate_cost, generate_meal_suggestions
from .tools.custom_tool import (
    get_current_date, 
    format_nutrition_summary, 
    validate_date_format, 
    parse_meal_input
)


class ColesShoppingAgent:
    """
    Main agent class that orchestrates different tools based on user queries
    """
    
    def __init__(self):
        self.agent = Agent(
            system_prompt=self._get_system_prompt(),
            tools=self._get_all_tools()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """
You are the Coles Shopping Assistant, an AI agent that helps users with grocery shopping, 
nutrition tracking, and meal planning. You have access to various tools to help users:

**Available Capabilities:**
1. **Product Information**: Check if products are in stock, get product details
2. **Nutrition Tracking**: Log meals, track calories, set daily targets, check remaining calories
3. **Meal Planning**: Generate meal suggestions based on preferences and budget
4. **User Profile**: Access user dietary preferences and constraints

**Routing Guidelines:**
- For product availability/stock questions → use product-related tools
- For nutrition tracking (calories, meals, targets) → use nutrition-related tools  
- For meal planning and suggestions → use meal planning tools
- For user preferences → use profile tools

**Important Rules:**
- Always ask for user_id when needed for personal data
- For date-specific queries, ask for date if not provided (use YYYY-MM-DD format)
- Be helpful and provide clear, actionable responses
- If a query is ambiguous, ask for clarification
- Use the most appropriate tool(s) for each query
- Provide concise, useful information without repetition

**Response Format:**
- Be conversational and helpful
- Provide specific information when available
- Ask follow-up questions when needed
- Summarize key information clearly
"""
    
    def _get_all_tools(self) -> List:
        """Get all available tools"""
        return [
            # Product tools
            find_product_stock,
            
            # Nutrition tools
            get_nutrition_plan,
            set_nutrition_target,
            append_meal,
            get_calories_remaining,
            
            # User profile tools
            get_user_profile,
            
            # Meal planning tools
            calculate_calories,
            calculate_cost,
            generate_meal_suggestions,
            
            # Utility tools
            get_current_date,
            format_nutrition_summary,
            validate_date_format,
            parse_meal_input
        ]
    
    def _extract_user_id(self, query: str) -> str:
        """Extract user_id from query if mentioned"""
        # Look for patterns like "user_id: xyz" or "I am user-123"
        patterns = [
            r"user[_\s]*id[:\s]+([a-zA-Z0-9_-]+)",
            r"I am ([a-zA-Z0-9_-]+)",
            r"my user[_\s]*id is ([a-zA-Z0-9_-]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "default-user"
    
    def _extract_date(self, query: str) -> str:
        """Extract date from query if mentioned"""
        # Look for YYYY-MM-DD format
        date_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
        match = re.search(date_pattern, query)
        if match:
            return match.group(1)
        
        # Look for "today" or "tomorrow"
        if "today" in query.lower():
            return get_current_date()
        
        return None
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        # Product/stock related keywords
        product_keywords = [
            "stock", "available", "in stock", "out of stock", "product", 
            "banana", "apple", "milk", "bread", "have", "buy", "price"
        ]
        
        # Nutrition/calorie related keywords
        nutrition_keywords = [
            "calorie", "calories", "meal", "breakfast", "lunch", "dinner",
            "target", "remaining", "log", "track", "nutrition", "diet"
        ]
        
        # Meal planning keywords
        meal_planning_keywords = [
            "suggest", "recommend", "plan", "recipe", "cook", "prepare"
        ]
        
        product_score = sum(1 for keyword in product_keywords if keyword in query_lower)
        nutrition_score = sum(1 for keyword in nutrition_keywords if keyword in query_lower)
        meal_planning_score = sum(1 for keyword in meal_planning_keywords if keyword in query_lower)
        
        if product_score > nutrition_score and product_score > meal_planning_score:
            return "product"
        elif nutrition_score > meal_planning_score:
            return "nutrition"
        elif meal_planning_score > 0:
            return "meal_planning"
        else:
            return "general"
    
    def process_query(self, query: str, user_id: str = None) -> str:
        """
        Process a user query and return the agent's response
        
        Args:
            query: The user's query
            user_id: Optional user ID (will be extracted from query if not provided)
        
        Returns:
            The agent's response as a string
        """
        # Extract user_id if not provided
        if not user_id:
            user_id = self._extract_user_id(query)
        
        # Extract date if mentioned
        date = self._extract_date(query)
        
        # Classify query type
        query_type = self._classify_query(query)
        
        # Enhance query with context
        enhanced_query = f"User ID: {user_id}. Query: {query}"
        if date:
            enhanced_query += f" Date: {date}"
        
        # Process through the agent
        try:
            response = self.agent(enhanced_query)
            return str(response)
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question."
