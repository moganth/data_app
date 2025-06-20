import uvicorn
import time
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

# Import routers
from routes.upload_route import router as upload_route
from routes.supabase_route import router as supabase_route
from routes.mongo_route import router as mongodb_route

# Import services for health checks
from services.supabase_service import test_connection
from services.mongo_service import list_collections

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up Dataset Upload API...")

    # Test Supabase connection
    supabase_ok = await test_connection()
    if not supabase_ok:
        logger.warning("⚠️  Supabase connection failed during startup")

    # Test MongoDB connection
    try:
        collections = await list_collections()
        logger.info(f"🍃 MongoDB connected successfully. Found {len(collections)} collections.")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed during startup: {e}")

    yield

    # Shutdown
    logger.info("📴 Shutting down Dataset Upload API...")


app = FastAPI(
    title="Dataset Upload & Query API",
    description="Upload CSV/Excel datasets to MongoDB Atlas and Supabase with automatic table creation, plus query capabilities with pagination, search, and filtering.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(upload_route, prefix="/api/upload", tags=["Upload"])
app.include_router(supabase_route, prefix="/api/supabase", tags=["Supabase"])
app.include_router(mongodb_route, prefix="/api/mongodb", tags=["MongoDB"])


@app.get("/")
async def root():
    return {"message": "Dataset Upload & Query API is running!", "version": "1.0.0"}


@app.get("/Database_health")
async def health_check():
    """Health check endpoint"""
    supabase_status = await test_connection()

    # Test MongoDB connection
    mongo_status = False
    try:
        await list_collections()
        mongo_status = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")

    return {
        "status": "healthy" if (supabase_status and mongo_status) else "degraded",
        "supabase": "connected" if supabase_status else "disconnected",
        "mongodb": "connected" if mongo_status else "disconnected",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )