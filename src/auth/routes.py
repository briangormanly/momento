"""
Authentication routes for login, token refresh, and user information.
"""
from fastapi import APIRouter, Depends, status, Request, Query
from datetime import timedelta, datetime, timezone

from src.auth.models import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    User,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailResponse
)
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    create_verification_token,
    verify_verification_token
)
from src.auth.dependencies import get_current_user
from src.auth.email import send_verification_email
from src.database.queries import (
    validate_credentials,
    check_email_exists,
    create_email_verification,
    get_email_verification_by_token,
    delete_email_verification,
    cleanup_expired_verifications,
    create_user_from_verification,
    hash_password
)
from src.config.settings import get_settings
from src.exceptions.handlers import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError
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
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register new user",
    description="Register a new user account with email verification"
)
async def register(credentials: RegisterRequest, request: Request) -> RegisterResponse:
    """
    Register a new user account with email verification.
    
    - **email**: User's email address
    - **password**: User's password (minimum 8 characters)
    
    Sends a verification email with a time-limited link.
    Returns the same response whether the email exists or not to prevent enumeration.
    """
    settings = get_settings()
    
    # Always return the same response to prevent email enumeration
    generic_response = RegisterResponse(
        message="Registration initiated. Please check your email to verify your account."
    )
    
    try:
        # Check if email already exists - but don't reveal this information
        if check_email_exists(credentials.email):
            # Return generic response even if email exists
            return generic_response
        
        # Hash the password
        hashed_password = hash_password(credentials.password)
        
        # Create verification token
        verification_token = create_verification_token(
            email=credentials.email,
            password_hash=hashed_password
        )
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.email_verification_expire_hours
        )
        
        # Store verification in database
        create_email_verification(
            email=credentials.email,
            password_hash=hashed_password,
            token=verification_token,
            expires_at=expires_at
        )
        
        # Get base URL from request
        base_url = str(request.base_url).rstrip('/')
        
        # Send verification email
        await send_verification_email(
            email=credentials.email,
            verification_token=verification_token,
            base_url=base_url
        )
        
    except Exception as e:
        # Log the error but still return generic response
        print(f"Registration error for {credentials.email}: {str(e)}")
        # Return generic response even if there's an error
        pass
    
    return generic_response


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


@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email and create account",
    description="Verify email address using the token from the verification email and create the user account"
)
async def verify_email(token: str = Query(..., description="Verification token from email")) -> VerifyEmailResponse:
    """
    Verify email address and create user account.
    
    - **token**: JWT verification token from the email link
    
    On success, creates the user account and returns JWT access and refresh tokens
    for immediate login.
    """
    settings = get_settings()
    
    try:
        # Verify the JWT token and extract email + password hash
        token_data = verify_verification_token(token)
        email = token_data["email"]
        password_hash = token_data["password_hash"]
        
        # Verify that the verification record exists in database
        verification_record = get_email_verification_by_token(token)
        if not verification_record:
            raise InvalidTokenError("Verification token not found or has expired")
        
        # Double-check email matches (should always match if token is valid)
        if verification_record["email"] != email:
            raise InvalidTokenError("Token data mismatch")
        
        # Check if user was already created (shouldn't happen, but be safe)
        if check_email_exists(email):
            # Clean up verification record
            delete_email_verification(token)
            raise AuthenticationError("Account already exists. Please login instead.")
        
        # Create the user account with the hashed password
        user_data = create_user_from_verification(
            email=email,
            password_hash=password_hash,
            roles=["user"]
        )
        
        # Delete the verification record
        delete_email_verification(token)
        
        # Clean up expired verifications while we're at it
        cleanup_expired_verifications()
        
        # Create token payload for new user
        token_payload = {
            "sub": user_data["email"],
            "roles": user_data["roles"]
        }
        
        # Generate JWT tokens for immediate login
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        
        return VerifyEmailResponse(
            message="Email verified successfully. Your account has been created.",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
        
    except (InvalidTokenError, TokenExpiredError) as e:
        # Re-raise token errors
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"Email verification error: {str(e)}")
        raise InvalidTokenError(f"Email verification failed: {str(e)}")

