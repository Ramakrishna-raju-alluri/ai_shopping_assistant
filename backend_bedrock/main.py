import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load .env from backend_bedrock directory explicitly (works when running from project root)
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Shopping Assistant API (AWS Bedrock Edition)",
        description=(
            "Backend focused on AWS services: Bedrock, Agents, and DynamoDB.\n"
            "Provides categorized endpoints for auth, profile setup, products, and chat."
        ),
        version="3.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    try:
        from backend_bedrock.routes import auth as auth_routes
        app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["authentication"])
        print("✅ Loaded auth routes")
    except Exception as e:
        print(f"⚠️ Failed to load auth routes: {e}")

    try:
        from backend_bedrock.routes import profile_setup as profile_routes
        app.include_router(profile_routes.router, prefix="/api/v1/profile-setup", tags=["profile-setup"])
        print("✅ Loaded profile_setup routes")
    except Exception as e:
        print(f"⚠️ Failed to load profile_setup routes: {e}")

    try:
        from backend_bedrock.routes import products as products_routes
        app.include_router(products_routes.router, prefix="/api/v1", tags=["products"])
        print("✅ Loaded products routes")
    except Exception as e:
        print(f"⚠️ Failed to load products routes: {e}")

    # Optional/placeholder routers for future parity
    for mod, tag in [
        ("chat", "chat"),
        ("chat_history", "chat-history"),
        ("cart", "cart"),
        ("chat_flexible", "smart-chat"),
        ("dynamic_chat", "dynamic-chat"),
    ]:
        try:
            module = __import__(f"backend_bedrock.routes.{mod}", fromlist=["router"])
            app.include_router(getattr(module, "router"), prefix="/api/v1", tags=[tag])
            print(f"✅ Loaded {mod} routes")
        except Exception as e:
            print(f"⚠️ Skipped {mod} routes: {e}")

    @app.get("/")
    async def root():
        return {
            "message": "AI Shopping Assistant API (Bedrock) is running!",
            "version": "3.0.0",
            "status": "operational",
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "3.0.0"}

    @app.get("/api-info")
    async def api_info():
        return {
            "name": "AI Shopping Assistant API (AWS Bedrock Edition)",
            "version": "3.0.0",
            "endpoints": {
                "auth": "/api/v1/auth/*",
                "profile_setup": "/api/v1/profile-setup/*",
                "products": "/api/v1/products/*",
                "chat": "/api/v1/chat*",
            },
        }

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "status_code": exc.status_code})

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})

    return app


app = create_app()


