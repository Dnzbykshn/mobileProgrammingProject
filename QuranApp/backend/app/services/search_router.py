"""
SearchRouter - Single-tier vector search service.
Now relies 100% on PgVector (semantic search) which is sufficient for "Manevi Rehber" context.

Tiers (Simplified):
  1. SIMPLE: Short/Islamic terms → direct vector search
  2. RULE: Modern words → cleaned vector search
  3. SMART: Complex queries → LLM transformation + vector search
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional

from app.core.config import settings
from app.services.ai_service import get_embedding, generate_content_sync

# --- CONSTANTS ---
ISLAMIC_KEYWORDS = {
    "allah", "kuran", "quran", "ayet", "sure", "hadis", "namaz", "dua",
    "oruç", "zekat", "hac", "peygamber", "muhammed", "iman", "islam",
    "cennet", "cehennem", "melek", "şeytan", "tevbe", "sabır", "şükür",
    "tevekkül", "ihlas", "rahman", "rahim", "esma", "zikir",
}

MODERN_STOP_WORDS = [
    "bana", "beni", "benim", "bir", "için", "nasıl", "nedir", "hakkında",
    "istiyorum", "oku", "söyle", "ver", "lazım",
]

EMOTION_MAPPINGS = {
    "korkuyorum": "korku güven tevekkül",
    "üzgünüm": "hüzün teselli rahmet",
    "kızgınım": "öfke sabır hilm",
    "bunaldım": "sıkıntı ferahlık inşirah",
    "daraldım": "darlık genişlik ferahlık",
    "endişeleniyorum": "endişe huzur sekinet",
    "yalnızım": "yalnızlık yakınlık üns",
}


class SearchRouter:
    def __init__(self):
        pass

    def classify_query(self, query: str) -> str:
        """Route query to one of 3 tiers."""
        query_lower = query.lower()
        words = query_lower.split()

        if len(words) < 5:
            return "SIMPLE"
        if any(w in ISLAMIC_KEYWORDS for w in words):
            return "SIMPLE"
        if any(stop in query_lower for stop in MODERN_STOP_WORDS):
            return "RULE"
        if any(emo in query_lower for emo in EMOTION_MAPPINGS):
            return "RULE"
        return "SMART"

    async def vector_search(self, db: AsyncSession, query: str, limit: int = 3):
        """PgVector cosine search."""
        embedding = await get_embedding(query)
        sql = text("""
            SELECT metadata, content_text, explanation
            FROM knowledge_units
            ORDER BY embedding <=> :emb::vector
            LIMIT :lim
        """)
        result = await db.execute(sql, {"emb": str(embedding), "lim": limit})
        return [
            {
                "content_text": row[1],
                "explanation": row[2],
                "metadata": row[0] if isinstance(row[0], dict) else json.loads(row[0] or "{}"),
            }
            for row in result.fetchall()
        ]

    def _clean_query(self, query: str) -> str:
        """Remove modern stop words, map emotions."""
        cleaned = query.lower()
        for stop in MODERN_STOP_WORDS:
            cleaned = cleaned.replace(stop, "")
        for emotion, mapping in EMOTION_MAPPINGS.items():
            if emotion in cleaned:
                cleaned = cleaned.replace(emotion, mapping)
        return " ".join(cleaned.split())

    async def transform_query(self, query: str) -> str:
        """Use Gemini to transform complex query into Islamic search terms."""
        prompt = f"""
        Transform this Turkish user query into optimal Islamic search terms.
        
        User Query: "{query}"
        
        Rules:
        - Output 3-5 Turkish keywords relevant to Quran/Hadith/Esma
        - Include both the literal topic AND spiritual concepts
        - Output ONLY the keywords separated by spaces, nothing else
        """
        response = await asyncio.to_thread(generate_content_sync, prompt)
        return response.text.strip()

    async def run(
        self,
        query: str,
        db: AsyncSession,
        force_mode: Optional[str] = None,
    ) -> List[dict]:
        """Main entry point — classify and execute search strategy."""
        mode = force_mode or self.classify_query(query)
        print(f"🔍 Search Mode: {mode} | Query: {query}")

        if mode == "SIMPLE":
            # Just vector search (PgVector)
            return await self.vector_search(db, query, limit=3)

        elif mode == "RULE":
            cleaned = self._clean_query(query)
            return await self.vector_search(db, cleaned, limit=3)

        elif mode == "SMART":
            transformed = await self.transform_query(query)
            return await self.vector_search(db, transformed, limit=3)

        return []
