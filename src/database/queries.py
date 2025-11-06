"""
Database query functions for user authentication.
Handles interactions with Neo4j ApiCredentials nodes.
"""
from typing import Optional, Dict, Any
from neo4j import Driver
from passlib.context import CryptContext

from src.database.connection import get_neo4j_driver


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


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
    
    with driver.session() as session:
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
    
    with driver.session() as session:
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

