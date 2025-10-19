import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load .env from backend_bedrock directory explicitly (works when running from project root)
ENV_PATH = current_dir / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Shopping Assistant API (AWS Bedrock Edition)",
        description=(
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

    # Include routers with flexible import system
    def safe_import_route(module_name, route_name):
        """Try both relative and absolute imports"""
        try:
            # Try absolute import first
            module = __import__(f"backend_bedrock.routes.{module_name}", fromlist=["router"])
            return getattr(module, "router")
        except ImportError:
            try:
                # Try local import when running directly
                module = __import__(f"routes.{module_name}", fromlist=["router"])
                return getattr(module, "router")
            except ImportError:
                return None

    # Load main routes
    auth_router = safe_import_route("auth", "auth")
    if auth_router:
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
        print("✅ Loaded auth routes")
    else:
        print("⚠️ Failed to load auth routes")

    profile_router = safe_import_route("profile_setup", "profile_setup")
    if profile_router:
        app.include_router(profile_router, prefix="/api/v1/profile-setup", tags=["profile-setup"])
        print("✅ Loaded profile_setup routes")
    else:
        print("⚠️ Failed to load profile_setup routes")

    products_router = safe_import_route("products", "products")
    if products_router:
        app.include_router(products_router, prefix="/api/v1", tags=["products"])
        print("✅ Loaded products routes")
    else:
        print("⚠️ Failed to load products routes")

    # Optional/placeholder routers for future parity
    for mod, tag in [
        ("chat", "chat"),
        ("chat_history", "chat-history"),
        ("cart", "cart"),
        # ("chat_flexible", "smart-chat"),
        # ("dynamic_chat", "dynamic-chat"),
    ]:
        router = safe_import_route(mod, mod)
        if router:
            app.include_router(router, prefix="/api/v1", tags=[tag])
            print(f"✅ Loaded {mod} routes")
        else:
            print(f"⚠️ Skipped {mod} routes: Module not found")

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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=True)


