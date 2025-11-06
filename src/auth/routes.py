"""
Authentication routes for login, token refresh, and user information.
"""
from fastapi import APIRouter, Depends, status
from datetime import timedelta

from src.auth.models import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    User
)
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token
)
from src.auth.dependencies import get_current_user
from src.database.queries import validate_credentials
from src.config.settings import get_settings
from src.exceptions.handlers import (
    AuthenticationError,
    InvalidTokenError
)


# Create router for auth endpoints
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate with email and password to receive access and refresh tokens"
)
async def login(credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token (short-lived) and refresh token (long-lived).
    """
    settings = get_settings()
    
    # Validate credentials against Neo4j database
    user_data = validate_credentials(credentials.email, credentials.password)
    
    if user_data is None:
        raise AuthenticationError("Invalid email or password")
    
    # Create token payload
    token_data = {
        "sub": user_data["email"],
        "roles": user_data["roles"]
    }
    
    # Generate tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60  # Convert to seconds
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Use a valid refresh token to obtain a new access token"
)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """
    Refresh an access token using a valid refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns a new access token and refresh token.
    """
    settings = get_settings()
    
    try:
        # Verify the refresh token
        payload = verify_token(request.refresh_token, expected_type="refresh")
        
        # Extract user information
        email = payload.get("sub")
        roles = payload.get("roles", ["user"])
        
        if email is None:
            raise InvalidTokenError("Invalid token payload")
        
        # Create new token payload
        token_data = {
            "sub": email,
            "roles": roles
        }
        
        # Generate new tokens
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
        
    except (InvalidTokenError, Exception) as e:
        if isinstance(e, InvalidTokenError):
            raise
        raise InvalidTokenError("Failed to refresh token")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user's information.
    
    Requires valid access token in Authorization header.
    Returns user email and roles.
    """
    return UserResponse(
        email=user.email,
        roles=user.roles
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout (client-side)",
    description="Logout endpoint for client-side token cleanup. Since JWT is stateless, tokens are removed client-side."
)
async def logout():
    """
    Logout endpoint.
    
    Since JWT authentication is stateless, this endpoint mainly serves as a signal
    for the client to delete their tokens. The tokens themselves remain valid until
    they expire.
    
    For true server-side logout, you would need to implement a token blacklist.
    """
    return {
        "message": "Logout successful. Please delete tokens on the client side.",
        "detail": "Tokens remain valid until expiration. Clear them from client storage."
    }

