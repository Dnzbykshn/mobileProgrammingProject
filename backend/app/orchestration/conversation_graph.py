from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.state import (
    GatheringDecision,
    IntentDecision,
    OngoingDecision,
    OrchestratorState,
)
from app.repositories.conversation_repository import conversation_history_to_text
from app.services.ai_service import generate_content
from app.orchestration.pathway_generation_graph import PathwayGenerationOrchestrator

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - runtime fallback for environments without langgraph
    END = "__end__"
    START = "__start__"
    StateGraph = None


class Diagnosis(BaseModel):
    emotional_state: str
    root_cause: str
    spiritual_needs: List[str]
    search_keywords: List[str]


class ConversationOrchestrator:
    CRISIS_IMMEDIATE = [
        "intihar", "kendimi öldürmek", "ölmek istiyorum", "hayatıma son",
        "yaşamak istemiyorum", "kendime zarar", "kendimi kesmek",
    ]
    CRISIS_HIGH = [
        "dayanamıyorum", "çaresizim", "umudum kalmadı", "hiçbir çıkış yok",
        "acı çekmek istemiyorum", "her şey anlamsız", "tükenişin eşiğindeyim",
    ]
    CRISIS_MODERATE = [
        "değersiz hissediyorum", "kimse beni sevmiyor", "çok yalnızım",
        "yaşamanın anlamı yok",
    ]
    EMERGENCY_CONTACTS = [
        {"service": "Acil Yardım", "number": "112"},
        {"service": "Psikolojik Destek", "number": "182"},
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self._compiled_graph = self._build_graph() if StateGraph else None

    async def process_turn(self, state: OrchestratorState) -> OrchestratorState:
        if self._compiled_graph is not None:
            return await self._compiled_graph.ainvoke(state)
        return await self._fallback_invoke(state)

    def _build_graph(self):
        graph = StateGraph(OrchestratorState)
        graph.add_node("guardrails", self.guardrails_node)
        graph.add_node("idle", self.idle_node)
        graph.add_node("gathering", self.gathering_node)
        graph.add_node("proposing", self.proposing_node)
        graph.add_node("ongoing", self.ongoing_node)
        graph.add_node("diagnosis_step", self.diagnosis_node)
        graph.add_node("pathway_step", self.pathway_node)
        graph.add_node("finalize", self.finalize_node)

        graph.add_edge(START, "guardrails")
        graph.add_conditional_edges(
            "guardrails",
            self._route_after_guardrails,
            {
                "idle": "idle",
                "gathering": "gathering",
                "proposing": "proposing",
                "ongoing": "ongoing",
                "finalize": "finalize",
            },
        )
        graph.add_conditional_edges(
            "idle",
            self._route_after_phase_node,
            {
                "finalize": "finalize",
                "diagnosis": "diagnosis_step",
            },
        )
        graph.add_conditional_edges(
            "gathering",
            self._route_after_phase_node,
            {
                "finalize": "finalize",
                "diagnosis": "diagnosis_step",
            },
        )
        graph.add_conditional_edges(
            "proposing",
            self._route_after_phase_node,
            {
                "finalize": "finalize",
                "diagnosis": "diagnosis_step",
            },
        )
        graph.add_conditional_edges(
            "ongoing",
            self._route_after_phase_node,
            {
                "finalize": "finalize",
                "diagnosis": "diagnosis_step",
            },
        )
        graph.add_conditional_edges(
            "diagnosis_step",
            self._route_after_diagnosis,
            {
                "pathway": "pathway_step",
                "finalize": "finalize",
            },
        )
        graph.add_edge("pathway_step", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    async def _fallback_invoke(self, state: OrchestratorState) -> OrchestratorState:
        state = {**state, **await self.guardrails_node(state)}
        route = self._route_after_guardrails(state)
        if route == "finalize":
            return {**state, **await self.finalize_node(state)}

        handler = {
            "idle": self.idle_node,
            "gathering": self.gathering_node,
            "proposing": self.proposing_node,
            "ongoing": self.ongoing_node,
        }[route]
        state = {**state, **await handler(state)}

        if self._route_after_phase_node(state) == "diagnosis":
            state = {**state, **await self.diagnosis_node(state)}
            if self._route_after_diagnosis(state) == "pathway":
                state = {**state, **await self.pathway_node(state)}

        return {**state, **await self.finalize_node(state)}

    async def guardrails_node(self, state: OrchestratorState) -> dict[str, Any]:
        lower = state["user_message"].lower().strip()
        for phrase in self.CRISIS_IMMEDIATE:
            if phrase in lower:
                return {
                    "guardrail_hit": True,
                    "intent": "CRISIS",
                    "response_text": (
                        "Şu anda çok zor bir durumdasın. Lütfen hemen profesyonel destek al. "
                        "Acil yardım için 112'yi, psikolojik destek için 182'yi ara."
                    ),
                    "new_phase": state["current_phase"],
                    "readiness_score": 0,
                    "crisis_level": "immediate",
                    "emergency_contacts": self.EMERGENCY_CONTACTS,
                }
        for phrase in self.CRISIS_HIGH:
            if phrase in lower:
                return {
                    "guardrail_hit": True,
                    "intent": "CRISIS",
                    "response_text": (
                        "Seni duyuyorum. Bu çok ağır geliyorsa lütfen yalnız kalma; 182 ya da 112'den destek iste. "
                        "İstersen ben de burada sakin kalmana yardımcı olmaya devam ederim."
                    ),
                    "new_phase": state["current_phase"],
                    "readiness_score": 0,
                    "crisis_level": "high",
                    "emergency_contacts": self.EMERGENCY_CONTACTS,
                }
        for phrase in self.CRISIS_MODERATE:
            if phrase in lower:
                return {
                    "guardrail_hit": False,
                    "crisis_level": "moderate",
                    "emergency_contacts": self.EMERGENCY_CONTACTS,
                }
        return {
            "guardrail_hit": False,
            "crisis_level": state.get("crisis_level"),
            "emergency_contacts": state.get("emergency_contacts", []),
        }

    async def idle_node(self, state: OrchestratorState) -> dict[str, Any]:
        prompt = f"""
        Kullanıcının mesajını sınıflandır.

        Mesaj: \"{state['user_message']}\"
        Kullanıcı profili: {state['user_context'].get('profile_str', 'Bilinmiyor')}
        Aktif yollar: {state['user_context'].get('pathways_str', 'Yok')}

        CHAT = selamlaşma, kısa konuşma, genel sıcak iletişim.
        SUPPORT = sıkıntı, yön arama, manevi destek ihtiyacı.

        response_text alanı:
        - CHAT ise kısa ve sıcak bir cevap yaz.
        - SUPPORT ise empatik giriş + kısa bir soru yaz.
        - JSON dışında hiçbir şey yazma.
        """
        try:
            decision = await generate_content(prompt, response_schema=IntentDecision)
            parsed = IntentDecision(**decision.parsed.model_dump())
        except Exception:
            lower = state["user_message"].lower().strip()
            greetings = {"merhaba", "selam", "selamünaleyküm", "selamun aleyküm", "hi", "hello"}
            if lower in greetings:
                parsed = IntentDecision(intent="CHAT", response_text="Selam, buradayım. Bugün nasılsın?")
            else:
                parsed = IntentDecision(intent="SUPPORT", response_text="Seni duyuyorum. Biraz daha anlatmak ister misin?")

        if parsed.intent == "CHAT":
            response_text = parsed.response_text
            if state["user_context"].get("active_pathways"):
                response_text = (
                    f"{parsed.response_text} "
                    f"Bu arada aktif yolunda nasıl gidiyor, bugün bir şeyleri tamamlayabildin mi?"
                ).strip()
                return {
                    "intent": "CHAT",
                    "response_text": response_text,
                    "new_phase": "ONGOING",
                    "readiness_score": 100,
                    "should_generate_pathway": False,
                }
            return {
                "intent": "CHAT",
                "response_text": response_text,
                "new_phase": "IDLE",
                "readiness_score": 0,
                "should_generate_pathway": False,
            }

        return {
            "intent": "GATHERING",
            "response_text": parsed.response_text,
            "new_phase": "GATHERING",
            "readiness_score": 15,
            "gathered_insight": state["user_message"],
            "should_generate_pathway": False,
        }

    async def gathering_node(self, state: OrchestratorState) -> dict[str, Any]:
        user_turn_count = len([item for item in state["history"] if item["sender"] == "user"])
        if max(user_turn_count - 1, 0) >= 6:
            return {
                "intent": "PROPOSING",
                "response_text": (
                    "Seni daha iyi anladım. İstersen sana küçük, uygulanabilir ve takip edilebilir bir yol önerebilirim. "
                    "Hazırsan birlikte başlayalım mı?"
                ),
                "new_phase": "PROPOSING",
                "readiness_score": 90,
                "proposal_summary": "Sana günlük küçük adımlarla ilerleyen bir manevi yol önerebilirim.",
                "should_generate_pathway": False,
                "gathered_insight": state["user_message"],
            }

        prompt = f"""
        Sen şefkatli ama sade bir manevi destek asistanısın.

        SON MESAJ: {state['user_message']}
        SOHBET GEÇMİŞİ: {state['history'][-6:]}
        KULLANICI BAĞLAMI: {state['user_context']}

        Görev:
        1. Kısa bir empati kur.
        2. Tek bir net takip sorusu sor.
        3. readiness_score ver (0-10).
        4. gathered_insight alanına tek cümle çıkarım yaz.
        5. readiness_score >= 7 ise kısa proposal_summary yaz.

        JSON dışında hiçbir şey yazma.
        """
        try:
            decision = await generate_content(prompt, response_schema=GatheringDecision)
            parsed = GatheringDecision(**decision.parsed.model_dump())
        except Exception:
            parsed = GatheringDecision(
                response_text="Seni daha iyi anlayabilmem için biraz daha açar mısın? Bu durum en çok hangi anlarda ağırlaşıyor?",
                readiness_score=5,
                gathered_insight=state["user_message"],
                proposal_summary="",
            )
        readiness_pct = min(parsed.readiness_score * 10, 100)
        enough_turns = user_turn_count >= 4
        if parsed.readiness_score >= 7 and enough_turns:
            return {
                "intent": "PROPOSING",
                "response_text": parsed.response_text,
                "new_phase": "PROPOSING",
                "readiness_score": readiness_pct,
                "proposal_summary": parsed.proposal_summary or "Sana takip edilebilir bir yol önerebilirim.",
                "gathered_insight": parsed.gathered_insight,
                "should_generate_pathway": False,
            }
        return {
            "intent": "GATHERING",
            "response_text": parsed.response_text,
            "new_phase": "GATHERING",
            "readiness_score": max(readiness_pct, min(user_turn_count * 15, 60)),
            "gathered_insight": parsed.gathered_insight,
            "proposal_summary": parsed.proposal_summary,
            "should_generate_pathway": False,
        }

    async def proposing_node(self, state: OrchestratorState) -> dict[str, Any]:
        lower = state["user_message"].lower().strip()

        continue_keywords = [
            "konuşalım", "biraz daha", "devam edelim", "hazır değilim", "emin değilim", "daha erken",
        ]
        if any(keyword in lower for keyword in continue_keywords):
            return {
                "intent": "GATHERING",
                "response_text": "Elbette, biraz daha konuşalım. Şu an en çok neresi zor geliyor?",
                "new_phase": "GATHERING",
                "readiness_score": 70,
                "should_generate_pathway": False,
            }

        accept_keywords = [
            "evet", "tamam", "başlayalım", "kabul", "olur", "hazırım",
            "haydi", "hadi", "istiyorum", "başla", "oluştur", "yapalım",
            "tabii", "tabi", "süper", "harika",
        ]
        if any(keyword in lower for keyword in accept_keywords):
            return {
                "intent": "READY",
                "response_text": "Tamam, senin için sade ve takip edilebilir bir yol hazırlıyorum.",
                "new_phase": "READY",
                "readiness_score": 100,
                "should_generate_pathway": True,
            }

        return {
            "intent": "GATHERING",
            "response_text": "Elbette, biraz daha konuşalım. Şu an en çok neresi zor geliyor?",
            "new_phase": "GATHERING",
            "readiness_score": 70,
            "should_generate_pathway": False,
        }

    async def ongoing_node(self, state: OrchestratorState) -> dict[str, Any]:
        prompt = f"""
        Kullanıcıyla süren bir destek sohbetini değerlendir.

        SON MESAJ: {state['user_message']}
        SOHBET: {state['history'][-8:]}
        AKTİF YOLLAR: {state['user_context'].get('pathways_str', 'Yok')}

        ÇIKTI:
        - response_type: pathway_feedback | new_topic | general_chat
        - response_text: kısa Türkçe yanıt
        - should_update_pathway: true/false
        """
        try:
            decision = await generate_content(prompt, response_schema=OngoingDecision)
            parsed = OngoingDecision(**decision.parsed.model_dump())
        except Exception:
            parsed = OngoingDecision(
                response_type="general_chat",
                response_text="Anladım. İstersen buradan devam edelim; dilersen mevcut yolunu da birlikte gözden geçirebiliriz.",
                should_update_pathway=False,
            )

        if parsed.response_type == "new_topic":
            return {
                "intent": "GATHERING",
                "response_text": parsed.response_text,
                "new_phase": "GATHERING",
                "readiness_score": 20,
                "should_generate_pathway": False,
            }
        if parsed.response_type == "pathway_feedback" and parsed.should_update_pathway:
            return {
                "intent": "READY",
                "response_text": parsed.response_text,
                "new_phase": "READY",
                "readiness_score": 100,
                "should_generate_pathway": True,
            }
        return {
            "intent": "CHAT",
            "response_text": parsed.response_text,
            "new_phase": "ONGOING",
            "readiness_score": 100,
            "should_generate_pathway": False,
        }

    async def diagnosis_node(self, state: OrchestratorState) -> dict[str, Any]:
        history_text = conversation_history_to_text(state["history"])
        prompt = f"""
        Sen uzman bir manevi danışmanlık sistemisin.
        Kullanıcıyla geçen konuşmayı analiz et ve kısa ama net bir teşhis çıkar.

        KONUŞMA:
        {history_text}

        ÇIKTI KURALLARI:
        - emotional_state: birincil duygu (Türkçe)
        - root_cause: kısa ama anlamlı kök sebep özeti (Türkçe)
        - spiritual_needs: en fazla 3 manevi ihtiyaç (Türkçe)
        - search_keywords: ayet ve içerik aramak için 3 ila 5 anahtar kelime

        KRİTİK:
        - Sorunu değil, şifayı aratacak kelimeler üret.
        - Örn. boşanma -> merhamet, teselli, sabır
        - JSON dışında hiçbir şey yazma.
        """
        try:
            response = await generate_content(prompt, response_schema=Diagnosis)
            diagnosis = Diagnosis(**response.parsed.model_dump())
            return {"diagnosis": diagnosis.model_dump()}
        except Exception:
            return {
                "diagnosis": {
                    "emotional_state": "Genel",
                    "root_cause": "Manevi destek arayışı",
                    "spiritual_needs": ["huzur", "güven", "sabır"],
                    "search_keywords": ["huzur", "teselli", "sabır"],
                }
            }

    async def pathway_node(self, state: OrchestratorState) -> dict[str, Any]:
        if not state.get("diagnosis"):
            return {
                "pathway_action": None,
                "pathway_id": None,
            }

        if not state.get("user_id"):
            return {
                "pathway_action": "authentication_required",
                "pathway_id": None,
                "response_text": (
                    "Senin için bir yol hazırladım. Takip edebilmem ve kaydedebilmem için giriş yapman gerekiyor."
                ),
                "new_phase": "GENERATED",
            }

        generation = PathwayGenerationOrchestrator(self.db)
        return await generation.generate(
            {
                "user_id": state["user_id"],
                "conversation_id": state["conversation_id"],
                "history": state["history"],
                "diagnosis": state["diagnosis"],
            }
        )

    async def finalize_node(self, state: OrchestratorState) -> dict[str, Any]:
        return {
            "new_phase": state.get("new_phase", state["current_phase"]),
            "response_text": state.get("response_text", "Seni dinliyorum."),
            "intent": state.get("intent", "CHAT"),
            "readiness_score": state.get("readiness_score", 0),
            "proposal_summary": state.get("proposal_summary", ""),
            "pathway_action": state.get("pathway_action"),
            "pathway_id": state.get("pathway_id"),
            "crisis_level": state.get("crisis_level"),
            "emergency_contacts": state.get("emergency_contacts", []),
        }

    def _route_after_guardrails(self, state: OrchestratorState) -> str:
        if state.get("guardrail_hit"):
            return "finalize"

        phase = state["current_phase"]
        if phase in (None, "", "IDLE"):
            return "idle"
        if phase == "GATHERING":
            return "gathering"
        if phase == "PROPOSING":
            return "proposing"
        return "ongoing"

    def _route_after_phase_node(self, state: OrchestratorState) -> str:
        return "diagnosis" if state.get("should_generate_pathway") else "finalize"

    def _route_after_diagnosis(self, state: OrchestratorState) -> str:
        return "pathway" if state.get("diagnosis") else "finalize"
