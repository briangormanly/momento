"""
In-memory MCP connector registry (placeholder until persistence is added).
"""
from __future__ import annotations

from typing import Dict, List

from src.integrations.mcp.schemas import MCPConnector, MCPConnectorCreate


class MCPService:
    def __init__(self):
        self._connectors: Dict[str, MCPConnector] = {}

    def register_connector(self, payload: MCPConnectorCreate) -> MCPConnector:
        connector = MCPConnector(
            name=payload.name,
            provider=payload.provider,
            base_url=str(payload.base_url) if payload.base_url else None,
            metadata=payload.metadata,
        )
        self._connectors[str(connector.id)] = connector
        return connector

    def list_connectors(self) -> List[MCPConnector]:
        return list(self._connectors.values())
