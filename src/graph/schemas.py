"""
API schemas dedicated to the graph endpoints.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.graph.models import ContentFormat, Entity


class EntryIngestionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw note or memory text.")
    title: Optional[str] = Field(default=None, description="Optional display title for the entry.")
    summary: Optional[str] = Field(default=None, description="Optional summary to show in listings.")
    labels: List[str] = Field(default_factory=list, description="User supplied free-form labels.")
    source: Optional[str] = Field(default=None, description="Originating application or integration.")
    format: ContentFormat = Field(default=ContentFormat.MARKDOWN, description="Entry text format.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata supplied by clients.")
    process_synchronously: bool = Field(
        default=False,
        description="Use only for testing; forces extraction pipeline to run inline.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Memory Entry - Indigo meets Tributary Labs",
                    "text": "My name is Indigo Montoya ... and I am a software engineer at Tributary Labs ",
                    "labels": ["relationship", "origin-story"],
                    "source": "ios-app",
                    "metadata": {"user_id": "user-123"},
                    "process_synchronously": False,
                }
            ]
        }
    }


class EntryIngestionResponse(BaseModel):
    entry_id: str
    status: str


class TextSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)


class EntityListResponse(BaseModel):
    items: List[Entity]
    total: int
