"""
Security utilities for the Sports Prediction Platform.
JWT authentication, password hashing, and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        exp_timestamp: int = payload.get("exp")
        
        if user_id is None:
            return None
        
        exp_datetime = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            exp=exp_datetime
        )
    
    except JWTError:
        return None


def create_token_pair(user_id: str, username: str, role: str = "user") -> TokenPair:
    """Create both access and refresh tokens."""
    data = {
        "sub": user_id,
        "username": username,
        "role": role
    }
    
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    # Calculate expiration in seconds
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )


def refresh_access_token(refresh_token: str) -> Optional[TokenPair]:
    """Refresh an access token using a refresh token."""
    token_data = decode_token(refresh_token)
    
    if token_data is None or token_data.exp is None:
        return None
    
    # Check if token is actually a refresh token
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        
        if payload.get("type") != "refresh":
            return None
        
    except JWTError:
        return None
    
    # Create new token pair
    return create_token_pair(
        user_id=token_data.user_id,
        username=token_data.username,
        role=token_data.role or "user"
    )


# Rate limiting helper
class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)."""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Clean old requests
        self._requests[identifier] = [
            ts for ts in self._requests[identifier] 
            if ts > window_start
        ]
        
        # Check limit
        if len(self._requests[identifier]) >= max_requests:
            return False
        
        # Record request
        self._requests[identifier].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()
