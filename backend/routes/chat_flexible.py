from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

# Import smart routing components
from agents.smart_router import (
    classify_query_category, 
    create_execution_plan, 
    should_skip_confirmation,
    QueryCategory
)
from langgraph.flexible_shopping_graph import execute_smart_query
from agents.intent_agent import extract_intent

# Import authentication
from routes.auth import get_current_user

router = APIRouter()

# Pydantic models
class SmartChatMessage(BaseModel):
    message: str = Field(..., description="User's message/query")
    session_id: Optional[str] = Field(None, description="Session identifier")

class SmartChatResponse(BaseModel):
    session_id: str
    message: str
    query_category: str
    execution_plan: Dict[str, Any]
    agents_executed: list
    response: str
    requires_confirmation: bool = False
    is_complete: bool = True
    processing_time_ms: int

@router.post("/smart-chat", response_model=SmartChatResponse)
async def smart_chat_endpoint(chat_message: SmartChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Smart chat endpoint that routes queries to only necessary agents
    Provides faster responses for simple queries
    """
    start_time = datetime.now()
    
    try:
        user_id = current_user["user_id"]
        message = chat_message.message
        session_id = chat_message.session_id or f"{user_id}_{int(datetime.now().timestamp())}"
        
        print(f"🚀 Smart Chat Processing: {message}")
        
        # Quick intent analysis for routing
        intent = extract_intent(message)
        query_category = classify_query_category(intent, message)
        execution_plan = create_execution_plan(query_category, intent, message)
        
        # Execute with smart routing
        result = await execute_smart_query(user_id, message)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SmartChatResponse(
            session_id=session_id,
            message=message,
            query_category=query_category.value,
            execution_plan=execution_plan,
            agents_executed=result["agents_executed"],
            response=result["final_response"],
            requires_confirmation=not should_skip_confirmation(query_category),
            is_complete=True,
            processing_time_ms=int(processing_time)
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"❌ Smart Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing smart chat: {str(e)}")

@router.get("/query-examples")
async def get_query_examples():
    """
    Provide examples of different query types and their routing
    """
    examples = {
        "price_check": {
            "examples": [
                "What's the price of milk?",
                "How much does organic bread cost?",
                "Price of bananas per pound?"
            ],
            "agents_used": ["general_query"],
            "skip_confirmation": True,
            "estimated_response_time": "< 2 seconds"
        },
        "availability_check": {
            "examples": [
                "Do you have almond milk?",
                "Is Greek yogurt in stock?",
                "Do you carry gluten-free bread?"
            ],
            "agents_used": ["general_query"],
            "skip_confirmation": True,
            "estimated_response_time": "< 2 seconds"
        },
        "product_recommendation": {
            "examples": [
                "Suggest low-carb snacks",
                "Recommend high-protein foods",
                "What keto products do you have?"
            ],
            "agents_used": ["intent", "preference", "product_recommender", "feedback"],
            "skip_confirmation": False,
            "estimated_response_time": "3-5 seconds"
        },
        "substitution_request": {
            "examples": [
                "What can I substitute for eggs?",
                "Alternative to almond milk?",
                "Replacement for wheat flour?"
            ],
            "agents_used": ["general_query", "stock_checker"],
            "skip_confirmation": True,
            "estimated_response_time": "2-3 seconds"
        },
        "discount_check": {
            "examples": [
                "What items are on sale?",
                "Show me current promotions",
                "Any discounts available?"
            ],
            "agents_used": ["stock_checker"],
            "skip_confirmation": True,
            "estimated_response_time": "< 2 seconds"
        },
        "meal_planning": {
            "examples": [
                "Plan 3 meals under $30",
                "Create a weekly meal plan",
                "Suggest dinner recipes for 4 people"
            ],
            "agents_used": ["intent", "preference", "meal_planner", "basket_builder", "stock_checker", "feedback"],
            "skip_confirmation": False,
            "estimated_response_time": "5-8 seconds"
        }
    }
    
    return {
        "message": "Smart routing optimizes response time by using only necessary agents",
        "total_categories": len(examples),
        "examples": examples,
        "routing_benefits": {
            "faster_simple_queries": "Price checks and availability queries respond in < 2 seconds",
            "personalized_recommendations": "Product suggestions use user preferences",
            "comprehensive_meal_planning": "Full pipeline for complex meal planning",
            "efficient_resource_usage": "Only executes required agents"
        }
    }

@router.post("/analyze-query")
async def analyze_query_routing(chat_message: SmartChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Analyze how a query would be routed without executing it
    Useful for understanding the smart routing system
    """
    try:
        message = chat_message.message
        
        # Perform routing analysis
        intent = extract_intent(message)
        query_category = classify_query_category(intent, message)
        execution_plan = create_execution_plan(query_category, intent, message)
        
        return {
            "message": message,
            "intent_analysis": intent,
            "query_category": query_category.value,
            "execution_plan": execution_plan,
            "routing_decision": {
                "agents_to_execute": execution_plan["required_agents"],
                "agents_to_skip": [
                    "intent", "preference", "meal_planner", "product_recommender", 
                    "basket_builder", "stock_checker", "feedback", "general_query"
                ],
                "skip_confirmation": execution_plan["skip_confirmation"],
                "complexity_level": execution_plan["complexity"],
                "estimated_steps": execution_plan["estimated_steps"]
            },
            "performance_benefits": {
                "agents_saved": 8 - len(execution_plan["required_agents"]),
                "estimated_time_saving": f"{(8 - len(execution_plan['required_agents'])) * 0.5}s",
                "efficiency_gain": f"{((8 - len(execution_plan['required_agents'])) / 8) * 100:.1f}%"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing query routing: {str(e)}")

# Performance comparison endpoint
@router.post("/compare-routing")
async def compare_routing_performance(chat_message: SmartChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Compare old vs new routing for a query
    """
    message = chat_message.message
    
    # Analyze smart routing
    intent = extract_intent(message)
    query_category = classify_query_category(intent, message)
    execution_plan = create_execution_plan(query_category, intent, message)
    
    # Old routing (always uses all agents for goal-based queries)
    old_routing = {
        "agents_used": ["intent", "preference", "meal_planner", "basket_builder", "stock_checker", "feedback"],
        "estimated_time": "6-8 seconds",
        "confirmation_required": True
    }
    
    # New smart routing
    new_routing = {
        "agents_used": execution_plan["required_agents"],
        "estimated_time": f"{len(execution_plan['required_agents']) * 0.7:.1f} seconds",
        "confirmation_required": not execution_plan["skip_confirmation"]
    }
    
    return {
        "query": message,
        "query_category": query_category.value,
        "old_routing": old_routing,
        "new_routing": new_routing,
        "improvement": {
            "agents_saved": len(old_routing["agents_used"]) - len(new_routing["agents_used"]),
            "time_saved": f"{6 - (len(execution_plan['required_agents']) * 0.7):.1f}s",
            "efficiency_improvement": f"{((len(old_routing['agents_used']) - len(new_routing['agents_used'])) / len(old_routing['agents_used'])) * 100:.1f}%",
            "user_experience": "Faster response" if execution_plan["skip_confirmation"] else "Same confirmation flow"
        }
    } 