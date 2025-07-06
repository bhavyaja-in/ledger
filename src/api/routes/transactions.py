"""
Transaction routes for CRUD operations and classification
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.models.database import DatabaseManager


router = APIRouter(prefix="/transactions", tags=["transactions"])


# Request/Response Models
class TransactionResponse(BaseModel):
    id: int
    transaction_hash: str
    institution_id: int
    processed_file_id: int
    transaction_date: datetime
    description: str
    debit_amount: Optional[float]
    credit_amount: Optional[float]
    balance: Optional[float]
    reference_number: Optional[str]
    transaction_type: str
    currency: str
    enum_id: Optional[int]
    category: Optional[str]
    transaction_category: Optional[str]
    reason: Optional[str]
    splits: Optional[List[Dict[str, Any]]]
    has_splits: bool
    is_settled: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
    has_more: bool


class SplitRequest(BaseModel):
    person: str
    percentage: float


class ClassifyRequest(BaseModel):
    regex: List[str]
    enum_name: str
    enum_category: str
    txn_category: str
    reason: str
    splits: Optional[List[SplitRequest]] = None


class SkipRequest(BaseModel):
    reason: str


class SuggestionResponse(BaseModel):
    enum_id: Optional[int] = None
    enum_name: Optional[str] = None
    category: Optional[str] = None
    txn_category: Optional[str] = None
    pattern_suggestions: List[str] = []


async def get_current_user_for_transactions(
    token: str = Depends(HTTPBearer())
) -> dict:
    """Get current user for transactions"""
    from src.api.main import app_state
    from src.utils.auth import get_auth_manager
    from fastapi.security import HTTPBearer
    from fastapi import HTTPException, status
    
    security = HTTPBearer()
    db_manager = app_state["db_manager"]
    auth_manager = app_state["auth_manager"]
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = auth_manager.verify_token(token.credentials, "access")
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Get user from database
    session = db_manager.get_session()
    try:
        User = db_manager.models["User"]
        user = session.query(User).filter(User.username == username).first()
        
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "roles": user.roles,
            "is_active": user.is_active
        }
    finally:
        session.close()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    status: Optional[str] = Query(None, regex="^(pending|processed|skipped)$"),
    search: Optional[str] = Query(None),
    processor_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_for_transactions)
):
    """List transactions with pagination and filtering"""
    from src.api.main import app_state
    
    db_manager = app_state["db_manager"]
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        
        # Build query
        query = session.query(Transaction)
        
        # Apply filters
        if status:
            query = query.filter(Transaction.status == status)
        
        if search:
            query = query.filter(Transaction.description.contains(search))
        
        if processor_type:
            # Join with processed_file to filter by processor_type
            ProcessedFile = db_manager.models["ProcessedFile"]
            query = query.join(ProcessedFile).filter(ProcessedFile.processor_type == processor_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        transactions = query.order_by(Transaction.id).offset(offset).limit(size).all()
        
        # Convert to response format
        items = []
        for txn in transactions:
            item_dict = {
                "id": txn.id,
                "transaction_hash": txn.transaction_hash,
                "institution_id": txn.institution_id,
                "processed_file_id": txn.processed_file_id,
                "transaction_date": txn.transaction_date,
                "description": txn.description,
                "debit_amount": txn.debit_amount,
                "credit_amount": txn.credit_amount,
                "balance": txn.balance,
                "reference_number": txn.reference_number,
                "transaction_type": txn.transaction_type,
                "currency": txn.currency,
                "enum_id": txn.enum_id,
                "category": txn.category,
                "transaction_category": txn.transaction_category,
                "reason": txn.reason,
                "splits": txn.splits,
                "has_splits": txn.has_splits,
                "is_settled": txn.is_settled,
                "status": txn.status,
                "created_at": txn.created_at,
                "updated_at": txn.updated_at,
            }
            items.append(TransactionResponse(**item_dict))
        
        has_more = (offset + size) < total
        
        return TransactionListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            has_more=has_more
        )
        
    finally:
        session.close()


@router.get("/next")
async def get_next_pending_transaction(
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Get the next pending transaction for processing"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        
        # Get the oldest pending transaction
        transaction = session.query(Transaction).filter(
            Transaction.status == "pending"
        ).order_by(Transaction.id).first()
        
        if not transaction:
            return {"message": "No pending transactions"}
        
        return {"id": transaction.id}
        
    finally:
        session.close()


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Get a specific transaction by ID"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        item_dict = {
            "id": transaction.id,
            "transaction_hash": transaction.transaction_hash,
            "institution_id": transaction.institution_id,
            "processed_file_id": transaction.processed_file_id,
            "transaction_date": transaction.transaction_date,
            "description": transaction.description,
            "debit_amount": transaction.debit_amount,
            "credit_amount": transaction.credit_amount,
            "balance": transaction.balance,
            "reference_number": transaction.reference_number,
            "transaction_type": transaction.transaction_type,
            "currency": transaction.currency,
            "enum_id": transaction.enum_id,
            "category": transaction.category,
            "transaction_category": transaction.transaction_category,
            "reason": transaction.reason,
            "splits": transaction.splits,
            "has_splits": transaction.has_splits,
            "is_settled": transaction.is_settled,
            "status": transaction.status,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
        }
        
        return TransactionResponse(**item_dict)
        
    finally:
        session.close()


@router.get("/{transaction_id}/suggestions", response_model=SuggestionResponse)
async def get_transaction_suggestions(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Get suggestions for transaction classification"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        TransactionEnum = db_manager.models["TransactionEnum"]
        
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Simple suggestion logic - check for exact matches in enum patterns
        description_lower = transaction.description.lower()
        
        # Look for existing enums that might match
        enums = session.query(TransactionEnum).filter(TransactionEnum.is_active == True).all()
        
        for enum in enums:
            patterns = enum.patterns if enum.patterns else []
            for pattern in patterns:
                if pattern.lower() in description_lower:
                    return SuggestionResponse(
                        enum_id=enum.id,
                        enum_name=enum.enum_name,
                        category=enum.category,
                        txn_category=enum.category,  # Default to enum category
                        pattern_suggestions=[pattern]
                    )
        
        # No match found, provide pattern suggestions
        words = description_lower.replace("-", " ").replace("_", " ").split()
        significant_words = [word for word in words if len(word) > 3 and word.isalpha()]
        
        return SuggestionResponse(
            pattern_suggestions=significant_words[:3]  # Top 3 suggestions
        )
        
    finally:
        session.close()


@router.post("/{transaction_id}/classify")
async def classify_transaction(
    transaction_id: int,
    classify_data: ClassifyRequest,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Classify a transaction"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        TransactionEnum = db_manager.models["TransactionEnum"]
        AuditLog = db_manager.models["AuditLog"]
        
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        if transaction.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not in pending status"
            )
        
        # Create or update enum
        enum_obj = session.query(TransactionEnum).filter(
            TransactionEnum.enum_name == classify_data.enum_name
        ).first()
        
        if enum_obj:
            # Update existing enum patterns
            existing_patterns = set(enum_obj.patterns or [])
            new_patterns = existing_patterns.union(set(classify_data.regex))
            enum_obj.patterns = list(new_patterns)
            enum_obj.category = classify_data.enum_category
            enum_obj.updated_at = datetime.utcnow()
        else:
            # Create new enum
            enum_obj = TransactionEnum(
                enum_name=classify_data.enum_name,
                patterns=classify_data.regex,
                category=classify_data.enum_category,
                processor_type="icici_bank",  # TODO: Get from transaction context
                is_active=True
            )
            session.add(enum_obj)
            session.flush()  # Get the ID
        
        # Update transaction
        old_status = transaction.status
        transaction.enum_id = enum_obj.id
        transaction.category = classify_data.enum_category
        transaction.transaction_category = classify_data.txn_category
        transaction.reason = classify_data.reason
        transaction.status = "processed"
        transaction.updated_at = datetime.utcnow()
        
        # Handle splits if provided
        if classify_data.splits:
            splits_data = [{"person": s.person, "percentage": s.percentage} for s in classify_data.splits]
            transaction.splits = splits_data
            transaction.has_splits = True
            
            # TODO: Create TransactionSplit records
        
        # Create audit log
        audit_log = AuditLog(
            transaction_id=transaction.id,
            user_id=current_user["id"],
            action="classify",
            from_status=old_status,
            to_status="processed",
            data={
                "enum_name": classify_data.enum_name,
                "enum_category": classify_data.enum_category,
                "txn_category": classify_data.txn_category,
                "reason": classify_data.reason,
                "patterns": classify_data.regex,
                "splits": splits_data if classify_data.splits else None
            }
        )
        session.add(audit_log)
        
        session.commit()
        
        return {"message": "Transaction classified successfully"}
        
    finally:
        session.close()


@router.post("/{transaction_id}/skip")
async def skip_transaction(
    transaction_id: int,
    skip_data: SkipRequest,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Skip a transaction"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        SkippedTransaction = db_manager.models["SkippedTransaction"]
        AuditLog = db_manager.models["AuditLog"]
        
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        if transaction.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not in pending status"
            )
        
        # Update transaction status
        old_status = transaction.status
        transaction.status = "skipped"
        transaction.updated_at = datetime.utcnow()
        
        # Create skipped transaction record
        skipped_txn = SkippedTransaction(
            transaction_hash=transaction.transaction_hash,
            institution_id=transaction.institution_id,
            processed_file_id=transaction.processed_file_id,
            raw_data={
                "description": transaction.description,
                "debit_amount": transaction.debit_amount,
                "credit_amount": transaction.credit_amount,
                "transaction_date": transaction.transaction_date.isoformat(),
            },
            skip_reason=skip_data.reason
        )
        session.add(skipped_txn)
        
        # Create audit log
        audit_log = AuditLog(
            transaction_id=transaction.id,
            user_id=current_user["id"],
            action="skip",
            from_status=old_status,
            to_status="skipped",
            data={"reason": skip_data.reason}
        )
        session.add(audit_log)
        
        session.commit()
        
        return {"message": "Transaction skipped successfully"}
        
    finally:
        session.close()


@router.post("/{transaction_id}/reprocess")
async def reprocess_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Reprocess a skipped transaction"""
    session = db_manager.get_session()
    
    try:
        Transaction = db_manager.models["Transaction"]
        AuditLog = db_manager.models["AuditLog"]
        
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        if transaction.status != "skipped":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not in skipped status"
            )
        
        # Update transaction status
        old_status = transaction.status
        transaction.status = "pending"
        transaction.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            transaction_id=transaction.id,
            user_id=current_user["id"],
            action="reprocess",
            from_status=old_status,
            to_status="pending",
            data={}
        )
        session.add(audit_log)
        
        session.commit()
        
        return {"message": "Transaction set for reprocessing"}
        
    finally:
        session.close()