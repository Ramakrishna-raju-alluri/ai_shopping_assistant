# langgraph/flexible_shopping_graph.py
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from agents.intent_agent import extract_intent
from agents.preference_agent import get_or_create_user_profile
from agents.meal_planner_agent import plan_meals, get_product_recommendations
from agents.basket_builder_agent import build_basket
from agents.stock_checker_agent import check_stock_and_promos
from agents.feedback_agent import learn_from_feedback
from agents.general_query_agent import handle_general_query
from agents.smart_router import (
    classify_query_category, 
    get_required_agents, 
    create_execution_plan,
    AgentType,
    QueryCategory
)

# Enhanced state schema with routing information
class FlexibleShoppingState(TypedDict):
    user_id: str
    message: str
    intent: Optional[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]]
    query_type: str
    query_category: str
    execution_plan: Dict[str, Any]
    required_agents: List[str]
    completed_agents: List[str]
    recipes: Optional[List[Dict[str, Any]]]
    cart: Optional[List[Dict[str, Any]]]
    final_cart: Optional[List[Dict[str, Any]]]
    product_recommendations: Optional[Dict[str, Any]]
    general_response: Optional[Dict[str, Any]]
    stock_info: Optional[Dict[str, Any]]
    feedback: Dict[str, Any]
    final_response: Optional[str]

