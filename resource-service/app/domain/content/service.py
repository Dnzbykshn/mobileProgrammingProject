from __future__ import annotations

import asyncio
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.content.models import ContentHit, ContentSearchQuery
from app.repositories.content_repository import ContentRepository
from app.services.embedding_service import get_embedding
from app.services.graph_context_service import GraphContextService


ISLAMIC_KEYWORDS = {
    "allah", "kuran", "quran", "ayet", "sure", "hadis", "namaz", "dua",
    "oruç", "zekat", "hac", "peygamber", "muhammed", "iman", "islam",
    "cennet", "cehennem", "melek", "şeytan", "tevbe", "sabır", "şükür",
    "tevekkül", "ihlas", "rahman", "rahim", "esma", "zikir",
}

# Words that signal a command/navigational query (clean before searching)
COMMAND_STOP_WORDS = {
    "istiyorum", "oku", "söyle", "ver", "lazım", "göster", "bul", "getir",
}

# High-frequency noise to strip from keyword extraction
NOISE_WORDS = {
    "bana", "beni", "benim", "bir", "için", "nasıl", "nedir", "hakkında",
    "ile", "de", "da", "ki", "mi", "mı", "mu", "mü", "ve", "ya",
}

EMOTION_MAPPINGS = {
    "korkuyorum": "korku güven tevekkül",
    "korktum": "korku güven tevekkül",
    "üzgünüm": "hüzün teselli rahmet",
    "üzüldüm": "hüzün teselli rahmet",
    "kızgınım": "öfke sabır hilm",
    "sinirli": "öfke sabır hilm",
    "bunaldım": "sıkıntı ferahlık inşirah",
    "daraldım": "darlık genişlik ferahlık",
    "endişeleniyorum": "endişe huzur sekinet",
    "endişeliyim": "endişe huzur sekinet",
    "kaygılıyım": "kaygı huzur tevekkül",
    "yalnızım": "yalnızlık yakınlık üns",
    "mutsuzum": "hüzün teselli rahmet sabır",
    "umutsuzum": "umut rahmet sabır tevbe",
    "pişmanım": "pişmanlık tevbe af mağfiret",
}

# Structured Quran reference patterns
_SURAH_VERSE_NUMERIC = re.compile(r"^\s*(\d{1,3})\s*[:.,]\s*(\d{1,3})\s*$")
_SURAH_NAME_VERSE = re.compile(
    r"^\s*([A-Za-zÇĞİÖŞÜçğıöşüâîû\-]{3,})\s+(\d{1,3})\s*$"
)
_SURAH_NAME_ONLY = re.compile(
    r"^\s*(?:sure|sura|surah)[\s:]+([A-Za-zÇĞİÖŞÜçğıöşüâîû\-]{3,})\s*$",
    re.IGNORECASE,
)

# Token extractor: Latin + Turkish + Arabic script chars
_TOKEN_RE = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşüâîûÀ-ÿ\u0600-\u06FF]+")

_RRF_K = 60


