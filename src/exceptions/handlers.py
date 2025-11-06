"""
Custom exception classes and handlers for authentication and authorization.
Provides standardized error responses across the API.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AuthenticationError(Exception):
    """Raised when authentication fails (invalid credentials or token)."""
    
    def __init__(self, detail: str = "Authentication failed"):
        self.detail = detail
        super().__init__(self.detail)


class InvalidTokenError(Exception):
    """Raised when a token is malformed or invalid."""
    
    def __init__(self, detail: str = "Invalid token"):
        self.detail = detail
        super().__init__(self.detail)


class TokenExpiredError(Exception):
    """Raised when a token has expired."""
    
    def __init__(self, detail: str = "Token has expired"):
        self.detail = detail
        super().__init__(self.detail)


class UnauthorizedError(Exception):
    """Raised when a user lacks sufficient privileges for an action."""
    
    def __init__(self, detail: str = "Insufficient privileges"):
        self.detail = detail
        super().__init__(self.detail)


# Exception handlers for FastAPI

async def authentication_error_handler(
    request: Request, 
    exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors with 401 status."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "authentication_error",
            "detail": exc.detail
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


async def invalid_token_error_handler(
    request: Request, 
    exc: InvalidTokenError
) -> JSONResponse:
    """Handle invalid token errors with 401 status."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "invalid_token",
            "detail": exc.detail
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


async def token_expired_error_handler(
    request: Request, 
    exc: TokenExpiredError
) -> JSONResponse:
    """Handle expired token errors with 401 status."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "token_expired",
            "detail": exc.detail
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


async def unauthorized_error_handler(
    request: Request, 
    exc: UnauthorizedError
) -> JSONResponse:
    """Handle authorization errors with 403 status."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "unauthorized",
            "detail": exc.detail
        }
    )

