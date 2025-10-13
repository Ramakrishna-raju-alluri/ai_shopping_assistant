# agents/smart_router.py
from typing import List, Dict, Any
from enum import Enum

class AgentType(Enum):
    INTENT = "intent"
    PREFERENCE = "preference" 
    MEAL_PLANNER = "meal_planner"
    PRODUCT_RECOMMENDER = "product_recommender"
    BASKET_BUILDER = "basket_builder"
    STOCK_CHECKER = "stock_checker"
    FEEDBACK = "feedback"
    GENERAL_QUERY = "general_query"

class QueryCategory(Enum):
    # Simple queries - no complex processing needed
    PRICE_CHECK = "price_check"
    AVAILABILITY_CHECK = "availability_check"
    STORE_INFO = "store_info"
    
    # Product-focused queries
    PRODUCT_RECOMMENDATION = "product_recommendation"
    DIETARY_FILTER = "dietary_filter"
    SUBSTITUTION_REQUEST = "substitution_request"
    
    # Promotion/discount queries
    DISCOUNT_CHECK = "discount_check"
    PROMOTION_INFO = "promotion_info"
    
    # Complex meal planning
    MEAL_PLANNING = "meal_planning"
    
    # General conversation
    GENERAL_QUERY = "general_query"

def classify_query_category(intent: Dict[str, Any], message: str) -> QueryCategory:
    """
    Classify query into specific categories using LLM intelligence with keyword fallback
    """
    try:
        # Import the LLM classifier
        from agents.llm_query_classifier import classify_query_with_llm
        
        # Use LLM classification
        llm_result = classify_query_with_llm(message)
        
        # Map LLM query types to QueryCategory enums
        llm_to_category_mapping = {
            "price_inquiry": QueryCategory.PRICE_CHECK,
            "availability_check": QueryCategory.AVAILABILITY_CHECK,
            "store_navigation": QueryCategory.STORE_INFO,
            "substitution_request": QueryCategory.SUBSTITUTION_REQUEST,
            "promotion_inquiry": QueryCategory.PROMOTION_INFO,
            "meal_planning": QueryCategory.MEAL_PLANNING,
            "recommendation_request": QueryCategory.PRODUCT_RECOMMENDATION,
            "dietary_filter": QueryCategory.DIETARY_FILTER,
            "product_search": QueryCategory.AVAILABILITY_CHECK,  # Map to availability check
            "general_inquiry": QueryCategory.GENERAL_QUERY
        }
        
        llm_query_type = llm_result['query_type']
        category = llm_to_category_mapping.get(llm_query_type, QueryCategory.GENERAL_QUERY)
        
        print(f"   ✅ LLM category classification: {category.value} (confidence: {llm_result.get('confidence', 0):.2f})")
        return category
        
    except Exception as e:
        print(f"   ❌ LLM category classification failed, using keyword fallback: {e}")
        return classify_query_category_keyword_fallback(intent, message)

def classify_query_category_keyword_fallback(intent: Dict[str, Any], message: str) -> QueryCategory:
    """
    Legacy keyword-based query category classification for when LLM fails
    """
    query_type = intent.get("query_type", "general_query")
    message_lower = message.lower()
    
    # Price check patterns
    price_keywords = ["price", "cost", "how much", "price of", "cost of", "$"]
    if any(keyword in message_lower for keyword in price_keywords):
        return QueryCategory.PRICE_CHECK
    
    # Availability check patterns
    availability_keywords = ["do you have", "do you carry", "available", "in stock", "out of stock"]
    if any(keyword in message_lower for keyword in availability_keywords):
        return QueryCategory.AVAILABILITY_CHECK
    
    # Store info patterns
    store_keywords = ["hours", "location", "delivery", "pickup", "contact", "address"]
    if any(keyword in message_lower for keyword in store_keywords):
        return QueryCategory.STORE_INFO
    
    # Substitution patterns
    substitution_keywords = ["substitute", "alternative", "replacement", "instead of", "similar to"]
    if any(keyword in message_lower for keyword in substitution_keywords):
        return QueryCategory.SUBSTITUTION_REQUEST
    
    # Discount/promotion patterns
    discount_keywords = ["discount", "sale", "promotion", "deal", "offer", "coupon", "promo"]
    if any(keyword in message_lower for keyword in discount_keywords):
        if "what" in message_lower or "show" in message_lower or "available" in message_lower:
            return QueryCategory.PROMOTION_INFO
        else:
            return QueryCategory.DISCOUNT_CHECK
    
    # Map original query types to categories
    if query_type == "meal_planning":
        return QueryCategory.MEAL_PLANNING
    elif query_type == "product_recommendation":
        return QueryCategory.PRODUCT_RECOMMENDATION
    elif query_type == "dietary_filter":
        return QueryCategory.DIETARY_FILTER
    else:
        return QueryCategory.GENERAL_QUERY

