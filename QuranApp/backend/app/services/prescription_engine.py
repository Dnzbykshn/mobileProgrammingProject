"""
PrescriptionEngine - Spiritual therapy prescription service.
Async version — uses centralized ai_service for Gemini/embeddings.

3-Phase process:
  1. Diagnose (LLM analysis of user's emotional state)
  2. Retrieve (Vector search for Esma, Dua, Verses)
  3. Synthesize (Combine into prescription card)
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from pydantic import BaseModel

from app.services.ai_service import generate_content, get_embedding
from app.utils.text_utils import normalize_turkish, chop_for_root


# --- MODELS ---
class Diagnosis(BaseModel):
    emotional_state: str
    root_cause: str
    spiritual_needs: List[str]
    search_keywords: List[str]


class PrescriptionEngine:
    # Verses that require deep context and might be misunderstood/harmful in AI auto-prescription
    BLACKLIST_VERSES = {
        "4:34",   # Nisa 34 (men are qawwam/beating)
        "64:14",  # Teğabun 14 (wives/children are enemies)
        "2:191",  # Kill them where you find them (context: war)
        "9:5",    # Sword verse
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def diagnose(self, conversation_context: str) -> Diagnosis:
        """Phase 1: Doctor - Analyze feelings from full conversation context."""
        print(f"🧠 Diagnosing from conversation context...")

        prompt = f"""
        Sen uzman bir İslami Manevi Terapistsin (Islamic Spiritual Psychologist).
        Kullanıcıyla birkaç tur konuştun ve yeterli bilgi topladın.
        Şimdi tüm konuşma bağlamını analiz ederek derinlemesine bir teşhis koy.
        
        TÜM KONUŞMA BAĞLAMI:
        {conversation_context}
        
        Aşağıdaki alanları içeren geçerli bir JSON nesnesi döndür:
        1. "emotional_state": Birincil duygu durumu (ör. Kaygı, Öfke, Hüzün, Korku, Üzüntü, Stres, Umutsuzluk). Türkçe olmalı.
        2. "root_cause": Bu şekilde hissetmelerinin derinlemesine psikolojik analizi. 
           Konuşmadan öğrendiğin detayları kullan. Türkçe olmalı.
        3. "spiritual_needs": İhtiyaç duydukları 3 manevi kavram listesi (ör. "Tevekkül", "Sabır", "Ümit"). Türkçe olmalı.
        4. "search_keywords": Kuran/Esma/Dua'da aranacak 3-5 Türkçe anahtar kelime listesi.

        KRİTİK ARAMA KURALI:
        - ASLA sorunu (örn. "boşanma", "düşmanlık", "kavga") arama. 
        - DAİMA ilacı (örn. "merhamet", "sekine", "muhabbet", "sakinlik") ara.
        - "Boşanma" yerine "Teskin teselli" ara.
        
        TÜM ALANLAR TÜRKÇE OLMALIDIR.
        """

        response = await generate_content(prompt, response_schema=Diagnosis)
        return Diagnosis(**response.parsed.model_dump())

    async def retrieve_esma(self, keywords: List[str]):
        """Phase 2a: Get Esma — table not yet populated, return empty."""
        # TODO: Create and populate esma_ul_husna table
        print(f"💊 Esma tablosu henüz mevcut değil, atlanıyor.")
        return []

    async def retrieve_dua(self, keywords: List[str]):
        """Phase 2b: Get Dua — table not yet populated, return empty."""
        # TODO: Create and populate prophet_duas table
        print(f"🤲 Dua tablosu henüz mevcut değil, atlanıyor.")
        return []

    async def select_best_verses(self, candidates: List[dict], diagnosis: Diagnosis) -> List[dict]:
        """Phase 2d: Spiritual Editor - Filter candidates for tone/relevance using LLM."""
        if not candidates:
            return []

        print(f"⚖️ Selecting best verses from {len(candidates)} candidates...")
        
        # Prepare candidates for LLM review
        candidates_preview = []
        for i, c in enumerate(candidates):
            candidates_preview.append({
                "id": i,
                "text": c["verse_text_tr"],
                "source": f"{c['verse_tr_name']} {c['surah_no']}:{c['verse_no']}"
            })
        
        prompt = f"""
        MANEVİ EDİTÖR GÖREVİ (Verse Selector):
        
        KULLANICI DURUMU:
        - Duygu: {diagnosis.emotional_state}
        - Kök Neden: {diagnosis.root_cause}
        - İhtiyaç: {', '.join(diagnosis.spiritual_needs)}
        
        ADAY AYETLER:
        {json.dumps(candidates_preview, ensure_ascii=False, indent=2)}
        
        GÖREVİN:
        Bu adaylar arasından kullanıcının ruh haline EN İYİ gelecek, ona şifa, umut ve teselli verecek EN FAZLA 2 ayeti seç.
        
        ELEMELER (ÇOK ÖNEMLİ):
        1. BAĞLAM HATASI: Hukuki hükümler (miras, boşanma prosedürü), savaş hukuku veya sert uyarılar içeren ayetleri ELE.
        2. SERTLİK: "Cehennem", "Azap", "Lanet" içeren korkutucu ayetleri -eğer kullanıcı kibir içinde değilse- ELE.
        3. ALAKASIZLIK: Kelime geçiyor ama anlam uymuyorsa ELE.
        
        HEDEF:
        Kullanıcı okuduğunda "Beni tam kalbimden vurdu, Rabbim benimle konuşuyor" hissi verecek "merhem" ayetleri seç.
        
        JSON ÇIKTISI:
        {{
            "selected_ids": [0, 3]  // Seçilen ayetlerin ID listesi (max 2 tane)
        }}
        """

        class SelectionResult(BaseModel):
            selected_ids: List[int]

        try:
            response = await generate_content(prompt, response_schema=SelectionResult)
            selected_indices = response.parsed.selected_ids
            
            final_selection = [candidates[i] for i in selected_indices if 0 <= i < len(candidates)]
            return final_selection[:2] # Ensure max 2
            
        except Exception as e:
            print(f"⚠️ Verse selection AI failed ({e}), falling back to top 2.")
            return candidates[:2]

    async def retrieve_verses(self, keywords: List[str], diagnosis: Diagnosis = None):
        """Phase 2c: Hybrid Search -> Smart Selection."""
        search_text = " ".join(keywords)
        print(f"📖 Fetching Verse Candidates for: {search_text}")
        embedding = await get_embedding(search_text)

        candidates = []
        seen_texts = set()

        # 1. TEXT SEARCH (Broader net: limit 5)
        for keyword in keywords:
            if len(candidates) >= 5 or len(keyword) < 3:
                continue

            normalized_keyword = normalize_turkish(keyword)
            chopped_keyword = chop_for_root(keyword)

            sql_text_query = text("""
                SELECT metadata, content_text, explanation
                FROM knowledge_units
                WHERE (content_text ILIKE :search OR explanation ILIKE :search
                   OR content_text ILIKE :norm OR explanation ILIKE :norm)
                   OR (
                      (content_text ILIKE :chop_start OR content_text ILIKE :chop_space)
                      OR 
                      (explanation ILIKE :chop_start OR explanation ILIKE :chop_space)
                   )
                ORDER BY (
                    CASE 
                        WHEN content_text ILIKE :search OR content_text ILIKE :norm 
                        THEN 1 
                        ELSE 2 
                    END
                ) ASC
                LIMIT 3
            """)

            result = await self.db.execute(
                sql_text_query,
                {
                    "search": f"%{keyword}%",
                    "norm": f"%{normalized_keyword}%",
                    "chop_start": f"{chopped_keyword}%",
                    "chop_space": f"% {chopped_keyword}%",
                },
            )

            for row in result.fetchall():
                meta = row[0]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {} # Handle metadata error gracefully
                
                if row[1] not in seen_texts:
                    seen_texts.add(row[1])
                    candidates.append({
                        "verse_text_ar": meta.get("arabic_text", ""),
                        "verse_text_tr": row[1],
                        "explanation": row[2],
                        "surah_no": meta.get("surah_no", 0),
                        "verse_no": meta.get("verse_no", 0),
                        "verse_tr_name": meta.get("surah_name", "Süre"),
                        "source_type": "TEXT_MATCH",
                    })

        # 2. VECTOR SEARCH (Fill up to 10 candidates total)
        limit = 10 - len(candidates)
        if limit > 0:
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            sql_vector = text("""
                SELECT metadata, content_text, explanation
                FROM knowledge_units
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :lim
            """)
            result = await self.db.execute(sql_vector, {"emb": embedding_str, "lim": limit})
            for row in result.fetchall():
                meta = row[0]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                
                if row[1] not in seen_texts:
                    seen_texts.add(row[1])
                    candidates.append({
                        "verse_text_ar": meta.get("arabic_text", ""),
                        "verse_text_tr": row[1],
                        "explanation": row[2],
                        "surah_no": meta.get("surah_no", 0),
                        "verse_no": meta.get("verse_no", 0),
                        "verse_tr_name": meta.get("surah_name", "Süre"),
                        "source_type": "VECTOR_MATCH",
                    })

        # 3. SMART SELECTION (LLM Filter)
        if diagnosis:
            return await self.select_best_verses(candidates, diagnosis)
        
        return candidates[:2]  # Fallback if no diagnosis passed

    def synthesize_prescription(self, diagnosis, esmas, duas, verses) -> dict:
        """Phase 3: Create the finalized card data."""
        return {
            "diagnosis": diagnosis.model_dump(),
            "esmas": esmas,
            "duas": duas,
            "verses": verses,
            "advice": "Bu rutin sizin manevi durumunuza özel hazırlanmıştır.",
        }

    async def process_request(self, conversation_context: str) -> dict:
        """Main entry point — fully async pipeline using full conversation context."""
        print(f"🩺 Rutin Motoru İşleniyor (konuşma bağlamıyla)...")
        diagnosis = await self.diagnose(conversation_context)

        # Launch searches in parallel (Pass diagnosis to retrieve_verses for filtering)
        esmas_task = self.retrieve_esma(diagnosis.search_keywords)
        duas_task = self.retrieve_dua(diagnosis.search_keywords)
        verses_task = self.retrieve_verses(diagnosis.search_keywords, diagnosis=diagnosis)
        
        esmas, duas, verses = await asyncio.gather(esmas_task, duas_task, verses_task)

        return self.synthesize_prescription(diagnosis, esmas, duas, verses)
