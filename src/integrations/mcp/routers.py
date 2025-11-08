"""
MCP-specific endpoints for registering external model connectors.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.integrations.mcp.schemas import MCPConnectorCreate
from src.integrations.mcp.services import MCPService

router = APIRouter(prefix="/mcp", tags=["mcp"])


@lru_cache
def get_mcp_service() -> MCPService:
    # Placeholder for eventual persistence-backed registry
    return MCPService()


@router.get("/connectors")
def list_connectors(
    user: User = Depends(get_current_user),
    service: MCPService = Depends(get_mcp_service),
):
    return service.list_connectors()


@router.post("/connectors", status_code=status.HTTP_201_CREATED)
def register_connector(
    payload: MCPConnectorCreate,
    user: User = Depends(get_current_user),
    service: MCPService = Depends(get_mcp_service),
):
    return service.register_connector(payload)