def get_required_agents(category: QueryCategory, intent: Dict[str, Any] = None) -> List[AgentType]:
    """
    Determine which agents are needed based on query category
    """
    agent_routing = {
        # Simple queries - minimal processing
        QueryCategory.PRICE_CHECK: [AgentType.GENERAL_QUERY],
        QueryCategory.AVAILABILITY_CHECK: [AgentType.GENERAL_QUERY],
        QueryCategory.STORE_INFO: [AgentType.GENERAL_QUERY],
        
        # Product queries - need preferences for personalization
        QueryCategory.PRODUCT_RECOMMENDATION: [
            AgentType.INTENT, 
            AgentType.PREFERENCE, 
            AgentType.PRODUCT_RECOMMENDER,
            AgentType.FEEDBACK
        ],
        QueryCategory.DIETARY_FILTER: [
            AgentType.INTENT,
            AgentType.PREFERENCE, 
            AgentType.PRODUCT_RECOMMENDER,
            AgentType.FEEDBACK
        ],
        QueryCategory.SUBSTITUTION_REQUEST: [
            AgentType.GENERAL_QUERY,
            AgentType.STOCK_CHECKER
        ],
        
        # Promotion queries - focus on stock/promotions
        QueryCategory.DISCOUNT_CHECK: [AgentType.STOCK_CHECKER],
        QueryCategory.PROMOTION_INFO: [AgentType.STOCK_CHECKER, AgentType.GENERAL_QUERY],
        
        # Complex meal planning - full pipeline
        QueryCategory.MEAL_PLANNING: [
            AgentType.INTENT,
            AgentType.PREFERENCE,
            AgentType.MEAL_PLANNER,
            AgentType.BASKET_BUILDER,
            AgentType.STOCK_CHECKER,
            AgentType.FEEDBACK
        ],
        
        # General conversation
        QueryCategory.GENERAL_QUERY: [AgentType.GENERAL_QUERY]
    }
    
    return agent_routing.get(category, [AgentType.GENERAL_QUERY])

def should_skip_confirmation(category: QueryCategory) -> bool:
    """
    Determine if this query type should skip confirmation steps for faster response
    """
    # Skip confirmation for simple, quick queries
    skip_confirmation_categories = [
        QueryCategory.PRICE_CHECK,
        QueryCategory.AVAILABILITY_CHECK, 
        QueryCategory.STORE_INFO,
        QueryCategory.DISCOUNT_CHECK,
        QueryCategory.PROMOTION_INFO
    ]
    
    return category in skip_confirmation_categories

def get_response_template(category: QueryCategory) -> str:
    """
    Get appropriate response template based on query category
    """
    templates = {
        QueryCategory.PRICE_CHECK: "Here's the pricing information you requested:",
        QueryCategory.AVAILABILITY_CHECK: "Here's the availability status:",
        QueryCategory.STORE_INFO: "Here's the store information:",
        QueryCategory.SUBSTITUTION_REQUEST: "Here are some substitute options:",
        QueryCategory.DISCOUNT_CHECK: "Here are the current discounts:",
        QueryCategory.PROMOTION_INFO: "Here are the available promotions:",
        QueryCategory.PRODUCT_RECOMMENDATION: "Here are my product recommendations:",
        QueryCategory.DIETARY_FILTER: "Here are products matching your dietary preferences:",
        QueryCategory.MEAL_PLANNING: "Let me create a meal plan for you:",
        QueryCategory.GENERAL_QUERY: "Here's the information you requested:"
    }
    
    return templates.get(category, "Here's what I found:")

def create_execution_plan(category: QueryCategory, intent: Dict[str, Any], message: str) -> Dict[str, Any]:
    """
    Create a complete execution plan for the query
    """
    required_agents = get_required_agents(category, intent)
    skip_confirmation = should_skip_confirmation(category)
    response_template = get_response_template(category)
    
    return {
        "category": category.value,
        "required_agents": [agent.value for agent in required_agents],
        "skip_confirmation": skip_confirmation,
        "response_template": response_template,
        "estimated_steps": len(required_agents),
        "complexity": "simple" if len(required_agents) <= 2 else "complex"
    } 