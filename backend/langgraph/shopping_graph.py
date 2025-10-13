# langgraph/shopping_graph.py
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from agents.intent_agent import extract_intent
from agents.preference_agent import get_or_create_user_profile
from agents.meal_planner_agent import plan_meals, get_product_recommendations
from agents.basket_builder_agent import build_basket
from agents.stock_checker_agent import check_stock_and_promos
from agents.feedback_agent import learn_from_feedback
from agents.general_query_agent import handle_general_query

# Define state schema using TypedDict
class ShoppingState(TypedDict):
    user_id: str
    message: str
    intent: Dict[str, Any]
    user_profile: Optional[Dict[str, Any]]
    query_type: str
    recipes: Optional[List[Dict[str, Any]]]
    cart: Optional[List[Dict[str, Any]]]
    final_cart: Optional[List[Dict[str, Any]]]
    product_recommendations: Optional[Dict[str, Any]]
    feedback: Dict[str, Any]

# Define functions
async def intent_node(state):
    """Extract intent and determine query type"""
    intent = extract_intent(state["message"])
    query_type = intent.get("query_type", "general_query")
    
    print(f"   Query classified as: {query_type}")
    print(f"   Intent details: {intent}")
    
    return {
        "intent": intent,
        "query_type": query_type
    }

async def preference_node(state):
    """Load user profile (only for meal planning and product recommendations)"""
    query_type = state["query_type"]
    
    # Skip profile loading for general queries
    if query_type == "general_query":
        return {"user_profile": None}
    
    user_id = state["user_id"]
    intent = state["intent"]
    user_profile = get_or_create_user_profile(user_id, intent)
    
    return {"user_profile": user_profile}

async def meal_node(state):
    """Plan meals, get product recommendations, or handle general queries based on query type"""
    query_type = state["query_type"]
    
    if query_type == "meal_planning":
        # Handle meal planning
        user_profile = state["user_profile"]
        if not user_profile:
            return {"recipes": []}
        
        recipes = plan_meals(user_profile)
        return {"recipes": recipes}
    
    elif query_type in ["product_recommendation", "dietary_filter"]:
        # Handle product recommendations
        intent = state["intent"]
        user_profile = state["user_profile"]
        
        recommendations = get_product_recommendations(intent, user_profile)
        return {"product_recommendations": recommendations}
    
    elif query_type == "general_query":
        # Handle general queries
        user_message = state["message"]
        user_id = state["user_id"]
        user_profile = state["user_profile"]
        
        general_response = handle_general_query(user_message, user_id, user_profile)
        return {"general_response": general_response}
    
    else:
        # For unknown query types, return empty results
        return {"recipes": None, "product_recommendations": None, "general_response": None}

async def basket_node(state):
    """Build shopping basket (only for meal_planning queries)"""
    query_type = state["query_type"]
    
    if query_type != "meal_planning":
        return {"cart": None}
    
    recipes = state["recipes"]
    user_profile = state["user_profile"]
    
    if not recipes or not user_profile:
        return {"cart": []}
    
    budget_limit = user_profile.get("budget_limit")
    cart = build_basket(recipes, budget_limit)
    return {"cart": cart}

async def stock_node(state):
    """Check stock and apply promotions (only for meal_planning queries)"""
    query_type = state["query_type"]
    
    if query_type != "meal_planning":
        return {"final_cart": None}
    
    cart = state["cart"]
    if not cart:
        return {"final_cart": []}
    
    final_cart = check_stock_and_promos(cart)
    return {"final_cart": final_cart}

async def feedback_node(state):
    """Collect and learn from feedback based on query type"""
    query_type = state["query_type"]
    user_id = state["user_id"]
    
    # Prepare feedback data based on query type
    feedback_data = {}
    
    if query_type == "meal_planning":
        feedback_data = {
            "current_cart": state.get("final_cart", []),
            "query_type": "meal_planning",
            **state.get("feedback", {})
        }
    elif query_type in ["product_recommendation", "dietary_filter"]:
        recommendations = state.get("product_recommendations", {})
        feedback_data = {
            "recommended_products": recommendations.get("products", []),
            "query_type": query_type,
            **state.get("feedback", {})
        }
    elif query_type == "general_query":
        general_response = state.get("general_response", {})
        feedback_data = {
            "general_response": general_response,
            "query_type": "general_query",
            **state.get("feedback", {})
        }
    else:
        feedback_data = {
            "query_type": "unknown",
            **state.get("feedback", {})
        }
    
    # Learn from feedback
    learn_from_feedback(user_id, feedback_data)
    return {}

# Build LangGraph
builder = StateGraph(ShoppingState)
builder.add_node("intent", intent_node)
builder.add_node("preference", preference_node)
builder.add_node("meal", meal_node)
builder.add_node("basket", basket_node)
builder.add_node("stock", stock_node)
builder.add_node("feedback", feedback_node)

# Define edges
builder.set_entry_point("intent")
builder.add_edge("intent", "preference")
builder.add_edge("preference", "meal")

# Conditional edges based on query type
def route_after_meal(state):
    """Route to next step based on query type"""
    query_type = state["query_type"]
    if query_type == "meal_planning":
        return "basket"
    else:
        return "feedback"

builder.add_conditional_edges("meal", route_after_meal, {
    "basket": "basket",
    "feedback": "feedback"
})

builder.add_edge("basket", "stock")
builder.add_edge("stock", "feedback")
builder.add_edge("feedback", END)

# Compile flow
shopping_graph = builder.compile()