"""
Simple FastAPI application for testing
"""

import os
import sys
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.config_loader import ConfigLoader
from src.models.database import DatabaseManager
from src.utils.auth import get_auth_manager


# Create FastAPI app
app = FastAPI(
    title="Ledger Transaction API",
    description="Web API for transaction review, categorization, and approval",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    global db_manager, auth_manager, config
    
    # Initialize configuration with in-memory database
    config = {
        'database': {
            'url': 'sqlite:///:memory:',
            'test_prefix': 'test_'
        }
    }
    
    # Initialize database
    db_manager = DatabaseManager(config, test_mode=True)
    
    # Initialize auth manager
    auth_manager = get_auth_manager()
    
    print("🚀 Ledger API started successfully!")


# Basic models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


class TransactionResponse(BaseModel):
    id: int
    description: str
    debit_amount: float = None
    credit_amount: float = None
    status: str


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


@app.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions():
    """List transactions"""
    global db_manager
    
    session = db_manager.get_session()
    try:
        Transaction = db_manager.models["Transaction"]
        
        # Get first 10 transactions
        transactions = session.query(Transaction).limit(10).all()
        
        result = []
        for txn in transactions:
            result.append(TransactionResponse(
                id=txn.id,
                description=txn.description,
                debit_amount=txn.debit_amount,
                credit_amount=txn.credit_amount,
                status=getattr(txn, 'status', 'processed')  # Default to processed for old records
            ))
        
        return result
        
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)