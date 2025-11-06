"""
FastAPI dependencies for authentication and authorization.
These work like Express.js middleware - add them to routes to protect them.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from src.auth.jwt import verify_token
from src.auth.models import User
from src.exceptions.handlers import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    UnauthorizedError
)


# HTTPBearer automatically extracts the token from the Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from the JWT token.
    
    This extracts the token from the Authorization header, validates it,
    and returns the user information. If the token is invalid or missing,
    appropriate exceptions are raised.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.email}
    
    Args:
        credentials: HTTP authorization credentials (automatically injected by FastAPI)
        
    Returns:
        User object with email and roles
        
    Raises:
        AuthenticationError: If token is missing or invalid
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is malformed
    """
    if not credentials:
        raise AuthenticationError("No authentication token provided")
    
    token = credentials.credentials
    
    try:
        # Verify the token and extract payload
        payload = verify_token(token, expected_type="access")
        
        # Extract user information from token
        email = payload.get("sub")
        roles = payload.get("roles", ["user"])
        
        if email is None:
            raise InvalidTokenError("Token missing required claims")
        
        # Create and return User object
        return User(email=email, roles=roles)
        
    except (InvalidTokenError, TokenExpiredError, AuthenticationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise AuthenticationError(f"Authentication failed: {str(e)}")


async def require_authentication(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that simply requires authentication.
    This is an alias for get_current_user but with a more explicit name.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(require_authentication)):
            return {"message": "You are authenticated"}
    """
    return user


def require_roles(required_roles: List[str]):
    """
    Dependency factory for role-based access control.
    Returns a dependency that checks if the user has any of the required roles.
    
    Usage:
        @app.get("/admin")
        async def admin_route(user: User = Depends(require_roles(["admin"]))):
            return {"message": "Admin access granted"}
    
    Args:
        required_roles: List of roles, user must have at least one
        
    Returns:
        Dependency function that validates user roles
    """
    async def check_roles(user: User = Depends(get_current_user)) -> User:
        if not user.has_any_role(required_roles):
            raise UnauthorizedError(
                f"Insufficient privileges. Required roles: {', '.join(required_roles)}"
            )
        return user
    
    return check_roles


def require_all_roles(required_roles: List[str]):
    """
    Dependency factory that requires user to have ALL specified roles.
    
    Usage:
        @app.get("/super-admin")
        async def super_admin_route(
            user: User = Depends(require_all_roles(["admin", "super"]))
        ):
            return {"message": "Super admin access granted"}
    
    Args:
        required_roles: List of roles, user must have all of them
        
    Returns:
        Dependency function that validates user has all roles
    """
    async def check_all_roles(user: User = Depends(get_current_user)) -> User:
        missing_roles = [role for role in required_roles if role not in user.roles]
        if missing_roles:
            raise UnauthorizedError(
                f"Insufficient privileges. Missing roles: {', '.join(missing_roles)}"
            )
        return user
    
    return check_all_roles


# Optional: Dependency to get user if authenticated, None otherwise
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> User | None:
    """
    Dependency to get the current user if authenticated, or None if not.
    Does not raise errors if token is missing or invalid.
    
    Useful for routes that have different behavior for authenticated vs anonymous users.
    
    Usage:
        @app.get("/content")
        async def get_content(user: User | None = Depends(get_current_user_optional)):
            if user:
                return {"content": "premium content", "user": user.email}
            return {"content": "public content"}
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, expected_type="access")
        email = payload.get("sub")
        roles = payload.get("roles", ["user"])
        
        if email:
            return User(email=email, roles=roles)
    except:
        pass
    
    return None

