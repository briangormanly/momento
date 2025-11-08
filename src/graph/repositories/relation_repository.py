"""
Repository helpers for Relation edges.
"""
from __future__ import annotations

import re
from typing import Iterable, List

from src.common.logging import get_logger
from src.database.connection import neo4j_connection
from src.graph.models import Relation


logger = get_logger("graph.repositories.relation")


RELATION_NAME_PATTERN = re.compile(r"^[A-Z0-9_]+$")


class RelationRepository:
    def __init__(self):
        self.connection = neo4j_connection

    def create(self, relation: Relation) -> Relation:
        relation_type = relation.relationType.upper()
        if not RELATION_NAME_PATTERN.match(relation_type):
            raise ValueError(f"Invalid relation type '{relation.relationType}'")

        query = """
MATCH (source:Entity {id: $source_id})
MATCH (target:Entity {id: $target_id})
MERGE (source)-[r:%s]->(target)
RETURN source.id AS source, target.id AS target
        """ % relation_type
        with self.connection.get_session() as session:
            session.run(
                query,
                source_id=relation.source,
                target_id=relation.target,
            )
        return relation

    def bulk_create(self, relations: Iterable[Relation]) -> List[Relation]:
        created = []
        for relation in relations:
            try:
                created.append(self.create(relation))
            except Exception as exc:  # pragma: no cover - guard rail
                logger.warning("Failed to persist relation %s -> %s: %s", relation.source, relation.target, exc)
        return created

    def list_for_entity(self, entity_id: str) -> List[Relation]:
        query = """
        MATCH (source:Entity {id: $entity_id})-[r]->(target:Entity)
        RETURN source.id AS source, type(r) AS type, target.id AS target
        """
        with self.connection.get_session() as session:
            result = session.run(query, entity_id=entity_id)
            return [
                Relation(source=record["source"], target=record["target"], relationType=record["type"])
                for record in result
            ]
