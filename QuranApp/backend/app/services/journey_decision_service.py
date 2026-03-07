"""
Journey Decision Service — AI-driven decision: new journey vs update existing.
"""
import json
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import generate_content


class JourneyDecision(BaseModel):
    action: str  # "new_journey" | "update_journey"
    matching_plan_id: Optional[str] = None
    reasoning: str
    confidence: float  # 0.0-1.0


class JourneyDecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decide(
        self,
        user_id: str,
        diagnosis: dict,
        active_journeys: List[dict],
    ) -> JourneyDecision:
        """
        AI decides: create new journey or update an existing one.

        Decision criteria:
        - Compare diagnosis emotional_state + root_cause with each active journey's topic_summary and topic_keywords
        - If >70% semantic overlap with an active journey -> update
        - Otherwise -> new journey
        """
        if not active_journeys:
            return JourneyDecision(
                action="new_journey",
                reasoning="Kullanıcının aktif yolculuğu yok.",
                confidence=1.0,
            )

        # Build prompt for AI decision
        emotional_state = diagnosis.get("emotional_state", "")
        root_cause = diagnosis.get("root_cause", "")
        search_keywords = diagnosis.get("search_keywords", [])

        journeys_str = "\n".join([
            f"- {j['plan_id']}: \"{j['title']}\" (Konu: {j.get('topic_summary', 'Bilinmiyor')}, Anahtar kelimeler: {j.get('topic_keywords', [])})"
            for j in active_journeys
        ])

        prompt = f"""
        Sen manevi yolculuk yöneticisisin. Kullanıcı yeni bir sohbet başlattı ve rutin hazırlandı.

        YENİ TEŞHİS:
        - Duygu: {emotional_state}
        - Kök Neden: {root_cause}
        - Anahtar Kelimeler: {search_keywords}

        AKTİF YOLCULUKLAR:
        {journeys_str}

        KARAR VER:
        1. Eğer yeni teşhis, mevcut bir yolculuğun konusuyla AYNI veya ÇOK BENZERse -> "update_journey" + matching_plan_id
           Örnekler:
           - "iş stresi" ve "iş baskısı" = AYNI (güncelle)
           - "Evlilik" ve "eş ile iletişim" = AYNI (güncelle)
           - "Kaygı" ve "korku" = BENZER (güncelle)

        2. Eğer yeni teşhis, mevcut yolculuklardan FARKLI bir konuysa -> "new_journey"
           Örnekler:
           - "iş stresi" ve "çocuk kaybı" = FARKLI (yeni)
           - "Kaygı" ve "öfke kontrolü" = FARKLI (yeni)

        ÇIKTI (JSON):
        {{
            "action": "new_journey" veya "update_journey",
            "matching_plan_id": "plan ID" (sadece update_journey ise),
            "reasoning": "Kararın açıklaması",
            "confidence": 0.0-1.0 (emin olma derecesi)
        }}
        """

        try:
            response = await generate_content(prompt)
            raw = response.text.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            data = json.loads(raw)
            decision = JourneyDecision(
                action=data.get("action", "new_journey"),
                matching_plan_id=data.get("matching_plan_id"),
                reasoning=data.get("reasoning", "AI karar verdi"),
                confidence=float(data.get("confidence", 0.5)),
            )

            # Safety: if confidence < 0.7, default to new_journey
            if decision.confidence < 0.7:
                return JourneyDecision(
                    action="new_journey",
                    reasoning=f"Güven düşük ({decision.confidence}), yeni yolculuk oluşturuluyor.",
                    confidence=decision.confidence,
                )

            return decision

        except Exception as e:
            print(f"⚠️ Journey decision AI failed ({e}), defaulting to new_journey")
            return JourneyDecision(
                action="new_journey",
                reasoning="AI karar veremedi, yeni yolculuk oluşturuluyor.",
                confidence=0.0,
            )
