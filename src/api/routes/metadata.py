"""
Metadata routes for enums, categories, and other reference data
"""

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.models.database import DatabaseManager
from src.api.routes.auth import get_current_user


router = APIRouter(prefix="/metadata", tags=["metadata"])


# Response Models
class EnumResponse(BaseModel):
    id: int
    enum_name: str
    patterns: List[str]
    category: str
    processor_type: str
    is_active: bool

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    name: str
    description: str


@router.get("/enums", response_model=List[EnumResponse])
async def list_enums(
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """List all transaction enums for autocomplete"""
    session = db_manager.get_session()
    
    try:
        TransactionEnum = db_manager.models["TransactionEnum"]
        
        enums = session.query(TransactionEnum).filter(
            TransactionEnum.is_active == True
        ).order_by(TransactionEnum.enum_name).all()
        
        result = []
        for enum in enums:
            result.append(EnumResponse(
                id=enum.id,
                enum_name=enum.enum_name,
                patterns=enum.patterns or [],
                category=enum.category,
                processor_type=enum.processor_type,
                is_active=enum.is_active
            ))
        
        return result
        
    finally:
        session.close()


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    current_user: dict = Depends(get_current_user),
    config = Depends()
):
    """List all available categories"""
    # Get categories from config
    # Note: In the current system, categories are loaded from config/categories.yaml
    # We'll return a simple list for now, but this could be enhanced to read from the config
    
    default_categories = [
        {"name": "food", "description": "Food and dining expenses"},
        {"name": "transport", "description": "Transportation costs"},
        {"name": "entertainment", "description": "Entertainment and leisure"},
        {"name": "utilities", "description": "Utility bills"},
        {"name": "shopping", "description": "Shopping and retail"},
        {"name": "healthcare", "description": "Medical and healthcare"},
        {"name": "education", "description": "Education and learning"},
        {"name": "income", "description": "Income and salary"},
        {"name": "transfer", "description": "Money transfers"},
        {"name": "investment", "description": "Investments and savings"},
        {"name": "other", "description": "Other miscellaneous expenses"},
    ]
    
    return [CategoryResponse(**cat) for cat in default_categories]