# Node functions with conditional execution
async def smart_intent_node(state):
    """Extract intent only if required by execution plan"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.INTENT.value not in required_agents:
        print("   Skipping intent extraction - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["intent"]}
    
    print("   Executing intent extraction")
    intent = extract_intent(state["message"])
    query_type = intent.get("query_type", "general_query")
    
    print(f"   Query classified as: {query_type}")
    print(f"   Intent details: {intent}")
    
    return {
        "intent": intent,
        "query_type": query_type,
        "completed_agents": state.get("completed_agents", []) + ["intent"]
    }

async def smart_preference_node(state):
    """Load user profile only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.PREFERENCE.value not in required_agents:
        print("   Skipping preference loading - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["preference"]}
    
    print("   Loading user preferences")
    user_id = state["user_id"]
    intent = state.get("intent", {})
    user_profile = get_or_create_user_profile(user_id, intent)
    
    return {
        "user_profile": user_profile,
        "completed_agents": state.get("completed_agents", []) + ["preference"]
    }

async def smart_meal_planner_node(state):
    """Plan meals only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.MEAL_PLANNER.value not in required_agents:
        print("   Skipping meal planning - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["meal_planner"]}
    
    print("   Planning meals")
    user_profile = state["user_profile"]
    if not user_profile:
        return {"recipes": [], "completed_agents": state.get("completed_agents", []) + ["meal_planner"]}
    
    recipes = plan_meals(user_profile)
    return {
        "recipes": recipes,
        "completed_agents": state.get("completed_agents", []) + ["meal_planner"]
    }

async def smart_product_recommender_node(state):
    """Get product recommendations only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.PRODUCT_RECOMMENDER.value not in required_agents:
        print("   Skipping product recommendations - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["product_recommender"]}
    
    print("   Getting product recommendations")
    intent = state.get("intent", {})
    user_profile = state.get("user_profile")
    
    recommendations = get_product_recommendations(intent, user_profile)
    return {
        "product_recommendations": recommendations,
        "completed_agents": state.get("completed_agents", []) + ["product_recommender"]
    }

async def smart_basket_builder_node(state):
    """Build basket only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.BASKET_BUILDER.value not in required_agents:
        print("   Skipping basket building - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["basket_builder"]}
    
    print("   Building shopping basket")
    recipes = state.get("recipes", [])
    user_profile = state.get("user_profile", {})
    
    if not recipes:
        return {"cart": [], "completed_agents": state.get("completed_agents", []) + ["basket_builder"]}
    
    budget_limit = user_profile.get("budget_limit")
    cart = build_basket(recipes, budget_limit)
    return {
        "cart": cart,
        "completed_agents": state.get("completed_agents", []) + ["basket_builder"]
    }

async def smart_stock_checker_node(state):
    """Check stock and promotions only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.STOCK_CHECKER.value not in required_agents:
        print("   Skipping stock checking - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["stock_checker"]}
    
    print("   Checking stock and applying promotions")
    query_category = state.get("query_category")
    
    # For promotion info queries, get all promotions
    if query_category == QueryCategory.PROMOTION_INFO.value:
        # Get all available promotions
        stock_info = {"promotions": check_stock_and_promos([])}
        return {
            "stock_info": stock_info,
            "completed_agents": state.get("completed_agents", []) + ["stock_checker"]
        }
    
    # For cart-based queries, process cart
    cart = state.get("cart", [])
    if cart:
        final_cart = check_stock_and_promos(cart)
        return {
            "final_cart": final_cart,
            "completed_agents": state.get("completed_agents", []) + ["stock_checker"]
        }
    
    return {"completed_agents": state.get("completed_agents", []) + ["stock_checker"]}

async def smart_general_query_node(state):
    """Handle general queries only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.GENERAL_QUERY.value not in required_agents:
        print("   Skipping general query processing - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["general_query"]}
    
    print("   Processing general query")
    user_message = state["message"]
    user_id = state["user_id"]
    user_profile = state.get("user_profile")
    
    general_response = handle_general_query(user_message, user_id, user_profile)
    return {
        "general_response": general_response,
        "completed_agents": state.get("completed_agents", []) + ["general_query"]
    }

async def smart_feedback_node(state):
    """Collect feedback only if required"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    
    if AgentType.FEEDBACK.value not in required_agents:
        print("   Skipping feedback collection - not required for this query")
        return {"completed_agents": state.get("completed_agents", []) + ["feedback"]}
    
    print("   Collecting feedback")
    query_category = state.get("query_category", "general_query")
    user_id = state["user_id"]
    
    # Prepare feedback data based on query category
    feedback_data = {"query_category": query_category}
    
    if state.get("final_cart"):
        feedback_data["current_cart"] = state["final_cart"]
    if state.get("product_recommendations"):
        feedback_data["recommended_products"] = state["product_recommendations"].get("products", [])
    if state.get("general_response"):
        feedback_data["general_response"] = state["general_response"]
    
    # Learn from feedback
    learn_from_feedback(user_id, feedback_data)
    return {"completed_agents": state.get("completed_agents", []) + ["feedback"]}

async def response_compiler_node(state):
    """Compile final response based on executed agents"""
    print("   Compiling final response")
    
    execution_plan = state.get("execution_plan", {})
    query_category = state.get("query_category")
    response_template = execution_plan.get("response_template", "Here's what I found:")
    
    # Build response based on available data
    response_parts = [response_template]
    
    if state.get("general_response"):
        response_parts.append(state["general_response"].get("response", ""))
    
    if state.get("product_recommendations"):
        products = state["product_recommendations"].get("products", [])
        if products:
            response_parts.append(f"Found {len(products)} products matching your criteria.")
    
    if state.get("final_cart"):
        total_cost = sum(float(item.get("price", 0)) for item in state["final_cart"])
        response_parts.append(f"Shopping cart ready with {len(state['final_cart'])} items, total cost: ${total_cost:.2f}")
    
    if state.get("stock_info") and state["stock_info"].get("promotions"):
        promos = state["stock_info"]["promotions"]
        response_parts.append(f"Found {len(promos)} current promotions available.")
    
    final_response = "\n".join(filter(None, response_parts))
    
    return {"final_response": final_response}

# Router function to determine execution flow
async def execution_router(state):
    """Route to appropriate agent based on execution plan"""
    execution_plan = state.get("execution_plan", {})
    required_agents = execution_plan.get("required_agents", [])
    completed_agents = state.get("completed_agents", [])
    
    # Find next agent to execute
    for agent in required_agents:
        if agent not in completed_agents:
            print(f"   Routing to: {agent}")
            return agent
    
    # All agents completed, compile response
    return "response_compiler"

# Build the flexible graph
def build_flexible_shopping_graph():
    """Build the flexible shopping graph with conditional routing"""
    builder = StateGraph(FlexibleShoppingState)
    
    # Add all agent nodes
    builder.add_node("smart_intent", smart_intent_node)
    builder.add_node("smart_preference", smart_preference_node)
    builder.add_node("smart_meal_planner", smart_meal_planner_node)
    builder.add_node("smart_product_recommender", smart_product_recommender_node)
    builder.add_node("smart_basket_builder", smart_basket_builder_node)
    builder.add_node("smart_stock_checker", smart_stock_checker_node)
    builder.add_node("smart_general_query", smart_general_query_node)
    builder.add_node("smart_feedback", smart_feedback_node)
    builder.add_node("response_compiler", response_compiler_node)
    
    # Set entry point
    builder.set_entry_point("smart_intent")
    
    # Add conditional routing between all nodes
    builder.add_conditional_edges("smart_intent", execution_router, {
        "smart_preference": "smart_preference",
        "smart_meal_planner": "smart_meal_planner", 
        "smart_product_recommender": "smart_product_recommender",
        "smart_basket_builder": "smart_basket_builder",
        "smart_stock_checker": "smart_stock_checker",
        "smart_general_query": "smart_general_query",
        "smart_feedback": "smart_feedback",
        "response_compiler": "response_compiler"
    })
    
    # Continue routing from each node
    for node_name in ["smart_preference", "smart_meal_planner", "smart_product_recommender", 
                      "smart_basket_builder", "smart_stock_checker", "smart_general_query", "smart_feedback"]:
        builder.add_conditional_edges(node_name, execution_router, {
            "smart_preference": "smart_preference",
            "smart_meal_planner": "smart_meal_planner",
            "smart_product_recommender": "smart_product_recommender", 
            "smart_basket_builder": "smart_basket_builder",
            "smart_stock_checker": "smart_stock_checker",
            "smart_general_query": "smart_general_query",
            "smart_feedback": "smart_feedback",
            "response_compiler": "response_compiler"
        })
    
    # End at response compiler
    builder.add_edge("response_compiler", END)
    
    return builder.compile()

# Create the flexible graph instance
flexible_shopping_graph = build_flexible_shopping_graph()

# Convenience function to execute with smart routing
async def execute_smart_query(user_id: str, message: str) -> Dict[str, Any]:
    """Execute a query with smart agent routing"""
    
    # First, do a quick intent extraction to determine routing
    intent = extract_intent(message)
    query_category = classify_query_category(intent, message)
    execution_plan = create_execution_plan(query_category, intent, message)
    
    print(f"🎯 Smart Routing Analysis:")
    print(f"   Query Category: {query_category.value}")
    print(f"   Required Agents: {execution_plan['required_agents']}")
    print(f"   Complexity: {execution_plan['complexity']}")
    print(f"   Skip Confirmation: {execution_plan['skip_confirmation']}")
    
    # Create initial state
    initial_state = {
        "user_id": user_id,
        "message": message,
        "intent": intent,
        "query_category": query_category.value,
        "execution_plan": execution_plan,
        "required_agents": execution_plan["required_agents"],
        "completed_agents": [],
        "feedback": {}
    }
    
    # Execute the graph
    result = await flexible_shopping_graph.ainvoke(initial_state)
    
    return {
        "execution_plan": execution_plan,
        "result": result,
        "final_response": result.get("final_response"),
        "agents_executed": result.get("completed_agents", [])
    } 