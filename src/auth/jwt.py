"""
JWT token creation and verification functions.
Handles access and refresh tokens with proper expiration and validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt

from src.config.settings import get_settings
from src.exceptions.handlers import InvalidTokenError, TokenExpiredError


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token (typically includes 'sub' for subject/user)
        expires_delta: Optional custom expiration time. If not provided, uses default from settings
        
    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time. If not provided, uses default from settings
        
    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        Dictionary of decoded token claims
        
    Raises:
        InvalidTokenError: If token is malformed or type doesn't match
        TokenExpiredError: If token has expired
    """
    settings = get_settings()
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise InvalidTokenError(
                f"Invalid token type. Expected '{expected_type}', got '{token_type}'"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a token without verifying signature or expiration.
    Useful for inspecting expired tokens or debugging.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary of decoded claims or None if token is malformed
    """
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
    except JWTError:
        return None


def create_verification_token(email: str, password_hash: str) -> str:
    """
    Create a JWT token for email verification.
    Includes the email and hashed password in the token payload.
    
    Args:
        email: User's email address
        password_hash: Already hashed password (from hash_password())
        
    Returns:
        Encoded JWT verification token string
    """
    settings = get_settings()
    
    # Set expiration time based on configured hours
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.email_verification_expire_hours
    )
    
    # Create token payload with email and hashed password
    to_encode = {
        "sub": email,
        "password_hash": password_hash,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "verification"
    }
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_verification_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode an email verification JWT token.
    
    Args:
        token: JWT verification token string
        
    Returns:
        Dictionary containing 'email' and 'password_hash' from token
        
    Raises:
        InvalidTokenError: If token is malformed or type doesn't match
        TokenExpiredError: If token has expired
    """
    settings = get_settings()
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "verification":
            raise InvalidTokenError(
                f"Invalid token type. Expected 'verification', got '{token_type}'"
            )
        
        # Extract required fields
        email = payload.get("sub")
        password_hash = payload.get("password_hash")
        
        if not email or not password_hash:
            raise InvalidTokenError("Token missing required claims")
        
        return {
            "email": email,
            "password_hash": password_hash
        }
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Verification link has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid verification token: {str(e)}")

