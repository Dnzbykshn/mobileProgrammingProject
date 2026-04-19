from __future__ import annotations

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_unit import KnowledgeUnit


class ContentRepository:
    async def list_source_types(self, db: AsyncSession) -> list[str]:
        sql = text(
            """
            SELECT DISTINCT source_type
            FROM knowledge_units
            ORDER BY source_type ASC
            """
        )
        result = await db.execute(sql)
        return [row[0] for row in result.fetchall() if row[0]]

    async def get_content_item(self, db: AsyncSession, content_id: int):
        sql = text(
            """
            SELECT id, source_type, content_text, explanation, metadata
            FROM knowledge_units
            WHERE id = :content_id
            LIMIT 1
            """
        )
        result = await db.execute(sql, {"content_id": content_id})
        return result.fetchone()

    async def vector_search(
        self,
        db: AsyncSession,
        *,
        embedding_str: str,
        limit: int,
        source_types: list[str],
    ) -> list[Any]:
        """Semantic search. Returns rows with vec_distance as col[5] (lower = closer)."""
        filters = []
        params: dict[str, Any] = {"emb": embedding_str, "lim": limit}

        if source_types:
            filters.append("source_type = ANY(:source_types)")
            params["source_types"] = source_types

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        sql = text(
            f"""
            SELECT id, source_type, content_text, explanation, metadata,
                   (embedding <=> CAST(:emb AS vector)) AS vec_distance
            FROM knowledge_units
            {where_sql}
            ORDER BY embedding <=> CAST(:emb AS vector)
            LIMIT :lim
            """
        )
        result = await db.execute(sql, params)
        return result.fetchall()

    @staticmethod
    def _normalize_tr(s: str) -> str:
        """Map Turkish/Arabic-extended chars to ASCII equivalents for fuzzy matching.
        DB content sometimes stores transliterated ASCII (kadin vs kadın), so we
        must normalize both sides of the comparison.
        """
        table = str.maketrans("şğıöüçâîûŞĞİÖÜÇÂÎÛ", "sgioucaiusgioucaiu")
        return s.lower().translate(table)

    async def text_search(
        self,
        db: AsyncSession,
        *,
        query: str,
        limit: int,
        source_types: list[str],
    ) -> list[Any]:
        """
        Hybrid text search combining PostgreSQL FTS and two LIKE passes:
        1. Exact lowercase match (handles content with proper Turkish chars)
        2. ASCII-normalised match (handles transliterated content like 'kadin')
        Both the query and content are normalized the same way.
        """
        filters = []
        query_lower = query.lower()
        query_ascii = self._normalize_tr(query)   # e.g. "kadın" → "kadin"
        params: dict[str, Any] = {
            "query": query_lower,
            "query_ascii": query_ascii,
            "ilike_query": f"%{query_lower}%",
            "ilike_ascii": f"%{query_ascii}%",
            "lim": limit,
        }

        if source_types:
            filters.append("source_type = ANY(:source_types)")
            params["source_types"] = source_types

        extra_where = f"AND {' AND '.join(filters)}" if filters else ""

        # translate() args: normalize Turkish chars inside the DB content
        _TR_FROM = "şğıöüçâîûşğıöüçâîû"
        _TR_TO   = "sgioucaiusgioucaiu"

        sql = text(
            f"""
            SELECT id, source_type, content_text, explanation, metadata,
                   GREATEST(
                       ts_rank(
                           to_tsvector('simple',
                               content_text || ' ' ||
                               COALESCE(explanation, '') || ' ' ||
                               COALESCE(metadata->>'surah_name', '') || ' ' ||
                               COALESCE(array_to_string(keywords, ' '), '')
                           ),
                           plainto_tsquery('simple', :query)
                       ),
                       ts_rank(
                           to_tsvector('simple',
                               translate(LOWER(content_text), '{_TR_FROM}', '{_TR_TO}') || ' ' ||
                               translate(LOWER(COALESCE(explanation, '')), '{_TR_FROM}', '{_TR_TO}')
                           ),
                           plainto_tsquery('simple', :query_ascii)
                       ),
                       0
                   ) AS text_rank
            FROM knowledge_units
            WHERE (
                -- exact Turkish chars in content
                LOWER(content_text) LIKE :ilike_query
                OR LOWER(COALESCE(explanation, '')) LIKE :ilike_query
                OR LOWER(COALESCE(metadata->>'surah_name', '')) LIKE :ilike_query
                OR LOWER(COALESCE(array_to_string(keywords, ' '), '')) LIKE :ilike_query
                -- ASCII-normalised: matches "kadin" when user typed "kadın"
                OR translate(LOWER(content_text), '{_TR_FROM}', '{_TR_TO}') LIKE :ilike_ascii
                OR translate(LOWER(COALESCE(explanation, '')), '{_TR_FROM}', '{_TR_TO}') LIKE :ilike_ascii
                OR translate(LOWER(COALESCE(array_to_string(keywords, ' '), '')), '{_TR_FROM}', '{_TR_TO}') LIKE :ilike_ascii
                -- FTS fallback
                OR to_tsvector('simple',
                    content_text || ' ' ||
                    COALESCE(explanation, '') || ' ' ||
                    COALESCE(metadata->>'surah_name', '')
                   ) @@ plainto_tsquery('simple', :query)
            )
            {extra_where}
            ORDER BY text_rank DESC
            LIMIT :lim
            """
        )
        result = await db.execute(sql, params)
        return result.fetchall()

    async def lookup_by_reference(
        self,
        db: AsyncSession,
        *,
        surah_no: int | None = None,
        verse_no: int | None = None,
        surah_name: str | None = None,
        limit: int = 5,
    ) -> list[Any]:
        """Direct structured lookup by surah number, verse number, or surah name."""
        filters = ["source_type = 'quran'"]
        params: dict[str, Any] = {"lim": limit}

        if surah_no is not None:
            filters.append("(metadata->>'surah_no')::int = :surah_no")
            params["surah_no"] = surah_no
        if verse_no is not None:
            filters.append("(metadata->>'verse_no')::int = :verse_no")
            params["verse_no"] = verse_no
        if surah_name:
            # Normalize so "Bakara" finds "Bakara" or "Baqara" etc.
            name_ascii = self._normalize_tr(surah_name)
            filters.append(
                "(metadata->>'surah_name' ILIKE :surah_name "
                "OR translate(LOWER(metadata->>'surah_name'), 'şğıöüçâîûşğıöüçâîû', 'sgioucaiusgioucaiu') LIKE :surah_name_ascii)"
            )
            params["surah_name"] = f"%{surah_name}%"
            params["surah_name_ascii"] = f"%{name_ascii}%"

        where_sql = f"WHERE {' AND '.join(filters)}"
        sql = text(
            f"""
            SELECT id, source_type, content_text, explanation, metadata
            FROM knowledge_units
            {where_sql}
            ORDER BY (metadata->>'verse_no')::int ASC
            LIMIT :lim
            """
        )
        result = await db.execute(sql, params)
        return result.fetchall()

    async def fetch_rows_by_ids(
        self,
        db: AsyncSession,
        ids: list[int],
        *,
        source_types: list[str],
    ) -> list[Any]:
        if not ids:
            return []

        stmt = select(
            KnowledgeUnit.id,
            KnowledgeUnit.source_type,
            KnowledgeUnit.content_text,
            KnowledgeUnit.explanation,
            KnowledgeUnit.unit_metadata.label("metadata"),
        ).where(KnowledgeUnit.id.in_(ids))

        if source_types:
            stmt = stmt.where(KnowledgeUnit.source_type.in_(source_types))

        result = await db.execute(stmt)
        rows = result.fetchall()
        rows_by_id = {int(row[0]): row for row in rows}
        return [rows_by_id[item_id] for item_id in ids if item_id in rows_by_id]
