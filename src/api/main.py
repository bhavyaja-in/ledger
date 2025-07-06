"""
FastAPI application for transaction review and classification
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.config_loader import ConfigLoader
from src.models.database import DatabaseManager
from src.utils.auth import get_auth_manager


# Global variables for dependency injection
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    # Initialize configuration
    config_loader = ConfigLoader("config/config.yaml", "config/categories.yaml")
    config = config_loader.get_config()
    
    # Initialize database
    db_manager = DatabaseManager(config, test_mode=False)
    
    # Initialize auth manager
    auth_manager = get_auth_manager()
    
    # Store in app state
    app_state["config"] = config
    app_state["db_manager"] = db_manager
    app_state["auth_manager"] = auth_manager
    app_state["config_loader"] = config_loader
    
    yield
    
    # Cleanup (if needed)
    pass


# Create FastAPI app
app = FastAPI(
    title="Ledger Transaction API",
    description="Web API for transaction review, categorization, and approval",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Include routers
from src.api.routes import auth, transactions, metadata
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(metadata.router)


# Dependency injection
def get_db_manager() -> DatabaseManager:
    """Get database manager from app state"""
    return app_state["db_manager"]


def get_auth_manager():
    """Get auth manager from app state"""
    return app_state["auth_manager"]


def get_config():
    """Get config from app state"""
    return app_state["config"]


# Basic models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, str]


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Ledger API is running",
        version="0.1.0"
    )


# Basic info endpoint  
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ledger Transaction API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)