from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import settings
from app.services.embedding_service import get_embedding

try:  # pragma: no cover - depends on optional external service
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None


class GraphContextService:
    """Owns graph retrieval against the resource service Neo4j projection."""

    _driver = None

    @staticmethod
    def _normalize_tr(s: str) -> str:
        table = str.maketrans("şğıöüçâîûŞĞİÖÜÇÂÎÛ", "sgioucaiusgioucaiu")
        return s.lower().translate(table)

    @classmethod
    def _get_driver(cls):
        if not settings.GRAPH_CONTEXT_ENABLED:
            return None
        if GraphDatabase is None:
            return None
        if not settings.NEO4J_PASSWORD:
            return None
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return cls._driver

    async def get_context(
        self,
        *,
        user_text: str,
        keywords: list[str] | None = None,
        top_k: int = 8,
    ) -> dict[str, Any]:
        driver = self._get_driver()
        if driver is None:
            return self.empty()

        base_text = " ".join([user_text, *(keywords or [])]).strip()
        if not base_text:
            return self.empty()

        try:
            embedding = await get_embedding(base_text[:1500])
        except Exception:
            return self.empty()

        try:
            return await asyncio.to_thread(
                self._query_context_sync,
                embedding,
                keywords or [],
                top_k,
            )
        except Exception:
            return self.empty()

    def _query_context_sync(
        self,
        embedding: list[float],
        keywords: list[str],
        top_k: int,
    ) -> dict[str, Any]:
        driver = self._get_driver()
        if driver is None:
            return self.empty()

        with driver.session() as session:
            vector_rows = session.run(
                """
                CALL db.index.vector.queryNodes('keyword_embedding', $top_k, $embedding)
                YIELD node, score
                WITH node, score
                WHERE score >= $min_score
                OPTIONAL MATCH (ku:KnowledgeUnit)-[:TAGGED_WITH]->(node)
                OPTIONAL MATCH (sub:SubCategory)-[:HAS_KEYWORD]->(node)
                OPTIONAL MATCH (root:RootCategory)-[:HAS_SUBCATEGORY]->(sub)
                RETURN node.text AS keyword,
                       score AS score,
                       ku.id AS ku_id,
                       ku.translation AS translation,
                       ku.explanation AS explanation,
                       sub.name AS sub_category,
                       root.name AS root_category
                ORDER BY score DESC
                LIMIT $row_limit
                """,
                {
                    "top_k": max(top_k, 4),
                    "row_limit": max(top_k * 3, 12),
                    "embedding": embedding,
                    "min_score": 0.62,
                },
            ).data()

            fallback_rows = []
            if not vector_rows and keywords:
                # Normalize Turkish chars so "kadın" matches "kadin" in the graph
                normalized_kws = [self._normalize_tr(kw) for kw in keywords[:8]]
                fallback_rows = session.run(
                    """
                    UNWIND $keywords AS kw
                    MATCH (k:Keyword)
                    WHERE toLower(k.text) CONTAINS toLower(kw)
                       OR toLower(k.text_ascii) CONTAINS toLower(kw)
                    OPTIONAL MATCH (ku:KnowledgeUnit)-[:TAGGED_WITH]->(k)
                    OPTIONAL MATCH (sub:SubCategory)-[:HAS_KEYWORD]->(k)
                    OPTIONAL MATCH (root:RootCategory)-[:HAS_SUBCATEGORY]->(sub)
                    RETURN k.text AS keyword,
                           0.60 AS score,
                           ku.id AS ku_id,
                           ku.translation AS translation,
                           ku.explanation AS explanation,
                           sub.name AS sub_category,
                           root.name AS root_category
                    LIMIT $row_limit
                    """,
                    {
                        "keywords": normalized_kws,
                        "row_limit": max(top_k * 2, 10),
                    },
                ).data()

        rows = vector_rows or fallback_rows
        if not rows:
            return self.empty()

        keyword_scores: dict[str, float] = {}
        passages: list[dict[str, Any]] = []
        sub_categories: dict[str, int] = {}
        root_categories: dict[str, int] = {}

        for row in rows:
            kw = (row.get("keyword") or "").strip()
            score = float(row.get("score") or 0)
            if kw:
                current = keyword_scores.get(kw)
                if current is None or score > current:
                    keyword_scores[kw] = score

            sub = (row.get("sub_category") or "").strip()
            if sub:
                sub_categories[sub] = sub_categories.get(sub, 0) + 1

            root = (row.get("root_category") or "").strip()
            if root:
                root_categories[root] = root_categories.get(root, 0) + 1

            translation = (row.get("translation") or "").strip()
            explanation = (row.get("explanation") or "").strip()
            if translation or explanation:
                passages.append(
                    {
                        "id": row.get("ku_id"),
                        "translation": translation[:260],
                        "explanation": explanation[:260],
                    }
                )

        sorted_keywords = [
            kw for kw, _ in sorted(keyword_scores.items(), key=lambda item: item[1], reverse=True)
        ][:top_k]

        dedup_passages: list[dict[str, Any]] = []
        seen = set()
        for item in passages:
            key = (item.get("translation"), item.get("explanation"))
            if key in seen:
                continue
            seen.add(key)
            dedup_passages.append(item)
            if len(dedup_passages) >= 5:
                break

        sorted_roots = [
            name for name, _ in sorted(root_categories.items(), key=lambda item: item[1], reverse=True)
        ]
        sorted_subs = [
            name for name, _ in sorted(sub_categories.items(), key=lambda item: item[1], reverse=True)
        ]

        summary_parts = []
        if sorted_keywords:
            summary_parts.append(f"Graf anahtarları: {', '.join(sorted_keywords[:4])}")
        if sorted_subs:
            summary_parts.append(f"Graf temaları: {', '.join(sorted_subs[:3])}")
        graph_summary = " | ".join(summary_parts)

        return {
            "graph_keywords": sorted_keywords,
            "graph_passages": dedup_passages,
            "graph_sub_categories": sorted_subs,
            "graph_root_categories": sorted_roots,
            "graph_summary": graph_summary,
            "suggested_pathway_type": self._suggest_pathway_type(sorted_keywords + sorted_subs + sorted_roots),
        }

    @staticmethod
    def _suggest_pathway_type(tokens: list[str]) -> str | None:
        token_text = " ".join(tokens).lower()
        if not token_text:
            return None

        anxiety_hits = ["kayg", "stres", "korku", "panik", "endişe", "anxiety"]
        grief_hits = ["yas", "hüz", "üzünt", "kayıp", "grief", "teselli"]
        anger_hits = ["öfke", "sinir", "anger", "hilm"]

        if any(hit in token_text for hit in anxiety_hits):
            return "anxiety_management"
        if any(hit in token_text for hit in grief_hits):
            return "grief_healing"
        if any(hit in token_text for hit in anger_hits):
            return "anger_control"
        return None

    @staticmethod
    def empty() -> dict[str, Any]:
        return {
            "graph_keywords": [],
            "graph_passages": [],
            "graph_sub_categories": [],
            "graph_root_categories": [],
            "graph_summary": "",
            "suggested_pathway_type": None,
        }
