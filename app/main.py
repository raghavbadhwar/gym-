"""
GymBot-Core - Production-Ready WhatsApp Agent Backend for Gyms

Main FastAPI Application Entry Point
Features:
- WhatsApp webhook handling
- AI-powered intent classification
- Class booking with double-booking prevention
- Member onboarding and retention
- Loguru structured logging
"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import init_db, Base, engine
from app.routers import members_router, classes_router, webhooks_router, chat_router

# ===== Configure Loguru =====
# Remove default handler
logger.remove()

# Add custom handlers
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.app_env == "development" else "INFO",
    colorize=True
)

# File logging for production
if settings.app_env == "production":
    logger.add(
        "logs/gymbot_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # New file at midnight
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

# Webhook-specific log file (always enabled - crucial for debugging)
logger.add(
    "logs/webhooks_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    filter=lambda record: "webhook" in record["name"].lower() or "whatsapp" in record["name"].lower(),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    level="DEBUG"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info(f"🚀 Starting GymBot-Core API ({settings.app_env} mode)")
    logger.info(f"🏋️ Gym: {settings.gym_name}")
    
    # Initialize database
    logger.info("📦 Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.success("✅ Database initialized")
    
    # Log AI configuration
    if settings.openai_api_key:
        logger.info(f"🤖 AI Provider: OpenAI ({settings.openai_model})")
    elif settings.gemini_api_key:
        logger.info(f"🤖 AI Provider: Google Gemini ({settings.gemini_model})")
    else:
        logger.warning("⚠️ No AI API key configured - using fallback responses")
    
    # Log WhatsApp configuration
    if settings.whatsapp_access_token:
        logger.info("📱 WhatsApp: Configured")
    else:
        logger.warning("⚠️ WhatsApp: Not configured")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down GymBot-Core API")


# Create FastAPI app
app = FastAPI(
    title="GymBot-Core API",
    description="""
    Production-ready, autonomous WhatsApp Agent backend for Gyms.
    
    ## Features
    - 🤖 AI-powered intent classification (OpenAI/Gemini)
    - 📅 Class booking with double-booking prevention
    - 👤 Member onboarding and retention
    - 💬 WhatsApp Business API integration
    - 📊 Analytics and reporting
    - 🧠 Personalized AI that remembers member details
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(members_router)
app.include_router(classes_router)
app.include_router(webhooks_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "GymBot-Core API",
        "status": "running",
        "version": "1.0.0",
        "gym": settings.gym_name,
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "whatsapp": "configured" if settings.whatsapp_access_token else "not_configured",
        "ai_provider": settings.ai_provider if (settings.openai_api_key or settings.gemini_api_key) else "not_configured",
        "escalation": "enabled" if settings.manager_phone else "disabled"
    }


# For development - run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
