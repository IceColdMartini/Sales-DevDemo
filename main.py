
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.webhook import router as webhook_router
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sales Agent Microservice",
    description="AI-powered sales agent for product recommendations and customer conversion",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connections and validate configuration on startup"""
    try:
        # Validate configuration
        settings.validate_settings()
        logger.info("Configuration validated successfully")
        
        # Connect to databases
        postgres_handler.connect()
        logger.info("PostgreSQL connection established")
        
        mongo_handler.connect()
        logger.info("MongoDB connection established")
        
        logger.info("Sales Agent Microservice started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start microservice: {e}")
        raise HTTPException(status_code=500, detail=f"Startup failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    try:
        postgres_handler.disconnect()
        mongo_handler.disconnect()
        logger.info("Sales Agent Microservice shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Include API routes
app.include_router(webhook_router, prefix="/api", tags=["Webhook"])

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "Sales Agent Microservice is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Detailed health check with database connectivity"""
    try:
        # Check PostgreSQL connection
        postgres_status = "connected" if postgres_handler.conn and not postgres_handler.conn.closed else "disconnected"
        
        # Check MongoDB connection (with Atlas support)
        mongo_info = mongo_handler.get_connection_info()
        mongo_status = mongo_info.get("status", "disconnected")
        mongo_type = mongo_info.get("connection_type", "unknown")
        
        return {
            "status": "healthy",
            "databases": {
                "postgresql": postgres_status,
                "mongodb": mongo_status,
                "mongodb_type": mongo_type,
                "mongodb_details": mongo_info
            },
            "services": {
                "ai_service": "available" if settings.AZURE_OPENAI_API_KEY else "not_configured"
            },
            "configuration": {
                "using_atlas": settings.USE_MONGODB_ATLAS,
                "mongo_db_name": settings.effective_mongo_db_name
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")
