"""
Data models for Momento Enhanced Memory System.

Defines the rich, schemaless building blocks used throughout the knowledge
graph pipeline. The `Entity` model is intentionally flexible so any type of
note, extracted entity, or observation can be represented while still
capturing enough structured information to power downstream reasoning.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# Shared Value Objects
# ============================================================================

class SystemLabel(str, Enum):
    """Reserved labels understood by the graph service."""

    ENTRY = "ENTRY"  # Full memories/notes authored by the user or an agent
    ENTITY = "ENTITY"  # Generic catch-all label for non-entry nodes
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    OBJECT = "OBJECT"
    EVENT = "EVENT"
    CONCEPT = "CONCEPT"
    OBSERVATION = "OBSERVATION"


class ContentFormat(str, Enum):
    """Formats supported for the primary textual payload."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    OTHER = "other"


class ContentBlock(BaseModel):
    """Human-readable body of a note or entity."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "format": "markdown",
                    "body": "## Morning run\nClocked 5k around Golden Gate Park.",
                    "metadata": {"language": "en", "sentiment": "positive", "tokens": 32},
                }
            ]
        }
    )

    format: ContentFormat = Field(
        default=ContentFormat.TEXT,
        description="Format of the body text; helps downstream renderers",
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Raw string payload (text, markdown, etc.)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Content specific properties (language, tokens, sentiment, ...)",
    )


class MediaAttachment(BaseModel):
    """References to images, audio, or other rich media for an entity."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "uri": "https://cdn.momento.app/media/run.jpg",
                    "media_type": "image/jpeg",
                    "title": "Morning Run Snapshot",
                    "description": "Photo taken midway through the trail.",
                    "metadata": {"width": 1024, "height": 768},
                }
            ]
        }
    )

    uri: AnyUrl = Field(
        ...,
        description="Pointer to the media resource (http(s), s3, ipfs, ...)",
    )
    media_type: str = Field(
        ...,
        min_length=1,
        description="MIME type or descriptive tag for the media resource",
        examples=["image/png", "audio/mpeg", "link", "video/mp4"],
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional human friendly title for the attachment",
    )
    description: Optional[str] = Field(
        default=None,
        description="Helper text or alt-text for accessibility/search",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured data about the asset (dimensions, size, ...)",
    )


class EmbeddingVector(BaseModel):
    """Dense vector representation used for semantic similarity search."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "text-embedding-3-large",
                    "vector": [0.12, -0.03, 0.44],
                    "created_at": "2024-01-21T09:12:33.000Z",
                    "metadata": {"dimension": 3072, "normalized": True},
                }
            ]
        }
    )

    model: str = Field(
        ...,
        min_length=1,
        description="Identifier of the embedding model/provider",
        examples=["text-embedding-3-large", "nomic-embed-text"],
    )
    vector: List[float] = Field(
        ...,
        description="Numeric values describing the embedding space representation",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the embedding was produced",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Storage for vendor specific parameters or normalization values",
    )

    @field_validator("vector")
    @classmethod
    def ensure_vector_not_empty(cls, value: List[float]) -> List[float]:
        if not value:
            raise ValueError("Embedding vector cannot be empty")
        return value


class Observation(BaseModel):
    """Structured observation/fact derived from a memory."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "22eeb5ce-1d8e-4baf-bf13-83f87e40cd55",
                    "text": "Brian mentioned training for the SF marathon.",
                    "source": "named-entity-agent",
                    "created_at": "2024-01-21T09:15:02.000Z",
                    "confidence": 0.87,
                    "metadata": {"entry_id": "f2a4b780-8b85-4f6f-b868-0ef3df739785"},
                }
            ]
        }
    )

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for referencing the observation node",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Natural language description of the fact or observation",
    )
    source: Optional[str] = Field(
        default=None,
        description="Origin of the observation (agent name, model id, user id, ...)",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp for auditing/event sourcing",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional probability/confidence score attached by the model",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any structured data that helps contextualize the observation",
    )


# ============================================================================
# Core Models (Backward Compatible with mcp-neo4j-memory)
# ============================================================================

