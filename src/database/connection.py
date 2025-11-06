"""
Neo4j database connection management.
Implements singleton pattern for database driver.
"""
from neo4j import GraphDatabase, Driver
from typing import Optional
from src.config.settings import get_settings


class Neo4jConnection:
    """Singleton Neo4j connection manager."""
    
    _instance: Optional['Neo4jConnection'] = None
    _driver: Optional[Driver] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> None:
        """Initialize the Neo4j driver connection."""
        if self._driver is None:
            settings = get_settings()
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password)
            )
    
    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
    
    def get_driver(self) -> Driver:
        """
        Get the Neo4j driver instance.
        Ensures connection is initialized.
        
        Returns:
            Neo4j Driver instance
            
        Raises:
            RuntimeError: If driver is not initialized
        """
        if self._driver is None:
            raise RuntimeError("Database connection not initialized. Call connect() first.")
        return self._driver
    
    def verify_connectivity(self) -> bool:
        """
        Verify that the database connection is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            driver = self.get_driver()
            driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Database connectivity check failed: {e}")
            return False


# Global instance
neo4j_connection = Neo4jConnection()


def get_neo4j_driver() -> Driver:
    """
    Dependency function to get Neo4j driver.
    Can be used with FastAPI's Depends.
    
    Returns:
        Neo4j Driver instance
    """
    return neo4j_connection.get_driver()

