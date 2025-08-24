"""
Authentication routes for login, logout, and token refresh
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from src.models.database import DatabaseManager
from src.utils.auth import get_auth_manager


router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    username: str
    roles: str
    is_active: bool


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict


# Dependency to get current user from token
async def get_current_user(
    token: str = Depends(security)
) -> dict:
    """Extract current user from JWT token"""
    from src.api.main import app_state
    
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


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response
):
    """Authenticate user and return tokens"""
    from src.api.main import app_state
    
    db_manager = app_state["db_manager"]
    auth_manager = app_state["auth_manager"]
    session = db_manager.get_session()
    
    try:
        User = db_manager.models["User"]
        RefreshToken = db_manager.models["RefreshToken"]
        
        # Find user
        user = session.query(User).filter(User.username == login_data.username).first()
        
        if not user or not auth_manager.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create tokens
        access_token = auth_manager.create_access_token({"sub": user.username, "roles": user.roles})
        refresh_token = auth_manager.create_refresh_token({"sub": user.username})
        
        # Store refresh token in database
        refresh_token_hash = auth_manager.hash_token(refresh_token)
        from datetime import timedelta
        expire_time = datetime.utcnow() + timedelta(days=auth_manager.refresh_token_expire_days)
        
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expire_time,
            is_revoked=False
        )
        
        session.add(db_refresh_token)
        session.commit()
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * auth_manager.refresh_token_expire_days  # 30 days
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=auth_manager.access_token_expire_minutes * 60  # seconds
        )
        
    finally:
        session.close()


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request
):
    """Refresh access token using refresh token"""
    from src.api.main import app_state
    
    db_manager = app_state["db_manager"]
    auth_manager = app_state["auth_manager"]
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify refresh token
    payload = auth_manager.verify_token(refresh_token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    session = db_manager.get_session()
    try:
        User = db_manager.models["User"]
        RefreshToken = db_manager.models["RefreshToken"]
        
        # Verify token exists in database and is not revoked
        token_hash = auth_manager.hash_token(refresh_token)
        db_token = session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False
        ).first()
        
        if not db_token or db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )
        
        # Get user
        user = session.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled"
            )
        
        # Create new access token
        access_token = auth_manager.create_access_token({"sub": user.username, "roles": user.roles})
        
        return TokenResponse(
            access_token=access_token,
            expires_in=auth_manager.access_token_expire_minutes * 60  # seconds
        )
        
    finally:
        session.close()


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """Logout user and revoke refresh token"""
    from src.api.main import app_state
    
    db_manager = app_state["db_manager"]
    auth_manager = app_state["auth_manager"]
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        session = db_manager.get_session()
        try:
            RefreshToken = db_manager.models["RefreshToken"]
            
            # Revoke refresh token
            token_hash = auth_manager.hash_token(refresh_token)
            db_token = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()
            
            if db_token:
                db_token.is_revoked = True
                session.commit()
                
        finally:
            session.close()
    
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user)