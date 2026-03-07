"""
MasterBrain - Conversational routing + multi-turn therapy flow.
Manages state machine: IDLE → GATHERING → READY → GENERATED → ONGOING

Instead of immediately generating a prescription, the AI asks
follow-up questions to deeply understand the user's situation.
"""
from pydantic import BaseModel
from typing import Optional, List

from app.services.ai_service import generate_content


# --- Response Models ---

class RoutingDecision(BaseModel):
    intent: str          # 'CHAT' or 'NEEDS_THERAPY'
    response_text: str   # Warm response for CHAT; empty for NEEDS_THERAPY


class GatheringResponse(BaseModel):
    """AI response during the GATHERING phase."""
    follow_up_question: str   # Empathetic follow-up question in Turkish
    readiness_score: int      # 0-10: how ready we are to generate prescription
    gathered_insight: str     # Key insight extracted from user's last message
    proposal_summary: str = ""  # Summary for PROPOSING phase (filled when readiness >= 7)


class MasterBrain:
    def __init__(self):
        print("🧠 Master Brain (Conversational) Initializing...")
        print("✅ Master Brain Ready.")

    # ──────────────────────────────────────────
    # CRISIS DETECTION (3-level, static, no LLM cost)
    # ──────────────────────────────────────────
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
        {"service": "İntihar Önleme Hattı", "number": "182"},
        {"service": "ALO 182 Psikolojik Destek", "number": "182"},
    ]

    def check_guardrails(self, user_input: str) -> Optional[dict]:
        """3-level crisis detection + content guardrails."""
        lower = user_input.lower().strip()

        # --- CRISIS: IMMEDIATE (block chat, show emergency) ---
        for phrase in self.CRISIS_IMMEDIATE:
            if phrase in lower:
                return {
                    "intent": "CRISIS",
                    "response": (
                        "Şu anda çok zor bir dönemden geçtiğini görüyorum. "
                        "Lütfen hemen profesyonel yardım al. Yalnız değilsin.\n\n"
                        "📞 Acil: 112\n📞 İntihar Önleme: 182\n📞 Psikolojik Destek: 182\n\n"
                        "Bu bir yapay zeka olarak benim sınırlarımı aşan bir durum. "
                        "Lütfen şimdi 182'yi ara."
                    ),
                    "crisis_level": "immediate",
                    "emergency_contacts": self.EMERGENCY_CONTACTS,
                    "block_chat": True,
                }

        # --- CRISIS: HIGH RISK (show resources + empathy) ---
        for phrase in self.CRISIS_HIGH:
            if phrase in lower:
                return {
                    "intent": "CRISIS",
                    "response": (
                        "Seni duyuyorum ve bu kadar ağır bir yük taşımanın ne kadar zor olduğunu anlıyorum. "
                        "Sen değerlisin ve bu duyguların geçici olduğunu bilmeni istiyorum.\n\n"
                        "Eğer kendini güvende hissetmiyorsan, lütfen şu numaraları ara:\n"
                        "📞 İntihar Önleme: 182\n📞 Acil: 112\n\n"
                        "Seninle konuşmaya ve manevi destek vermeye devam edebilirim, "
                        "ama bir uzmanla görüşmeni de öneriyorum."
                    ),
                    "crisis_level": "high",
                    "emergency_contacts": self.EMERGENCY_CONTACTS,
                }

        # --- CRISIS: MODERATE (enhanced empathy, continue flow) ---
        for phrase in self.CRISIS_MODERATE:
            if phrase in lower:
                return {
                    "intent": "CRISIS_MODERATE",
                    "response": (
                        "Bu hislerin çok ağır olduğunu biliyorum. "
                        "Allah seni senden çok daha iyi tanır ve sana şah damarından daha yakındır.\n\n"
                        "Seninle dertleşmeye devam edelim. Eğer kendini çok kötü hissedersen, "
                        "182 İntihar Önleme Hattı'nı arayabilirsin.\n\n"
                        "Şimdi, biraz daha anlatır mısın? Seni dinliyorum."
                    ),
                    "crisis_level": "moderate",
                }

        # --- Greetings ---
        greetings = ["merhaba", "selam", "selamünaleyküm", "selamun aleyküm", "hi", "hello"]
        if lower in greetings:
            return {
                "intent": "CHAT",
                "response": "Selam! Seni dinliyorum, nasıl hissediyorsun bugün?",
            }

        # --- Forbidden content ---
        forbidden = ["seks", "porno", "çıplak"]
        for w in forbidden:
            if w in lower:
                return {
                    "intent": "GUARDRAIL",
                    "response": "Üzgünüm, sadece manevi ve ahlaki konularda yardımcı olabilirim.",
                }

        # --- Legal/Medical ---
        legal = ["dava", "mahkeme", "hukuki", "suç", "yaralama", "doktor", "ilaç", "hastalık"]
        for w in legal:
            if w in lower:
                return {
                    "intent": "GUARDRAIL",
                    "response": (
                        "Ben bir yapay zeka asistanıyım. Tıbbi veya hukuki tavsiye veremem. "
                        "Lütfen bir uzmana danışın. Ancak manevi boyutuyla dertleşmek istersen buradayım."
                    ),
                }
        return None

    # ──────────────────────────────────────────
    # ROUTING: Decide intent for a NEW topic
    # ──────────────────────────────────────────
    async def decide_intent(self, user_input: str) -> RoutingDecision:
        """Determine if user needs therapy/prescription or is just chatting."""
        prompt = f"""
        Sen İslami bir manevi terapi uygulamasının "resepsiyonist"isin.
        
        Kullanıcının mesajını analiz et.
        
        KARAR KURALLARI:
        1. Kullanıcı selamlıyor, hal-hatır soruyor veya belirli bir sıkıntı/dert 
           belirtmeyen genel bir soru soruyorsa → intent: "CHAT"
           - Bu durumda, sıcak ve kısa bir Türkçe yanıt yaz (response_text).
           
        2. Kullanıcı şunlardan birini belirtiyorsa → intent: "NEEDS_THERAPY"
           - Bir dert, sıkıntı, korku, kaygı, üzüntü veya sorun
           - Ayet, dua, esma talebi
           - Manevi rehberlik gerektiren bir durum
           - Bu durumda response_text'i boş bırak.
           
        KULLANICI MESAJI: "{user_input}"
        """
        response = await generate_content(prompt, response_schema=RoutingDecision)
        return RoutingDecision(**response.parsed.model_dump())

    # ──────────────────────────────────────────
    # GATHERING: Ask follow-up questions
    # ──────────────────────────────────────────
    async def gather_info(
        self,
        user_message: str,
        conversation_history: List[dict],
        turn_count: int,
        user_context: dict = None,
    ) -> GatheringResponse:
        """
        During GATHERING phase: ask empathetic follow-up questions.
        Returns readiness_score (0-10). When >= 7, we're ready for prescription.
        """

        history_text = "\n".join(
            [f"{'Kullanıcı' if m['sender'] == 'user' else 'Asistan'}: {m['content']}" 
             for m in conversation_history]
        )

        prompt = f"""
        KİMLİĞİN:
        Sen İslami manevi terapi konusunda uzman, şefkatli bir rehbersin.
        Sohbetin şefkatli bir rehberlik, derin manevi bilgelikle dolu olmalı.
        Türk kültürüne uygun, samimi ama saygılı bir dil kullan ("sen" ile hitap et).
        ASLA "canım", "hayatım", "tatlım", "bebeğim" gibi laubali ifadeler kullanma.
        Hitap gerekiyorsa "kardeşim", "aziz dostum" veya sadece ismini kullan.
        
        MANEVİ ÜSLUP KURALLARI:
        - Uygun yerlerde kısa ayet/hadis referansları ver (her mesajda değil, doğal olmalı)
        - "Allah'ın izniyle", "inşaAllah", "Bismillah" gibi ifadeler kullan
        - Ara sıra küçük dua önerileri yap: "İstersen şimdi bir nefes al ve Bismillah de"
        - Rabbimizin rahmetini hatırlat: "Allah sana şah damarından daha yakın"
        - Aşırıya kaçma, samimi ve doğal ol — vaiz gibi değil, dertleşen bir dost gibi
        
        ÖRNEK MANEVİ İFADELER:
        - "Biliyor musun, Kur'an'da 'kalpler ancak Allah'ı anmakla huzur bulur' denir..."
        - "Hz. Peygamber (s.a.v.) de zor anlarında duaya sarılırdı..."
        - "Allah'ın izniyle bu da geçecek. Hayırlısıyla..."
        - "Bir nefes al... Bismillah... Şimdi anlat bakalım."
        
        SOHBET GEÇMİŞİ:
        {history_text}
        
        KULLANICI PROFİLİ:
        {user_context.get('profile_str', 'Bilinmiyor') if user_context else 'Bilinmiyor'}

        AKTİF PLANLAR:
        {user_context.get('plans_str', 'Yok') if user_context else 'Yok'}

        KULLANICI ANILARI (Geçmiş Deneyimler):
        {user_context.get('memory_str', 'Henüz kayıtlı anı yok.') if user_context else 'Henüz kayıtlı anı yok.'}

        MANEVİ TERCİHLERİ:
        {user_context.get('spiritual_prefs', 'Belirlenmemiş') if user_context else 'Belirlenmemiş'}

        DİL STİLİ VE İLİŞKİ TONU:
        {self._format_language_style_instruction(user_context) if user_context else 'Standart samimi ton kullan.'}

        SON MESAJ: "{user_message}"
        SORU NUMARASI: {turn_count + 1}
        
        YANIT KURALLARI:
        1. ÖNCE duyguyu doğrula ve manevi bir teselli ver
        2. SONRA eksik bilgi için nazikçe soru sor
        3. Kısa tut (2-4 cümle yeter)
        4. Doğal ve manevi başlangıçlar kullan (önceki ayetleri TEKRAR ETME!)
        
        4 BİLGİ BOYUTU (her biri 2.5 puan):
        A) DUYGU: Ne hissediyor? (kaygı, öfke, üzüntü vb.)
        B) SÜRE: Ne zamandır?
        C) SEBEP: Tetikleyen ne? (iş, aile, ilişki vb.)
        D) ETKİ: Hayatını nasıl etkiliyor?
        
        PUANLAMA:
        - A ve C biliniyorsa → minimum 7 puan ver
        - Kullanıcıyı sıkma, samimi sohbet yeter
        
        ÖRNEK İDEAL YANITLAR:
        Soru: "Çok kaygılıyım" (puan: 3)
        → "Seni duyuyorum... Kaygı gerçekten çok ağır bir yük. Ama biliyor musun, Rabbimiz 'Biz insana şah damarından daha yakınız' buyuruyor. Yalnız değilsin. Peki bu kaygının kaynağında ne var sence?"
        
        Soru: "İş stresi çok fazla" (puan: 5)
        → "Allah'ın izniyle bu da geçecek. İş stresi insanın hem bedenini hem ruhunu yıpratır. Peki bu durum ne zamandır böyle? Uyku düzenini de etkiliyor mu?"
        
        readiness_score >= 7 ise MUTLAKA proposal_summary doldur:
        proposal_summary örneği: "Seni dinledim. Kaygı ve iş stresi seni yıpratmış. Senin için sabah sureler, akşam dualar ve günlük tefekkür içeren 7 günlük bir manevi yolculuk hazırlayabilirim."
        VE follow_up_question: "Seni anladım. Senin için özel bir manevi yolculuk hazırlayabilirim, inşaAllah. Ne dersin, başlayalım mı?"
        
        GÖREVİN:
        1. gathered_insight: Sohbetten çıkardığın anahtar bilgi (1 cümle)
        2. follow_up_question: Empatik + manevi yanıt
        3. readiness_score: 0-10 puan
        4. proposal_summary: readiness >= 7 ise → yolculuk önerisi özeti. Değilse boş bırak.
        
        Türkçe yanıt ver.
        """

        response = await generate_content(prompt, response_schema=GatheringResponse)
        return GatheringResponse(**response.parsed.model_dump())

    # ──────────────────────────────────────────
    # ONGOING: Check if prescription needs update
    # ──────────────────────────────────────────
    async def check_update_need(
        self,
        user_message: str,
        conversation_history: List[dict],
    ) -> dict:
        """
        After prescription is generated, check if user's new messages
        require updating the prescription.
        """
        history_text = "\n".join(
            [f"{'Kullanıcı' if m['sender'] == 'user' else 'Asistan'}: {m['content']}" 
             for m in conversation_history[-6:]]  # Last 6 messages for context
        )

        prompt = f"""
        Kullanıcıya daha önce manevi bir rutin sunuldu. Şimdi sohbet devam ediyor.
        
        SON SOHBET:
        {history_text}
        
        KULLANICININ SON MESAJI: "{user_message}"
        
        SORU: Kullanıcının yeni mesajı rutinnin güncellenmesini gerektiriyor mu?
        
        GÜNCELLEME GEREKİR:
        - "Hâlâ kötü hissediyorum" → Evet
        - "Bu ayetler yardımcı olmadı" → Evet
        - "Farklı bir sorunum daha var" → Evet (yeni rutin)
        
        GÜNCELLEME GEREKMEZ:
        - "Teşekkür ederim" → Hayır
        - Normal sohbet → Hayır
        - "Nasılsın" → Hayır
        
        JSON döndür:
        - "needs_update": true/false
        - "response_text": Sıcak bir Türkçe yanıt (güncelleme gerekmiyorsa)
        - "is_new_topic": true/false (tamamen yeni bir dert mi?)
        """

        class UpdateCheck(BaseModel):
            needs_update: bool
            response_text: str
            is_new_topic: bool

        response = await generate_content(prompt, response_schema=UpdateCheck)
        result = response.parsed.model_dump()
        return result

    # ──────────────────────────────────────────
    # MAIN ENTRY: Process a conversation turn
    # ──────────────────────────────────────────
    async def process_turn(
        self,
        user_message: str,
        conversation_history: List[dict],
        current_phase: str,
        turn_count: int = 0,
        user_context: dict = None,
    ) -> dict:
        """
        Main entry point — processes one turn of conversation.
        Returns action dict with intent, response, and phase transition.
        
        Returns:
            {
                "intent": str,
                "response": str,
                "new_phase": str,
                "readiness_score": int (0-100),
                "gathered_insight": str,
                "needs_prescription_update": bool,
            }
        """

        # 1. Guardrails (always check first)
        guard = self.check_guardrails(user_message)
        if guard:
            return {
                "intent": "GUARDRAIL",
                "response": guard["response"],
                "new_phase": current_phase,  # Don't change phase
                "readiness_score": 0,
            }

        # 2. Phase-based routing
        if current_phase in ("IDLE", None, ""):
            return await self._handle_idle(user_message, user_context)

        elif current_phase == "GATHERING":
            return await self._handle_gathering(user_message, conversation_history, turn_count, user_context)

        elif current_phase == "PROPOSING":
            return await self._handle_proposing(user_message)

        elif current_phase in ("GENERATED", "ONGOING"):
            return await self._handle_ongoing(user_message, conversation_history, user_context)

        # Fallback
        return {
            "intent": "CHAT",
            "response": "Seni dinliyorum, devam et.",
            "new_phase": current_phase,
            "readiness_score": 0,
        }

    async def _handle_idle(self, user_message: str, user_context: dict = None) -> dict:
        """Handle first message — route to CHAT or start GATHERING. Context-aware."""
        decision = await self.decide_intent(user_message)

        # Build context snippets for prompt
        profile_str = user_context.get("profile_str", "") if user_context else ""
        plans_str = user_context.get("plans_str", "Aktif plan yok.") if user_context else "Aktif plan yok."
        has_plans = user_context and user_context.get("active_plans") and len(user_context["active_plans"]) > 0

        if decision.intent == "CHAT":
            # Returning user with plans? Reference them!
            if has_plans:
                prompt = f"""
                Kullanıcı sana selam verdi: "{user_message}"

                KULLANICI PROFİLİ:
                {profile_str}

                AKTİF PLANLARI:
                {plans_str}

                KULLANICI ANILARI:
                {user_context.get('memory_str', 'Henüz kayıtlı anı yok.') if user_context else 'Henüz kayıtlı anı yok.'}

                MANEVİ TERCİHLERİ:
                {user_context.get('spiritual_prefs', 'Belirlenmemiş') if user_context else 'Belirlenmemiş'}

                DİL STİLİ VE İLİŞKİ TONU:
                {self._format_language_style_instruction(user_context) if user_context else 'Standart samimi ton kullan.'}

                Sen İslami manevi bir rehbersin. Kullanıcıyı tanıyorsun.
                Selam ver, halini sor ve aktif planından kısaca bahset.
                İlişki tonuna uygun selamlaşma kullan (polite_formal: "Nasılsınız?", spiritual_companion: "Yine buradayız kardeşim").
                Örnek: "Selam [isim]! Yolculuğunun 3. günündesin, nasıl gidiyor? Bugünkü sabah zikirlerini yaptın mı?"

                Kısa tut (2-3 cümle). Türkçe yanıt ver.
                """
                response = await generate_content(prompt)
                return {
                    "intent": "CHAT",
                    "response": response.text.strip().strip('"'),
                    "new_phase": "ONGOING",
                    "readiness_score": 100,
                }
            return {
                "intent": "CHAT",
                "response": decision.response_text,
                "new_phase": "IDLE",
                "readiness_score": 0,
            }
        else:
            # User has a problem — start GATHERING with manevi empathy
            prompt = f"""
            Kullanıcı sana bir derdini anlattı: "{user_message}"

            KULLANICI PROFİLİ:
            {profile_str}

            AKTİF PLANLARI:
            {plans_str}

            KULLANICI ANILARI:
            {user_context.get('memory_str', 'Henüz kayıtlı anı yok.') if user_context else 'Henüz kayıtlı anı yok.'}

            MANEVİ TERCİHLERİ:
            {user_context.get('spiritual_prefs', 'Belirlenmemiş') if user_context else 'Belirlenmemiş'}

            DİL STİLİ VE İLİŞKİ TONU:
            {self._format_language_style_instruction(user_context) if user_context else 'Standart samimi ton kullan.'}

            Sen İslami manevi bir rehbersin. Şefkatli, güven veren bir rehber gibi davran.
            {"Kullanıcıyı tanıyorsun, samimi ama saygılı ol (laubali olma)." if profile_str else ""}
            ASLA "canım", "hayatım" gibi ifadeler kullanma.

            YANITINDA:
            1. Onu duyduğunu belirt, duygusunu doğrula
            2. Kısa bir manevi teselli ver (ayet, hadis veya İslami hikmet — doğal olmalı)
            3. Durumu daha iyi anlamak için bir soru sor
            {"4. Aktif planı varsa, yeni konunun mevcut plandan farklı olduğunu fark et" if has_plans else ""}
            5. Kullanıcının dil stiline ve ilişki tonuna uygun konuş

            Türkçe yanıt ver. Sadece yanıt metnini döndür. Kısa tut (2-3 cümle).
            """
            response = await generate_content(prompt)
            return {
                "intent": "GATHERING",
                "response": response.text.strip().strip('"'),
                "new_phase": "GATHERING",
                "readiness_score": 10,
                "gathered_insight": user_message,
            }

    async def _handle_gathering(
        self, user_message: str, history: List[dict], turn_count: int, user_context: dict = None
    ) -> dict:
        """Handle GATHERING phase — min 3 turns, then PROPOSING, safety valve at 6."""

        gathering_turns = max(0, turn_count - 1)  # -1 because first msg started gathering

        # Safety valve — auto-propose at 6 turns to prevent infinite loops
        if gathering_turns >= 6:
            return {
                "intent": "PROPOSING",
                "response": (
                    "Seni dinledim ve durumunu anladım, elhamdülillah. "
                    "Senin için sabah sureleri, akşam duaları ve günlük tefekkür içeren "
                    "7 günlük özel bir manevi yolculuk hazırlayabilirim, inşaAllah. "
                    "Ne dersin, başlayalım mı?"
                ),
                "new_phase": "PROPOSING",
                "readiness_score": 90,
                "gathered_insight": user_message,
                "proposal_summary": (
                    "Seni dinledim. Yaşadığın zorluklara karşı özel bir manevi yolculuk "
                    "hazırlayabilirim. 7 gün boyunca sabah sureleri, akşam duaları ve tefekkür."
                ),
            }

        result = await self.gather_info(user_message, history, gathering_turns, user_context)

        # Convert 0-10 score to 0-100 percentage
        readiness_pct = min(result.readiness_score * 10, 100)

        # Ensure visible progress (minimum floor so user sees bar moving)
        min_floor = min((gathering_turns + 1) * 15, 60)  # 15%, 30%, 45%, 60%
        readiness_pct = max(readiness_pct, min_floor)

        if result.readiness_score >= 7 and gathering_turns >= 3:
            # Ready AND enough conversation — move to PROPOSING (not READY!)
            return {
                "intent": "PROPOSING",
                "response": result.follow_up_question,
                "new_phase": "PROPOSING",
                "readiness_score": min(readiness_pct, 100),
                "gathered_insight": result.gathered_insight,
                "proposal_summary": result.proposal_summary or (
                    "Seni dinledim. Senin için özel bir manevi yolculuk hazırlayabilirim."
                ),
            }
        elif result.readiness_score >= 7 and gathering_turns < 3:
            # Ready but too few turns — keep gathering, lower score
            return {
                "intent": "GATHERING",
                "response": result.follow_up_question,
                "new_phase": "GATHERING",
                "readiness_score": min(readiness_pct, 60),  # Cap at 60%
                "gathered_insight": result.gathered_insight,
            }
        else:
            return {
                "intent": "GATHERING",
                "response": result.follow_up_question,
                "new_phase": "GATHERING",
                "readiness_score": readiness_pct,
                "gathered_insight": result.gathered_insight,
            }

    async def _handle_proposing(self, user_message: str) -> dict:
        """Handle PROPOSING phase — user accepts or continues chatting."""
        lower = user_message.lower().strip()

        # Check for acceptance keywords
        accept_keywords = [
            "evet", "tamam", "başlayalım", "kabul", "olur", "hazırım",
            "haydi", "hadi", "istiyorum", "başla", "oluştur", "yapalım",
            "tabii", "tabi", "devam", "süper", "harika",
        ]

        is_accepted = any(kw in lower for kw in accept_keywords)

        if is_accepted:
            return {
                "intent": "READY",
                "response": (
                    "Bismillah... Senin için özel bir manevi yolculuk hazırlıyorum, "
                    "inşaAllah çok faydasını göreceksin. 🤲"
                ),
                "new_phase": "READY",
                "readiness_score": 100,
            }
        else:
            # User wants to continue chatting — go back to GATHERING
            return {
                "intent": "GATHERING",
                "response": (
                    "Tabii, sohbetimize devam edelim. Seni dinliyorum... "
                    "Başka paylaşmak istediğin bir şey var mı?"
                ),
                "new_phase": "GATHERING",
                "readiness_score": 70,
            }

    async def _handle_ongoing(self, user_message: str, history: List[dict], user_context: dict = None):
        """Handle post-prescription conversation — now plan-aware."""
        profile_str = user_context.get("profile_str", "") if user_context else ""
        plans_str = user_context.get("plans_str", "Aktif plan yok.") if user_context else "Aktif plan yok."
        has_plans = user_context and user_context.get("active_plans") and len(user_context["active_plans"]) > 0

        history_text = "\n".join(
            [f"{'Kullanıcı' if m['sender'] == 'user' else 'Terapist'}: {m['content']}"
             for m in history[-10:]]
        )

        prompt = f"""
        Sen İslami manevi bir rehbersin. Kullanıcıyla devam eden bir sohbetin var.

        KULLANICI PROFİLİ:
        {profile_str}

        AKTİF PLANLAR:
        {plans_str}

        KULLANICI ANILARI:
        {user_context.get('memory_str', 'Henüz kayıtlı anı yok.') if user_context else 'Henüz kayıtlı anı yok.'}

        MANEVİ TERCİHLERİ:
        {user_context.get('spiritual_prefs', 'Belirlenmemiş') if user_context else 'Belirlenmemiş'}

        DİL STİLİ VE İLİŞKİ TONU:
        {self._format_language_style_instruction(user_context) if user_context else 'Standart samimi ton kullan.'}

        SON SOHBET:
        {history_text}

        KULLANICININ SON MESAJI: "{user_message}"

        KARAR VER:
        A) Kullanıcı MEVCUT PLAN hakkında mı konuşuyor? (geri bildirim, soru, şikayet)
           → Plan hakkında yorum yap, motivasyon ver, bugünkü görevlerden bahset
        B) Kullanıcı YENİ BİR KONU mu açıyor? (farklı dert, yeni sorun)
           → "new_topic" olarak işaretle (geçmiş anıları kontrol et, benzer bir dert yaşamış mı?)
        C) Kullanıcı GENEL SOHBET mi yapıyor?
           → Samimi, sıcak yanıt ver. Duruma göre planını hatırlat. Anılarından bahset.

        {"Kullanıcıyı tanıyorsun, samimi ama saygılı ol. İsmiyle hitap edebilirsin." if profile_str else ""}
        ASLA "canım", "hayatım" gibi ifadeler kullanma.
        Kullanıcının dil stiline ve ilişki tonuna uygun konuş.

        JSON DÖNDÜR:
        {{
            "response_type": "plan_feedback" | "new_topic" | "general_chat",
            "response_text": "Türkçe yanıt (2-4 cümle)",
            "should_update_plan": true/false
        }}
        """

        try:
            response = await generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            import json
            parsed = json.loads(raw)
        except Exception:
            # Fallback to old behavior
            update_check = await self.check_update_need(user_message, history)
            if update_check["needs_update"]:
                if update_check["is_new_topic"]:
                    return {
                        "intent": "GATHERING",
                        "response": "Anlıyorum, bu farklı bir konu. Biraz daha anlatır mısın?",
                        "new_phase": "GATHERING",
                        "readiness_score": 10,
                        "needs_prescription_update": False,
                    }
                return {
                    "intent": "UPDATE_PRESCRIPTION",
                    "response": update_check["response_text"],
                    "new_phase": "ONGOING",
                    "readiness_score": 100,
                    "needs_prescription_update": True,
                }
            return {
                "intent": "CHAT",
                "response": update_check["response_text"],
                "new_phase": "ONGOING",
                "readiness_score": 100,
            }

        response_type = parsed.get("response_type", "general_chat")
        response_text = parsed.get("response_text", "Seni dinliyorum.")

        if response_type == "new_topic":
            return {
                "intent": "GATHERING",
                "response": response_text,
                "new_phase": "GATHERING",
                "readiness_score": 10,
                "needs_prescription_update": False,
            }
        elif response_type == "plan_feedback" and parsed.get("should_update_plan"):
            return {
                "intent": "UPDATE_PRESCRIPTION",
                "response": response_text,
                "new_phase": "ONGOING",
                "readiness_score": 100,
                "needs_prescription_update": True,
            }
        else:
            return {
                "intent": "CHAT",
                "response": response_text,
                "new_phase": "ONGOING",
                "readiness_score": 100,
            }

    # ──────────────────────────────────────────
    # HELPER: Format language style instruction
    # ──────────────────────────────────────────

    def _format_language_style_instruction(self, user_context: dict) -> str:
        """
        Format language style and conversational tone into AI prompt instruction.
        Adapts AI's communication style to match user's preferences over time.
        """
        if not user_context:
            return "Standart samimi ton kullan."

        language_style = user_context.get('language_style', {})
        conversational_tone = user_context.get('conversational_tone', 'polite_formal')

        # Formality level (0-1 scale)
        formality = language_style.get('formality_level', 0.5)
        formality_pct = int(formality * 100)

        # Emoji usage
        emoji_usage = language_style.get('emoji_usage', 0.0)
        emoji_instruction = ""
        if emoji_usage > 0.5:
            emoji_instruction = "Kullanıcı emoji kullanıyor, sen de ara sıra uygun emoji kullan (🤲, 🌟, ✨, 💚)."
        elif emoji_usage > 0.2:
            emoji_instruction = "Kullanıcı nadiren emoji kullanıyor, sen de çok az kullan."
        else:
            emoji_instruction = "Kullanıcı emoji kullanmıyor, sen de kullanma."

        # Address style
        address_style = language_style.get('address_style', 'sen')
        if address_style == 'siz':
            address_instruction = "'Siz' ile hitap et (formel üslup)."
        else:
            address_instruction = "'Sen' ile hitap et (samimi ama saygılı)."

        # Vocabulary preference
        vocab = language_style.get('vocabulary_preference', 'standard')
        vocab_instruction = ""
        if vocab == 'religious':
            vocab_instruction = "Kullanıcı manevi/dini kelimeler seviyor, sen de daha fazla dini terim kullan."
        elif vocab == 'modern':
            vocab_instruction = "Kullanıcı modern dil kullanıyor, sen de güncel ve anlaşılır ifadeler kullan."

        # Common phrases (user's frequently used words)
        common_phrases = language_style.get('common_phrases', [])
        phrases_instruction = ""
        if common_phrases:
            phrases_str = ", ".join(common_phrases[:5])
            phrases_instruction = f"Kullanıcının sık kullandığı kelimeler: {phrases_str}. Doğal olduğunda bunları sen de kullan."

        # Tone evolution based on relationship
        tone_map = {
            "polite_formal": "İlişki yeni başladı. Saygılı ve dikkatli ol. 'Sizi dinliyorum', 'Size yardımcı olmak isterim' gibi ifadeler kullan.",
            "warm_friendly": "Kullanıcıyla tanışıklık gelişti. Samimi ve dostane ol. 'Seni dinliyorum', 'Nasılsın bugün?' gibi samimi ifadeler kullan.",
            "empathetic_guide": "İlişki derinleşti. Şefkatli ve anlayışlı bir rehber gibi ol. 'Anlıyorum, bu gerçekten zor', 'Seninle bu yolculuktayım' gibi empatik ifadeler kullan.",
            "spiritual_companion": "Uzun süreli ilişki var. Manevi bir dost/kardeş gibi ol. 'Kardeşim', 'Yine buradayız', 'Birlikte devam edelim inşaAllah' gibi yakın ifadeler kullan.",
        }
        tone_instruction = tone_map.get(conversational_tone, "Samimi ama saygılı ol.")

        # Combine all instructions
        instruction = f"""
        Kullanıcının dil tercihleri:
        - Samimiyet: {formality_pct}% formel ({"formal" if formality > 0.7 else "samimi" if formality < 0.3 else "dengeli"})
        - {emoji_instruction}
        - {address_instruction}
        {f"- {vocab_instruction}" if vocab_instruction else ""}
        {f"- {phrases_instruction}" if phrases_instruction else ""}

        İlişki tonu: {conversational_tone}
        → {tone_instruction}

        ÖNEMLİ: Kullanıcıyı taklit etme, sadece uyum sağla. Doğal ve samimi kal.
        """

        return instruction.strip()
