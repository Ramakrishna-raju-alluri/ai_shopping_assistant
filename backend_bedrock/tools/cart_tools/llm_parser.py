"""
LLM-powered intelligent parser for grocery requests
Much more flexible and capable than regex-based NLP
"""

import json
from typing import Dict, List, Any, Optional
from strands.models import BedrockModel

try:
    from backend_bedrock.agents.grocery_list_agent import _build_bedrock_model
except ImportError:
    # Fallback for testing
    def _build_bedrock_model():
        return BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name="us-east-1",
        )

class IntelligentGroceryParser:
    """
    LLM-powered parser for understanding grocery requests
    """
    
    def __init__(self):
        self.model = _build_bedrock_model()
        
    def parse_grocery_request(self, user_input: str) -> Dict[str, Any]:
        """
        Parse grocery request using LLM intelligence
        
        Args:
            user_input: Raw user input
            
        Returns:
            Structured parsing results
        """
        
        parsing_prompt = f"""
You are an intelligent grocery request parser. Analyze the user's request and extract structured information.

User Request: "{user_input}"

Please analyze this request and return a JSON response with the following structure:
{{
    "action": "add|remove|view|check_availability|check_budget|substitution|clear",
    "items": [
        {{
            "name": "normalized item name",
            "quantity": number,
            "unit": "items|pounds|ounces|gallons|bottles|cans|boxes|bags|packs|cups|liters",
            "original_text": "original item text from user"
        }}
    ],
    "intent_confidence": 0.0-1.0,
    "special_requests": ["any special requirements like organic, low-fat, etc"],
    "urgency": "low|medium|high",
    "context_clues": ["any additional context from the request"]
}}

Guidelines:
- For action, choose the most appropriate action based on the request
- Normalize item names (e.g., "veggies" -> "vegetables", "milk carton" -> "milk")
- Convert word numbers to digits (e.g., "two" -> 2, "dozen" -> 12)
- Default quantity is 1 if not specified
- Default unit is "items" if not specified
- Extract special requests like "organic", "low-fat", "gluten-free"
- Consider urgency based on language like "need now", "urgent", "ASAP"
- Include any context clues that might help with product selection

Examples:
- "add 2 pounds of organic chicken" -> action: "add", items: [{{"name": "chicken", "quantity": 2, "unit": "pounds", "original_text": "organic chicken"}}], special_requests: ["organic"]
- "I need milk, eggs, and bread" -> action: "add", items: [{{"name": "milk", "quantity": 1, "unit": "items"}}, {{"name": "eggs", "quantity": 1, "unit": "items"}}, {{"name": "bread", "quantity": 1, "unit": "items"}}]
- "show my cart" -> action: "view", items: []
- "do you have apples?" -> action: "check_availability", items: [{{"name": "apples", "quantity": 1, "unit": "items"}}]

Return only the JSON response, no additional text.
"""

        try:
            # Use the LLM to parse the request
            try:
                # Try different BedrockModel methods
                if hasattr(self.model, 'invoke'):
                    response = self.model.invoke(parsing_prompt)
                elif hasattr(self.model, 'run'):
                    response = self.model.run(parsing_prompt)
                elif hasattr(self.model, '__call__'):
                    response = self.model(parsing_prompt)
                else:
                    # Fallback - use fallback parsing instead of stream
                    print("No suitable LLM method found, using fallback parsing")
                    return self._fallback_parse(user_input)
            except Exception as e:
                print(f"LLM method error: {e}")
                # Use fallback parsing
                return self._fallback_parse(user_input)
            
            # Extract JSON from response
            response_text = str(response)
            
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                
                # Validate and clean the result
                return self._validate_and_clean_result(parsed_result, user_input)
            else:
                # Fallback parsing if JSON extraction fails
                return self._fallback_parse(user_input)
                
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._fallback_parse(user_input)
    
    def _validate_and_clean_result(self, result: Dict[str, Any], original_input: str) -> Dict[str, Any]:
        """
        Validate and clean the LLM parsing result
        """
        # Ensure required fields exist
        cleaned_result = {
            "action": result.get("action", "add"),
            "items": result.get("items", []),
            "intent_confidence": min(max(result.get("intent_confidence", 0.8), 0.0), 1.0),
            "special_requests": result.get("special_requests", []),
            "urgency": result.get("urgency", "medium"),
            "context_clues": result.get("context_clues", []),
            "original_input": original_input,
            "parsing_method": "llm"
        }
        
        # Validate and clean items
        cleaned_items = []
        for item in cleaned_result["items"]:
            if isinstance(item, dict) and item.get("name"):
                cleaned_item = {
                    "name": str(item["name"]).strip().lower(),
                    "quantity": max(float(item.get("quantity", 1)), 0.1),
                    "unit": item.get("unit", "items"),
                    "original_text": item.get("original_text", item["name"])
                }
                cleaned_items.append(cleaned_item)
        
        cleaned_result["items"] = cleaned_items
        return cleaned_result
    
    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """
        Fallback parsing when LLM fails
        """
        user_input_lower = user_input.lower().strip()
        
        # Simple action detection
        if any(word in user_input_lower for word in ["add", "get", "buy", "need", "want"]):
            action = "add"
        elif any(word in user_input_lower for word in ["show", "view", "cart", "list"]):
            action = "view"
        elif any(word in user_input_lower for word in ["remove", "delete", "take out"]):
            action = "remove"
        elif any(word in user_input_lower for word in ["available", "have", "stock"]):
            action = "check_availability"
        elif any(word in user_input_lower for word in ["budget", "cost", "price", "total"]):
            action = "check_budget"
        else:
            action = "add"  # Default
        
        return {
            "action": action,
            "items": [{"name": user_input_lower, "quantity": 1, "unit": "items", "original_text": user_input}],
            "intent_confidence": 0.6,
            "special_requests": [],
            "urgency": "medium",
            "context_clues": [],
            "original_input": user_input,
            "parsing_method": "fallback"
        }

# Global parser instance
_parser_instance = None

def get_intelligent_parser() -> IntelligentGroceryParser:
    """Get or create the intelligent parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntelligentGroceryParser()
    return _parser_instance

def parse_grocery_request_with_llm(user_input: str) -> Dict[str, Any]:
    """
    Parse grocery request using LLM intelligence
    
    Args:
        user_input: Raw user input
        
    Returns:
        Structured parsing results
    """
    parser = get_intelligent_parser()
    return parser.parse_grocery_request(user_input)