from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.api.v1.router import api_router
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title="SalesMind AI API",
    description="AI-powered sales automation platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Setup middleware (CORS, rate limiting, security headers, logging)
setup_middleware(app)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/")
async def root():
    return {
        "name": "SalesMind AI API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }
