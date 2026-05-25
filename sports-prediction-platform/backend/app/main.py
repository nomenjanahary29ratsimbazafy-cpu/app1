"""
Sports Prediction Platform - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging import get_logging_config, get_logger
from app.core.database import init_db, create_tables
from app.api.routes import router as api_router

settings = get_settings()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting Sports Prediction Platform...")
    
    # Initialize database
    init_db()
    await create_tables()
    logger.info("Database initialized")
    
    # Configure logging
    logging_config = get_logging_config(settings.LOG_LEVEL, settings.LOG_FORMAT)
    
    logger.info(f"Sports Prediction Platform v{settings.APP_VERSION} started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sports Prediction Platform...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Sports Prediction Platform API

A multi-agent AI system for sports prediction and value betting detection.

### Features
- **Real-time predictions** powered by multiple AI agents
- **Value betting detection** with Kelly Criterion staking
- **Statistical analysis** including Poisson models and Monte Carlo simulations
- **Market analysis** for sharp money and arbitrage detection
- **Risk management** with bankroll tracking

### Agents
1. Data Collector - Aggregates data from multiple sources
2. Statistical Engine - Poisson, xG, Monte Carlo
3. Machine Learning - Ensemble predictions
4. Market Analyzer - Odds movement detection
5. Psychological Context - Motivation and pressure analysis
6. Risk Management - Bankroll optimization
7. Master Orchestrator - Fuses all analyses
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "errors": exc.errors(),
            "message": "Validation error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": [str(exc)] if settings.DEBUG else ["An unexpected error occurred"],
        },
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
