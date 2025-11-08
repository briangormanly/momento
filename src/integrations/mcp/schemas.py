"""
Schemas for Model Context Protocol (MCP) connectors.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class MCPConnectorCreate(BaseModel):
    name: str = Field(..., description="Human readable connector name.")
    provider: str = Field(..., description="Identifier for the downstream provider (ollama, openai, etc.).")
    base_url: Optional[HttpUrl] = Field(default=None, description="Optional override for provider base URL.")
    api_key: Optional[str] = Field(default=None, description="Optional API key/token.")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPConnector(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    provider: str
    base_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
