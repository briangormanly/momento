"""
Momento - FastAPI application with JWT authentication and Neo4j integration.
"""
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from src.config.settings import get_settings
from src.database.connection import neo4j_connection
from src.auth.routes import router as auth_router
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.exceptions.handlers import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    UnauthorizedError,
    authentication_error_handler,
    invalid_token_error_handler,
    token_expired_error_handler,
    unauthorized_error_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events for startup and shutdown.
    Manages Neo4j connection lifecycle and cleanup tasks.
    """
    # Startup: Connect to Neo4j
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Connecting to Neo4j at {settings.neo4j_uri}...")
    
    neo4j_connection.connect()
    
    if neo4j_connection.verify_connectivity():
        print("✓ Neo4j connection established successfully")
    else:
        print("✗ Warning: Neo4j connection verification failed")
    
    # Cleanup expired email verifications on startup
    from src.database.queries import cleanup_expired_verifications
    try:
        deleted_count = cleanup_expired_verifications()
        if deleted_count > 0:
            print(f"✓ Cleaned up {deleted_count} expired email verification(s)")
    except Exception as e:
        print(f"Warning: Failed to cleanup expired verifications: {e}")
    
    yield
    
    # Shutdown: Close Neo4j connection
    print("Shutting down...")
    neo4j_connection.close()
    print("✓ Neo4j connection closed")


# Initialize FastAPI application
app = FastAPI(
    title="Momento API",
    description="API with JWT authentication and Neo4j graph database",
    version="0.1.0",
    lifespan=lifespan
)


# Register exception handlers
app.add_exception_handler(AuthenticationError, authentication_error_handler)
app.add_exception_handler(InvalidTokenError, invalid_token_error_handler)
app.add_exception_handler(TokenExpiredError, token_expired_error_handler)
app.add_exception_handler(UnauthorizedError, unauthorized_error_handler)


# Include authentication routes
app.include_router(auth_router)


# Root endpoint (public)
@app.get("/", tags=["general"])
async def root():
    """Public root endpoint."""
    settings = get_settings()
    return {
        "message": "Welcome to Momento API",
        "version": settings.app_version,
        "docs": "/docs",
        "auth": {
            "login": "/auth/login",
            "refresh": "/auth/refresh",
            "me": "/auth/me"
        }
    }


# Health check endpoint (public)
@app.get("/health", tags=["general"])
async def health_check():
    """Check API and database health."""
    db_status = "healthy" if neo4j_connection.verify_connectivity() else "unhealthy"
    
    return {
        "status": "healthy",
        "database": db_status
    }


# Protected endpoint example
@app.get("/protected", tags=["examples"])
async def protected_route(user: User = Depends(get_current_user)):
    """
    Example of a protected route.
    Requires valid JWT access token in Authorization header.
    """
    return {
        "message": "This is a protected endpoint",
        "user": {
            "email": user.email,
            "roles": user.roles
        }
    }
