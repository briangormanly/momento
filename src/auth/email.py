"""
Email service for sending verification emails using FastAPI-Mail.
Handles email configuration and verification email sending.
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import Dict, Any

from src.config.settings import get_settings


def get_mail_config() -> ConnectionConfig:
    """
    Get email connection configuration from settings.
    
    Returns:
        ConnectionConfig object for FastMail
    """
    settings = get_settings()
    
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        MAIL_FROM_NAME=settings.mail_from_name,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )


async def send_verification_email(
    email: EmailStr,
    verification_token: str,
    base_url: str = "http://localhost:8000"
) -> None:
    """
    Send a verification email with a JWT-signed link.
    
    Args:
        email: Recipient's email address
        verification_token: JWT verification token
        base_url: Base URL for the verification link (e.g., "https://api.example.com")
        
    Raises:
        Exception: If email sending fails
    """
    settings = get_settings()
    
    # Build verification URL
    verification_url = f"{base_url}/auth/verify-email?token={verification_token}"
    
    # Create email body
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to {settings.app_name}!</h2>
                
                <p>Thank you for registering. To complete your registration and activate your account, 
                please click the button below to verify your email address:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #3498db; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background-color: #f4f4f4; padding: 10px; border-radius: 3px; 
                          word-break: break-all;">
                    {verification_url}
                </p>
                
                <p style="color: #e74c3c; font-weight: bold;">
                    This link will expire in {settings.email_verification_expire_hours} hours.
                </p>
                
                <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
                    If you did not create an account, please ignore this email.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                
                <p style="font-size: 0.8em; color: #95a5a6; text-align: center;">
                    {settings.app_name} - {settings.app_version}
                </p>
            </div>
        </body>
    </html>
    """
    
    text_body = f"""
    Welcome to {settings.app_name}!
    
    Thank you for registering. To complete your registration and activate your account,
    please visit the following link to verify your email address:
    
    {verification_url}
    
    This link will expire in {settings.email_verification_expire_hours} hours.
    
    If you did not create an account, please ignore this email.
    
    ---
    {settings.app_name} - {settings.app_version}
    """
    
    # Create message
    message = MessageSchema(
        subject=f"Verify your {settings.app_name} account",
        recipients=[email],
        body=text_body,
        html=html_body,
        subtype=MessageType.html
    )
    
    # Send email
    fm = FastMail(get_mail_config())
    await fm.send_message(message)

