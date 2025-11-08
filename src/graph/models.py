"""
Data models for Momento Enhanced Memory System.

This module defines all Pydantic models used throughout the system:
- Entry: Original text with embeddings and metadata
- Project: Project context for organizing memories
- Enhanced Memory, Relation, etc. (backward compatible with base system)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Core Models (Backward Compatible with mcp-neo4j-memory)
# ============================================================================

class Entity(BaseModel):
    """Represents a memory entity in the knowledge graph.
    
    Backward compatible with base mcp-neo4j-memory system.
    
    Example:
    {
        "name": "John Smith",
        "type": "person", 
        "observations": ["Works at Neo4j", "Lives in San Francisco"]
    }
    """
    name: str = Field(
        description="Unique identifier/name for the entity",
        min_length=1,
        examples=["John Smith", "Neo4j Inc", "Authentication Module"]
    )
    type: str = Field(
        description="Category: 'person', 'company', 'location', 'concept', 'component', 'technology', etc.",
        min_length=1,
        examples=["person", "company", "location", "component", "technology"]
    )
    observations: List[str] = Field(
        description="List of facts or observations about this entity",
        default_factory=list
    )


class Relation(BaseModel):
    """Represents a relationship between two entities.
    
    Backward compatible with base mcp-neo4j-memory system.
    
    Example:
    {
        "source": "John Smith",
        "target": "Neo4j Inc", 
        "relationType": "WORKS_AT"
    }
    """
    source: str = Field(
        description="Name of the source entity",
        min_length=1
    )
    target: str = Field(
        description="Name of the target entity",
        min_length=1
    )
    relationType: str = Field(
        description="Type of relationship (uppercase with underscores)",
        min_length=1,
        examples=["WORKS_AT", "USES", "IMPLEMENTED", "RELATES_TO"]
    )
