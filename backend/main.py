
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from routes import chat, auth, profile_setup




# Create FastAPI app
app = FastAPI(
    title="AI Grocery Shopping Assistant API",
    description="""
    A comprehensive conversational AI assistant for grocery shopping with the following capabilities:
    
    ## Features:
    - **User Authentication**: Signup, login, and profile management
    - **Meal Planning**: Plan meals with recipes and shopping lists
    - **Product Recommendations**: Get personalized product suggestions
    - **Dietary Filtering**: Filter products by dietary preferences (gluten-free, vegan, keto, etc.)
    - **General Queries**: Answer questions about products, availability, past purchases, recipes, promotions
    - **Conversational AI**: Natural conversation with goal-based and casual query handling
    - **User Profiling**: Personalized recommendations based on preferences and purchase history
    - **Stock & Promotions**: Real-time stock checking and promotional offers
    - **Feedback Learning**: Continuous improvement through user feedback
    
    ## Query Types Supported:
    - `meal_planning`: "Plan 3 meals under $50"
    - `product_recommendation`: "Suggest low-carb snacks"
    - `dietary_filter`: "Show me gluten-free items"
    - `general_query`: "Do you have organic milk?", "What are your store hours?"
    
    ## Agents:
    - Intent Classification Agent
    - User Preference Agent
    - Meal Planning Agent
    - Product Recommendation Agent
    - Basket Builder Agent
    - Stock & Promotions Agent
    - Feedback Learning Agent
    - General Query Agent (with LLM fallback)
    """,
    version="2.0.0",
    contact={
        "name": "AI Grocery Assistant Team",
        "email": "support@grocery-assistant.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(profile_setup.router, prefix="/api/v1", tags=["profile-setup"])

# Include Cart Management endpoints
try:
    from routes import cart
    app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
    print("✅ Cart Management endpoints loaded successfully")
except ImportError:
    print("⚠️  Cart management endpoints not available")

# Include Product Catalog endpoints
try:
    from routes import products
    app.include_router(products.router, prefix="/api/v1", tags=["products"])
    print("✅ Product Catalog endpoints loaded successfully")
except ImportError:
    print("⚠️  Product catalog endpoints not available")

# Include flexible smart routing (new optimized endpoint)
try:
    from routes import chat_flexible
    app.include_router(chat_flexible.router, prefix="/api/v1", tags=["smart-chat"])
except ImportError:
    print("⚠️  Smart routing not available - using traditional routing only")

# Include Dynamic Agent Flow Architecture (newest implementation)
try:
    from routes import dynamic_chat
    app.include_router(dynamic_chat.router, prefix="/api/v1", tags=["dynamic-chat"])
    print("✅ Dynamic Agent Flow Architecture loaded successfully")
except ImportError:
    print("⚠️  Dynamic flow architecture not available")

# Include Chat History endpoints
try:
    from routes import chat_history
    app.include_router(chat_history.router, prefix="/api/v1", tags=["chat-history"])
    print("✅ Chat History endpoints loaded successfully")
except ImportError:
    print("⚠️  Chat history endpoints not available")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Grocery Shopping Assistant API is running!",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "User Authentication",
            "Meal Planning",
            "Product Recommendations", 
            "Dietary Filtering",
            "General Queries",
            "Conversational AI",
            "User Profiling",
            "Stock & Promotions",
            "Feedback Learning"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "API is operational",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0"
    }

@app.get("/api-info")
async def api_info():
    """Get detailed API information"""
    return {
        "name": "AI Grocery Shopping Assistant API",
        "version": "2.0.0",
        "description": "Comprehensive conversational AI for grocery shopping with authentication",
        "endpoints": {
            "auth": {
                "signup": "/api/v1/auth/signup - User registration",
                "login": "/api/v1/auth/login - User login",
                "profile": "/api/v1/auth/profile - Get/update user profile",
                "logout": "/api/v1/auth/logout - User logout",
                "verify-token": "/api/v1/auth/verify-token - Verify JWT token"
            },
            "chat": {
                "chat": "/api/v1/chat - Main conversation endpoint",
                "confirm": "/api/v1/confirm - Confirm user actions",
                "collect-feedback": "/api/v1/collect-feedback - Start detailed feedback collection",
                "feedback-rating": "/api/v1/feedback-rating - Submit feedback rating",
                "feedback-liked": "/api/v1/feedback-liked - Submit liked items",
                "feedback-disliked": "/api/v1/feedback-disliked - Submit disliked items",
                "feedback-suggestions": "/api/v1/feedback-suggestions - Submit suggestions",
                "feedback-purchase": "/api/v1/feedback-purchase - Submit purchase intent"
            }
        },
        "query_types": [
            "meal_planning",
            "product_recommendation", 
            "dietary_filter",
            "general_query"
        ],
        "agents": [
            "Intent Classification Agent",
            "User Preference Agent", 
            "Meal Planning Agent",
            "Product Recommendation Agent",
            "Basket Builder Agent",
            "Stock & Promotions Agent",
            "Feedback Learning Agent",
            "General Query Agent"
        ]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
