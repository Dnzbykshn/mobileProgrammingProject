"""Pathway decision service.

Decides whether a new pathway should be created or an existing one should be
updated after a new prescription is generated.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import generate_content


class PathwayDecision(BaseModel):
    action: Literal["new_pathway", "update_pathway"]
    matching_pathway_id: Optional[str] = None
    reasoning: str
    confidence: float


class PathwayDecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decide(
        self,
        user_id: str,
        diagnosis: dict,
        active_pathways: List[dict],
    ) -> PathwayDecision:
        if not active_pathways:
            return PathwayDecision(
                action="new_pathway",
                reasoning="Kullanıcının aktif yolu yok.",
                confidence=1.0,
            )

        emotional_state = diagnosis.get("emotional_state", "")
        root_cause = diagnosis.get("root_cause", "")
        search_keywords = diagnosis.get("search_keywords", [])
        pathways_str = "\n".join(
            [
                f"- {item['pathway_id']}: {item['title']} | konu={item.get('topic_summary', 'Bilinmiyor')} | anahtar={item.get('topic_keywords', [])}"
                for item in active_pathways
            ]
        )

        prompt = f"""
        Kullanıcı için yeni bir yol mu açılmalı yoksa mevcut aktif yollardan biri mi güncellenmeli?

        YENİ TEŞHİS
        - Duygu: {emotional_state}
        - Kök neden: {root_cause}
        - Anahtar kelimeler: {search_keywords}

        AKTİF YOLLAR
        {pathways_str}

        KURALLAR
        - Aynı veya çok benzer konuysa: update_pathway
        - Farklı bir konuysa: new_pathway
        - Emin değilsen new_pathway seç
        - JSON dışında hiçbir şey yazma
        """

        try:
            response = await generate_content(prompt, response_schema=PathwayDecision)
            decision = PathwayDecision(**response.parsed.model_dump())
            if decision.confidence < 0.7:
                return PathwayDecision(
                    action="new_pathway",
                    reasoning=f"Güven düşük ({decision.confidence}). Yeni yol açılıyor.",
                    confidence=decision.confidence,
                )
            return decision
        except Exception:
            return PathwayDecision(
                action="new_pathway",
                reasoning="Karar servisi başarısız oldu; güvenli varsayılan olarak yeni yol açılıyor.",
                confidence=0.0,
            )
