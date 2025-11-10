"""
Persistence helpers for Entity nodes in Neo4j.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from neo4j.graph import Node

from src.common.logging import get_logger
from src.database.connection import neo4j_connection
from src.graph.models import Entity


logger = get_logger("graph.repositories.entity")

JSON_FIELDS = {
    "content",
    "attachments",
    "embedding",
    "metadata",
    "observations",
}


class EntityRepository:
    def __init__(self):
        self.connection = neo4j_connection

    """ Upsert an entity into the graph. """
    def upsert(self, entity: Entity) -> Entity:
        payload = self._serialize_entity(entity)
        # Ensure system labels are applied as Neo4j labels in addition to :Entity
        # We use FOREACH with CASE to conditionally set labels from parameters.
        query = """
        MERGE (e:Entity {id: $entity.id})
        SET e = $entity
        // Apply system labels as Neo4j labels
        FOREACH (_ IN CASE WHEN 'ENTRY' IN $entity.system_labels THEN [1] ELSE [] END | SET e:ENTRY)
        FOREACH (_ IN CASE WHEN 'ENTITY' IN $entity.system_labels THEN [1] ELSE [] END | SET e:ENTITY)
        FOREACH (_ IN CASE WHEN 'PERSON' IN $entity.system_labels THEN [1] ELSE [] END | SET e:PERSON)
        FOREACH (_ IN CASE WHEN 'LOCATION' IN $entity.system_labels THEN [1] ELSE [] END | SET e:LOCATION)
        FOREACH (_ IN CASE WHEN 'ORGANIZATION' IN $entity.system_labels THEN [1] ELSE [] END | SET e:ORGANIZATION)
        FOREACH (_ IN CASE WHEN 'OBJECT' IN $entity.system_labels THEN [1] ELSE [] END | SET e:OBJECT)
        FOREACH (_ IN CASE WHEN 'EVENT' IN $entity.system_labels THEN [1] ELSE [] END | SET e:EVENT)
        FOREACH (_ IN CASE WHEN 'CONCEPT' IN $entity.system_labels THEN [1] ELSE [] END | SET e:CONCEPT)
        FOREACH (_ IN CASE WHEN 'OBSERVATION' IN $entity.system_labels THEN [1] ELSE [] END | SET e:OBSERVATION)
        RETURN e
        """
        with self.connection.get_session() as session:
            record = session.run(query, entity=payload).single()
            if not record:
                raise RuntimeError("Failed to persist entity")
            return self._node_to_entity(record["e"])

    def bulk_create(self, entities: Iterable[Entity]) -> List[Entity]:
        entities = list(entities)
        if not entities:
            return []

        payload = [self._serialize_entity(entity) for entity in entities]
        query = """
        UNWIND $entities AS entity
        MERGE (e:Entity {id: entity.id})
        SET e = entity
        // Apply system labels as Neo4j labels
        FOREACH (_ IN CASE WHEN 'ENTRY' IN entity.system_labels THEN [1] ELSE [] END | SET e:ENTRY)
        FOREACH (_ IN CASE WHEN 'ENTITY' IN entity.system_labels THEN [1] ELSE [] END | SET e:ENTITY)
        FOREACH (_ IN CASE WHEN 'PERSON' IN entity.system_labels THEN [1] ELSE [] END | SET e:PERSON)
        FOREACH (_ IN CASE WHEN 'LOCATION' IN entity.system_labels THEN [1] ELSE [] END | SET e:LOCATION)
        FOREACH (_ IN CASE WHEN 'ORGANIZATION' IN entity.system_labels THEN [1] ELSE [] END | SET e:ORGANIZATION)
        FOREACH (_ IN CASE WHEN 'OBJECT' IN entity.system_labels THEN [1] ELSE [] END | SET e:OBJECT)
        FOREACH (_ IN CASE WHEN 'EVENT' IN entity.system_labels THEN [1] ELSE [] END | SET e:EVENT)
        FOREACH (_ IN CASE WHEN 'CONCEPT' IN entity.system_labels THEN [1] ELSE [] END | SET e:CONCEPT)
        FOREACH (_ IN CASE WHEN 'OBSERVATION' IN entity.system_labels THEN [1] ELSE [] END | SET e:OBSERVATION)
        RETURN e
        """
        with self.connection.get_session() as session:
            result = session.run(query, entities=payload)
            return [self._node_to_entity(record["e"]) for record in result]

    def get(self, entity_id: str) -> Optional[Entity]:
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        with self.connection.get_session() as session:
            record = session.run(query, entity_id=entity_id).single()
            return self._node_to_entity(record["e"]) if record else None

    def list(self, limit: int = 50, skip: int = 0) -> List[Entity]:
        query = """
        MATCH (e:Entity)
        RETURN e
        SKIP $skip
        LIMIT $limit
        """
        with self.connection.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            return [self._node_to_entity(record["e"]) for record in result]

    def search(self, query_text: str, limit: int = 20) -> List[Entity]:
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($q)
           OR toLower(e.summary) CONTAINS toLower($q)
        RETURN e
        LIMIT $limit
        """
        with self.connection.get_session() as session:
            result = session.run(query, q=query_text, limit=limit)
            return [self._node_to_entity(record["e"]) for record in result]

    def delete(self, entity_id: str) -> bool:
        query = """
        MATCH (e:Entity {id: $entity_id})
        DETACH DELETE e
        RETURN count(e) AS deleted_count
        """
        with self.connection.get_session() as session:
            record = session.run(query, entity_id=entity_id).single()
            return bool(record and record["deleted_count"])

    def _serialize_entity(self, entity: Entity) -> Dict[str, Any]:
        payload = entity.model_dump(mode="json")
        for field in JSON_FIELDS:
            value = payload.get(field)
            if value is not None:
                payload[field] = json.dumps(value)
        return payload

    def _node_to_entity(self, node: Node) -> Entity:
        data = dict(node)
        for field in JSON_FIELDS:
            value = data.get(field)
            if isinstance(value, str) and value:
                try:
                    data[field] = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON field '%s' on entity %s", field, data.get("id"))
        return Entity.model_validate(data)