class ContentService:
    """Owns retrieval orchestration inside the resource service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ContentRepository()
        self.graph_context_service = GraphContextService()

    async def search(self, search: ContentSearchQuery) -> list[ContentHit]:
        # 1. Structured reference lookup ("2:255", "Bakara 255", "Sure Fatiha")
        ref = self._detect_structured_query(search.query)
        if ref:
            rows = await self.repository.lookup_by_reference(
                self.db, **ref, limit=search.limit
            )
            if rows:
                return [self._map_row(r, score_hint="lookup") for r in rows]

        # 2. Resolve mode and clean/expand query
        mode = self._resolve_mode(search.query)
        if mode == "RULE":
            resolved_query = self._clean_query(search.query)
        elif mode == "SMART":
            resolved_query = self._expand_query(search.query)
        else:
            resolved_query = search.query

        # For very short SIMPLE queries (1-2 words), add source context so the
        # embedding captures retrieval intent rather than just word-level meaning.
        # "Kadın" → "Kadın ile ilgili Kuran ayet ve hadis" gives the model enough
        # context to find semantically relevant passages.
        if mode == "SIMPLE" and len(search.query.split()) <= 2:
            source_hint = ", ".join(search.source_types) if search.source_types else "kuran"
            resolved_query = f"{resolved_query} ile ilgili {source_hint} ayet ve hadis"

        # 3. Graph context enrichment
        graph_context = await self._get_graph_context(
            original_query=search.query,
            resolved_query=resolved_query,
            mode=mode,
        )
        graph_ids = self._extract_graph_ids(graph_context)
        final_query = self._merge_graph_query(resolved_query, graph_context)

        # 4. Run vector search + text/regex search in parallel
        fetch_limit = max(search.limit * 3, 20)
        vector_rows, text_rows = await asyncio.gather(
            self._vector_search(
                query=final_query,
                limit=fetch_limit,
                source_types=search.source_types,
            ),
            self._text_search(
                query=resolved_query,
                limit=fetch_limit,
                source_types=search.source_types,
            ),
        )

        # Short keyword queries (SIMPLE, ≤3 words): exact text matches should
        # outrank semantic-only matches — users expect to find the word they typed.
        text_weight = (
            2.5 if mode == "SIMPLE" and len(search.query.split()) <= 3 else 1.0
        )

        # 5. RRF merge vector + text, then prioritise graph-matched rows
        candidates = self._rrf_merge(
            vector_rows=vector_rows,
            text_rows=text_rows,
            limit=fetch_limit,
            text_weight=text_weight,
        )
        candidates = self._rerank_with_graph(candidates, graph_ids)

        # 6. Assign score hints and build result list
        has_graph = bool(graph_ids)
        vector_ids = {int(r[0]) for r in vector_rows}
        text_ids = {int(r[0]) for r in text_rows}
        results: list[ContentHit] = []
        for row in candidates:
            row_id = int(row[0])
            if has_graph:
                hint = "hybrid"
            elif row_id in vector_ids and row_id in text_ids:
                hint = "hybrid"
            elif row_id in text_ids:
                hint = "text"
            else:
                hint = "semantic"
            results.append(self._map_row(row, score_hint=hint))

        # 7. Backfill from graph direct matches when results are short
        if len(results) < search.limit and graph_ids:
            graph_rows = await self.repository.fetch_rows_by_ids(
                self.db,
                graph_ids,
                source_types=search.source_types,
            )
            graph_results = [self._map_row(r, score_hint="graph") for r in graph_rows]
            results = self._merge_ranked_results(results, graph_results, limit=search.limit)

        return results[:search.limit]

    async def get_content_item(self, content_id: int) -> ContentHit:
        row = await self.repository.get_content_item(self.db, content_id)
        if not row:
            raise LookupError("Content item not found")
        return self._map_row(row, score_hint="lookup")

    async def list_source_types(self) -> list[str]:
        return await self.repository.list_source_types(self.db)

    async def find_supporting_passages(
        self,
        *,
        query: str,
        keywords: list[str],
        limit: int = 8,
        source_types: list[str] | None = None,
    ) -> list[ContentHit]:
        merged_query = " ".join([query, *keywords]).strip()
        return await self.search(
            ContentSearchQuery(
                query=merged_query or query,
                limit=limit,
                source_types=source_types or ["quran"],
            )
        )

    # ------------------------------------------------------------------ #
    # Mode resolution                                                       #
    # ------------------------------------------------------------------ #

    def _resolve_mode(self, query: str) -> str:
        query_lower = query.lower()
        words = query_lower.split()

        # Short emotional queries → replace with Islamic concept terms
        # Only apply for short queries to avoid losing context in complex sentences
        if len(words) <= 5 and any(emotion in query_lower for emotion in EMOTION_MAPPINGS):
            return "RULE"
        # Islamic topic keyword → direct semantic works well
        if any(word in ISLAMIC_KEYWORDS for word in words):
            return "SIMPLE"
        # Command/navigational noise → clean before searching
        if any(stop in query_lower for stop in COMMAND_STOP_WORDS):
            return "RULE"
        # Short queries → simple semantic is sufficient
        if len(words) < 5:
            return "SIMPLE"
        return "SMART"

    # ------------------------------------------------------------------ #
    # Structured reference detection                                        #
    # ------------------------------------------------------------------ #

    def _detect_structured_query(self, query: str) -> dict[str, Any] | None:
        """Parse Quran references: '2:255', 'Bakara 255', 'Sure Fatiha'."""
        q = query.strip()

        m = _SURAH_VERSE_NUMERIC.match(q)
        if m:
            return {"surah_no": int(m.group(1)), "verse_no": int(m.group(2))}

        m = _SURAH_NAME_VERSE.match(q)
        if m:
            name = m.group(1)
            if name.lower() not in COMMAND_STOP_WORDS and len(name) >= 3:
                return {"surah_name": name, "verse_no": int(m.group(2))}

        m = _SURAH_NAME_ONLY.match(q)
        if m:
            return {"surah_name": m.group(1)}

        return None

    # ------------------------------------------------------------------ #
    # Query cleaning / expansion                                            #
    # ------------------------------------------------------------------ #

    def _clean_query(self, query: str) -> str:
        """RULE mode: replace emotional term with Islamic concept terms."""
        query_lower = query.lower()
        for emotion, replacement in EMOTION_MAPPINGS.items():
            if emotion in query_lower:
                return replacement
        # Fallback: strip noise/command words, return clean tokens
        tokens = self._extract_query_keywords(query)
        return " ".join(tokens) or query

    def _expand_query(self, query: str) -> str:
        """
        SMART mode: strip noise, deduplicate, inline-expand any emotion terms,
        producing a cleaner string for embedding.
        """
        tokens = self._extract_query_keywords(query)
        expanded: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            expanded.append(token)
            for emotion, replacement in EMOTION_MAPPINGS.items():
                if emotion.startswith(token) or token in emotion:
                    for extra in replacement.split():
                        if extra not in seen:
                            seen.add(extra)
                            expanded.append(extra)

        return " ".join(expanded) if expanded else query

    # ------------------------------------------------------------------ #
    # Search execution                                                      #
    # ------------------------------------------------------------------ #

    async def _vector_search(
        self,
        *,
        query: str,
        limit: int,
        source_types: list[str],
    ) -> list[Any]:
        embedding = await get_embedding(query)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        return await self.repository.vector_search(
            self.db,
            embedding_str=embedding_str,
            limit=limit,
            source_types=source_types,
        )

    async def _text_search(
        self,
        *,
        query: str,
        limit: int,
        source_types: list[str],
    ) -> list[Any]:
        try:
            return await self.repository.text_search(
                self.db,
                query=query,
                limit=limit,
                source_types=source_types,
            )
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    # Hybrid RRF merge + graph re-rank                                      #
    # ------------------------------------------------------------------ #

    def _rrf_merge(
        self,
        *,
        vector_rows: list[Any],
        text_rows: list[Any],
        limit: int,
        text_weight: float = 1.0,
    ) -> list[Any]:
        """
        Reciprocal Rank Fusion of vector + text result lists.
        text_weight > 1.0 boosts exact-text matches (useful for short keyword queries).
        """
        scores: dict[int, float] = {}
        row_by_id: dict[int, Any] = {}

        for rank, row in enumerate(vector_rows):
            row_id = int(row[0])
            scores[row_id] = scores.get(row_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
            row_by_id[row_id] = row

        for rank, row in enumerate(text_rows):
            row_id = int(row[0])
            scores[row_id] = scores.get(row_id, 0.0) + text_weight / (_RRF_K + rank + 1)
            row_by_id.setdefault(row_id, row)

        sorted_ids = sorted(scores, key=lambda i: scores[i], reverse=True)
        return [row_by_id[i] for i in sorted_ids[:limit]]

    def _rerank_with_graph(self, rows: list[Any], graph_ids: list[int]) -> list[Any]:
        """Move graph-matched rows to the front, preserving graph priority order."""
        if not rows or not graph_ids:
            return rows

        graph_rank = {content_id: idx for idx, content_id in enumerate(graph_ids)}
        indexed = list(enumerate(rows))
        indexed.sort(
            key=lambda item: (
                0 if int(item[1][0]) in graph_rank else 1,
                graph_rank.get(int(item[1][0]), len(graph_rank)),
                item[0],
            )
        )
        return [row for _, row in indexed]

    # ------------------------------------------------------------------ #
    # Graph context                                                         #
    # ------------------------------------------------------------------ #

    async def _get_graph_context(
        self,
        *,
        original_query: str,
        resolved_query: str,
        mode: str,
    ) -> dict[str, Any]:
        keywords = self._extract_query_keywords(original_query)
        if not self._should_use_graph_search(mode=mode, keywords=keywords):
            return GraphContextService.empty()

        return await self.graph_context_service.get_context(
            user_text=resolved_query,
            keywords=keywords,
            top_k=6,
        )

    def _should_use_graph_search(self, *, mode: str, keywords: list[str]) -> bool:
        # Use graph for any multi-keyword query or RULE/SMART modes with at least one keyword
        if len(keywords) >= 2:
            return True
        if mode in {"RULE", "SMART"} and bool(keywords):
            return True
        # Single keyword: use graph when it's NOT a pure Islamic keyword
        # (Islamic keywords are well-served by vector search alone)
        return len(keywords) == 1 and keywords[0] not in ISLAMIC_KEYWORDS

    def _extract_query_keywords(self, query: str) -> list[str]:
        """Extract meaningful tokens, stripping noise/command words. Supports Turkish + Arabic script."""
        words = _TOKEN_RE.findall(query.lower())
        stop = NOISE_WORDS | COMMAND_STOP_WORDS
        keywords: list[str] = []
        seen: set[str] = set()
        for word in words:
            if len(word) < 2:
                continue
            if word in stop:
                continue
            if word in seen:
                continue
            seen.add(word)
            keywords.append(word)
        return keywords[:10]

    def _merge_graph_query(self, query: str, graph_context: dict[str, Any]) -> str:
        graph_terms = [
            *(graph_context.get("graph_keywords") or [])[:4],
            *(graph_context.get("graph_sub_categories") or [])[:2],
            *(graph_context.get("graph_root_categories") or [])[:1],
        ]
        merged_terms = self._dedupe_terms([query, *graph_terms])
        return " ".join(merged_terms).strip() or query

    def _dedupe_terms(self, terms: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for term in terms:
            cleaned = (term or "").strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
        return merged

    def _extract_graph_ids(self, graph_context: dict[str, Any]) -> list[int]:
        ids: list[int] = []
        seen: set[int] = set()
        for item in graph_context.get("graph_passages") or []:
            try:
                content_id = int(item.get("id"))
            except (TypeError, ValueError, AttributeError):
                continue
            if content_id in seen:
                continue
            seen.add(content_id)
            ids.append(content_id)
        return ids

    # ------------------------------------------------------------------ #
    # Result helpers                                                        #
    # ------------------------------------------------------------------ #

    def _merge_ranked_results(
        self,
        primary: list[ContentHit],
        secondary: list[ContentHit],
        *,
        limit: int,
    ) -> list[ContentHit]:
        merged: list[ContentHit] = []
        seen: set[int] = set()
        for item in [*primary, *secondary]:
            if item.id in seen:
                continue
            seen.add(item.id)
            merged.append(item)
            if len(merged) >= limit:
                break
        return merged

    def _map_row(self, row: Any, *, score_hint: str) -> ContentHit:
        metadata = row[4] if len(row) > 4 and row[4] is not None else {}
        return ContentHit(
            id=int(row[0]),
            source_type=row[1],
            content_text=row[2],
            explanation=row[3] or "",
            metadata=metadata or {},
            score_hint=score_hint,
        )
