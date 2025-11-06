"""
Pydantic models for authentication requests and responses.
Defines the data structures for login, token refresh, and user information.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "securepassword123"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Response model for token issuance."""
    access_token: str = Field(..., description="JWT access token for API authentication")
    refresh_token: str = Field(..., description="JWT refresh token for obtaining new access tokens")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900
                }
            ]
        }
    }


class RefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Valid refresh token")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Response model for user information."""
    email: str = Field(..., description="User's email address")
    roles: List[str] = Field(..., description="List of user roles")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "roles": ["user"]
                }
            ]
        }
    }


class User(BaseModel):
    """Internal user model for authentication."""
    email: str
    roles: List[str]
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "newuser@example.com",
                    "password": "securepassword123"
                }
            ]
        }
    }


class RegisterResponse(BaseModel):
    """Response model for user registration."""
    message: str = Field(..., description="Registration status message")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Registration initiated. Please check your email to verify your account."
                }
            ]
        }
    }


class VerifyEmailResponse(BaseModel):
    """Response model for email verification."""
    message: str = Field(..., description="Verification status message")
    access_token: str = Field(..., description="JWT access token for API authentication")
    refresh_token: str = Field(..., description="JWT refresh token for obtaining new access tokens")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Email verified successfully. Your account has been created.",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900
                }
            ]
        }
    }

