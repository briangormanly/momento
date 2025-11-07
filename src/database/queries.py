"""
Database query functions for user authentication.
Handles interactions with Neo4j ApiCredentials nodes.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from neo4j import Driver
from pwdlib import PasswordHash

from src.database.connection import get_neo4j_driver, neo4j_connection



# Password hashing using bcrypt (or use PasswordHash.recommended() for Argon2)
pwd_hasher = PasswordHash.recommended()  # For Argon2 (recommended)
# OR
# from pwdlib.hashers.bcrypt import BcryptHasher
# pwd_hasher = PasswordHash(BcryptHasher())  # For bcrypt (to maintain compatibility)


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_hasher.verify(plain_password, hashed_password)


def get_user_by_email(email: str, driver: Driver = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve user credentials from Neo4j by email address.
    
    Args:
        email: User's email address
        driver: Neo4j driver instance (optional, will use default if not provided)
        
    Returns:
        Dictionary containing user data (email, password, roles) or None if not found
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    MATCH (user:ApiCredentials {emailAddress: $email})
    RETURN user.emailAddress as email, 
           user.password as password, 
           user.roles as roles
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(query, email=email)
        record = result.single()
        
        if record:
            return {
                "email": record["email"],
                "password": record["password"],
                "roles": record["roles"] or ["user"]  # Default to ["user"] if roles is None
            }
        return None


def validate_credentials(email: str, password: str, driver: Driver = None) -> Optional[Dict[str, Any]]:
    """
    Validate user credentials against stored values in Neo4j.
    
    Args:
        email: User's email address
        password: Plain text password to validate
        driver: Neo4j driver instance (optional)
        
    Returns:
        Dictionary containing user data (email, roles) if valid, None otherwise
    """
    user = get_user_by_email(email, driver)
    
    if user is None:
        return None
    
    # Verify the password
    if not verify_password(password, user["password"]):
        return None
    
    # Return user data without password
    return {
        "email": user["email"],
        "roles": user["roles"]
    }


def create_user(email: str, password: str, roles: list = None, driver: Driver = None) -> Dict[str, Any]:
    """
    Create a new ApiCredentials node in Neo4j.
    Note: This is a helper function for manual user creation.
    
    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        roles: List of role strings (defaults to ["user"])
        driver: Neo4j driver instance (optional)
        
    Returns:
        Dictionary containing created user data
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    if roles is None:
        roles = ["user"]
    
    hashed_password = hash_password(password)
    
    query = """
    CREATE (user:ApiCredentials {
        emailAddress: $email,
        password: $password,
        roles: $roles
    })
    RETURN user.emailAddress as email, user.roles as roles
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(
            query,
            email=email,
            password=hashed_password,
            roles=roles
        )
        record = result.single()
        
        return {
            "email": record["email"],
            "roles": record["roles"]
        }


def check_email_exists(email: str, driver: Driver = None) -> bool:
    """
    Check if an email address already exists in ApiCredentials.
    
    Args:
        email: Email address to check
        driver: Neo4j driver instance (optional)
        
    Returns:
        True if email exists, False otherwise
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    MATCH (user:ApiCredentials {emailAddress: $email})
    RETURN count(user) > 0 as exists
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(query, email=email)
        record = result.single()
        return record["exists"] if record else False


def create_email_verification(
    email: str,
    password_hash: str,
    token: str,
    expires_at: datetime,
    driver: Driver = None
) -> Dict[str, Any]:
    """
    Create a new EmailVerification node in Neo4j.
    
    Args:
        email: User's email address
        password_hash: Hashed password
        token: Verification token
        expires_at: Token expiration datetime
        driver: Neo4j driver instance (optional)
        
    Returns:
        Dictionary containing verification data
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    CREATE (verification:EmailVerification {
        emailAddress: $email,
        hashedPassword: $password_hash,
        token: $token,
        expiresAt: datetime($expires_at),
        createdAt: datetime($created_at)
    })
    RETURN verification.emailAddress as email,
           verification.token as token,
           verification.expiresAt as expires_at
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(
            query,
            email=email,
            password_hash=password_hash,
            token=token,
            expires_at=expires_at.isoformat(),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        record = result.single()
        
        return {
            "email": record["email"],
            "token": record["token"],
            "expires_at": record["expires_at"]
        }


def get_email_verification_by_token(token: str, driver: Driver = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve email verification record by token.
    
    Args:
        token: Verification token
        driver: Neo4j driver instance (optional)
        
    Returns:
        Dictionary containing verification data or None if not found
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    MATCH (verification:EmailVerification {token: $token})
    WHERE verification.expiresAt > datetime()
    RETURN verification.emailAddress as email,
           verification.hashedPassword as password_hash,
           verification.token as token,
           verification.expiresAt as expires_at
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(query, token=token)
        record = result.single()
        
        if record:
            return {
                "email": record["email"],
                "password_hash": record["password_hash"],
                "token": record["token"],
                "expires_at": record["expires_at"]
            }
        return None


def delete_email_verification(token: str, driver: Driver = None) -> bool:
    """
    Delete an email verification record by token.
    
    Args:
        token: Verification token
        driver: Neo4j driver instance (optional)
        
    Returns:
        True if deleted, False if not found
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    MATCH (verification:EmailVerification {token: $token})
    DELETE verification
    RETURN count(verification) as deleted_count
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(query, token=token)
        record = result.single()
        return record["deleted_count"] > 0 if record else False


def cleanup_expired_verifications(driver: Driver = None) -> int:
    """
    Delete all expired EmailVerification nodes.
    
    Args:
        driver: Neo4j driver instance (optional)
        
    Returns:
        Number of expired verifications deleted
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    query = """
    MATCH (verification:EmailVerification)
    WHERE verification.expiresAt <= datetime()
    DELETE verification
    RETURN count(verification) as deleted_count
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(query)
        record = result.single()
        return record["deleted_count"] if record else 0


def create_user_from_verification(
    email: str,
    password_hash: str,
    roles: list = None,
    driver: Driver = None
) -> Dict[str, Any]:
    """
    Create a new ApiCredentials node using already-hashed password.
    Used during email verification when password is already hashed.
    
    Args:
        email: User's email address
        password_hash: Already hashed password
        roles: List of role strings (defaults to ["user"])
        driver: Neo4j driver instance (optional)
        
    Returns:
        Dictionary containing created user data
    """
    if driver is None:
        driver = get_neo4j_driver()
    
    if roles is None:
        roles = ["user"]
    
    query = """
    CREATE (user:ApiCredentials {
        emailAddress: $email,
        password: $password_hash,
        roles: $roles
    })
    RETURN user.emailAddress as email, user.roles as roles
    """
    
    with neo4j_connection.get_session() as session:
        result = session.run(
            query,
            email=email,
            password_hash=password_hash,
            roles=roles
        )
        record = result.single()
        
        return {
            "email": record["email"],
            "roles": record["roles"]
        }