class Entity(BaseModel):
    """Represents any node (note, extracted entity, observation) in the graph."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "f2a4b780-8b85-4f6f-b868-0ef3df739785",
                    "external_id": "notion:entry:42",
                    "name": "Morning Run - 21 Jan",
                    "summary": "Training log entry with distance, route, and companions.",
                    "labels": ["fitness", "running"],
                    "system_labels": ["ENTRY"],
                    "content": {
                        "format": "markdown",
                        "body": "Ran 5k with Alex along the Embarcadero.",
                        "metadata": {"language": "en"},
                    },
                    "attachments": [
                        {
                            "uri": "https://cdn.momento.app/run.png",
                            "media_type": "image/png",
                            "title": "Route snapshot",
                        }
                    ],
                    "embedding": {
                        "model": "text-embedding-3-large",
                        "vector": [0.12, -0.03, 0.44],
                        "created_at": "2024-01-21T09:12:33.000Z",
                    },
                    "metadata": {
                        "distance_km": 5,
                        "duration_min": 27,
                        "weather": "foggy",
                    },
                    "observations": [
                        {
                            "id": "22eeb5ce-1d8e-4baf-bf13-83f87e40cd55",
                            "text": "Alex joined for the training session.",
                            "source": "co-reference-agent",
                        }
                    ],
                    "created_at": "2024-01-21T09:12:33.000Z",
                    "updated_at": "2024-01-21T09:18:00.000Z",
                }
            ]
        },
    )

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the node used internally/for storage",
    )
    external_id: Optional[str] = Field(
        default=None,
        description="Optional mapping back to the source system/user supplied id",
    )
    name: Optional[str] = Field(
        default=None,
        description="Human readable name/title if applicable (person name, place, etc.)",
        examples=["John Smith", "Neo4j Inc", "Authentication Module"],
    )
    summary: Optional[str] = Field(
        default=None,
        description="Short description used when displaying nodes in UI",
    )
    labels: List[str] = Field(
        default_factory=list,
        description="Free-form labels/tags supplied by the user or upstream agent",
    )
    system_labels: List[SystemLabel] = Field(
        default_factory=lambda: [SystemLabel.ENTITY],
        description="Reserved, platform-recognized labels (e.g. ENTRY, PERSON, ...)",
    )
    content: Optional[ContentBlock] = Field(
        default=None,
        description="Primary textual payload for the node (full entries/memories)",
    )
    attachments: List[MediaAttachment] = Field(
        default_factory=list,
        description="Links to related media (images, audio, docs, ...)",
    )
    embedding: Optional[EmbeddingVector] = Field(
        default=None,
        description="Semantic embedding for retrieval/grounding",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary schemaless properties mirrored into the graph",
    )
    observations: List[Observation] = Field(
        default_factory=list,
        description="Additional observations/facts attached to this node",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Node creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last time the node was updated",
    )

    @field_validator("labels")
    @classmethod
    def normalize_labels(cls, values: List[str]) -> List[str]:
        """Deduplicate/trim user supplied labels while maintaining order."""
        seen = set()
        cleaned: List[str] = []
        for label in values or []:
            normalized = label.strip()
            if not normalized:
                continue
            lower = normalized.lower()
            if lower in seen:
                continue
            seen.add(lower)
            cleaned.append(normalized)
        return cleaned

    @field_validator("system_labels")
    @classmethod
    def ensure_system_labels(cls, values: List[SystemLabel]) -> List[SystemLabel]:
        """Always keep at least ENTITY and deduplicate system labels."""
        cleaned: List[SystemLabel] = []
        seen = set()
        for label in values or []:
            if label in seen:
                continue
            seen.add(label)
            cleaned.append(label)

        if SystemLabel.ENTITY not in seen:
            cleaned.insert(0, SystemLabel.ENTITY)

        return cleaned

    @property
    def is_entry(self) -> bool:
        """Convenience helper for checking if the node stores a full memory."""
        return SystemLabel.ENTRY in self.system_labels

    @model_validator(mode="after")
    def ensure_entry_payload(self) -> "Entity":
        """
        ENTRY labeled nodes should hold textual content, media, or metadata.

        This guard prevents accidentally creating empty ENTRY nodes that cannot
        reconstruct the original memory.
        """
        if self.is_entry and not any([self.content, self.attachments, self.metadata]):
            raise ValueError("ENTRY entities require content, attachments, or metadata")
        return self


class Relation(BaseModel):
    """Represents a relationship between two entities.
    
    Backward compatible with base mcp-neo4j-memory system.
    
    Example:
    {
        "source": "John Smith",
        "target": "Tributary Labs Inc", 
        "relationType": "WORKS_AT"
    }
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source": "f2a4b780-8b85-4f6f-b868-0ef3df739785",
                    "target": "b7e71642-0b2f-4c7d-a0f2-15fe385d01c8",
                    "relationType": "MENTIONED",
                }
            ]
        }
    )
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
