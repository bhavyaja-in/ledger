"""
Authentication utilities for JWT token management and password hashing
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    import jwt
    from passlib.context import CryptContext
except ImportError:
    # For now, we'll implement basic auth without external dependencies
    # In production, we would use proper libraries
    jwt = None
    CryptContext = None


class AuthManager:
    """Handles authentication, password hashing, and JWT tokens"""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize auth manager with secret key"""
        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 30
        
        # For now, use basic password hashing
        # In production, use passlib with argon2
        self.pwd_context = self._get_password_context()

    def _generate_secret_key(self) -> str:
        """Generate a random secret key"""
        return secrets.token_urlsafe(32)

    def _get_password_context(self):
        """Get password context for hashing"""
        if CryptContext:
            return CryptContext(schemes=["argon2"], deprecated="auto")
        else:
            # Fallback to basic hashing for testing
            return None

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        if self.pwd_context:
            return self.pwd_context.hash(password)
        else:
            # Basic fallback for testing (NOT for production)
            salt = secrets.token_hex(16)
            return hashlib.sha256((password + salt).encode()).hexdigest() + ":" + salt

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if self.pwd_context:
            return self.pwd_context.verify(plain_password, hashed_password)
        else:
            # Basic fallback for testing (NOT for production)
            try:
                hash_part, salt = hashed_password.split(":")
                return hashlib.sha256((plain_password + salt).encode()).hexdigest() == hash_part
            except ValueError:
                return False

    def create_access_token(self, data: Dict) -> str:
        """Create an access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        if jwt:
            return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        else:
            # Basic fallback for testing
            import json
            import base64
            return base64.b64encode(json.dumps(to_encode).encode()).decode()

    def create_refresh_token(self, data: Dict) -> str:
        """Create a refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        if jwt:
            return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        else:
            # Basic fallback for testing
            import json
            import base64
            return base64.b64encode(json.dumps(to_encode).encode()).decode()

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """Verify and decode a token"""
        try:
            if jwt:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            else:
                # Basic fallback for testing
                import json
                import base64
                payload = json.loads(base64.b64decode(token.encode()).decode())
                
                # Check expiration
                if "exp" in payload:
                    exp_time = datetime.fromtimestamp(payload["exp"])
                    if datetime.utcnow() > exp_time:
                        return None
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
                
            return payload
        except Exception:
            return None

    def hash_token(self, token: str) -> str:
        """Hash a token for storage (for refresh token revocation)"""
        return hashlib.sha256(token.encode()).hexdigest()


# Global auth manager instance
_auth_manager = None


def get_auth_manager(secret_key: Optional[str] = None) -> AuthManager:
    """Get or create the global auth manager instance"""
    global _auth_manager
    if _auth_manager is None or secret_key:
        _auth_manager = AuthManager(secret_key)
    return _auth_manager