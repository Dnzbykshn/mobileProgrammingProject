import os
import sys
import json
from google import genai
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

# --- AYARLAR ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")
client = genai.Client(api_key=GEMINI_API_KEY)

# --- SCHEMA ---
class EsmaItem(BaseModel):
    name: str = Field(..., description="Arabic name provided (e.g., Al-Wali)")
    appellation: str = Field(..., description="Turkish name (e.g., El-Velî)")
    meaning: str = Field(..., description="Deep spiritual meaning")
    psychological_benefits: List[str] = Field(..., description="List of psychological states helps with (e.g. Anxiety, Loneliness)")
    zmir_recommendation: str = Field(..., description="Short recommendation text for prescription card")

class DuaItem(BaseModel):
    source: str = Field(..., description="Source (e.g., Bukhari, Muslim)")
    arabic_text: str = Field(..., description="Arabic text of the dua")
    turkish_text: str = Field(..., description="Turkish translation")
    context: str = Field(..., description="When context (e.g. \"Borç altında ezilince okunur\")")
    emotional_tags: List[str] = Field(..., description="Tags for vector matching (e.g. [\"Kaygı\", \"Korku\"])")

class EsmaList(BaseModel):
    items: List[EsmaItem]

class DuaList(BaseModel):
    items: List[DuaItem]

def generate_esma():
    print("⏳ Generating ALL 99 Esma-ul Husna data...")
    prompt = """
    You are an expert Islamic psychologist and scholar.
    Generate a JSON list of ALL 99 Names of Allah (Esma-ul Husna).
    
    IMPORTANT: You must provide ALL 99 names. Do not truncate.
    IMPORTANT: ALL CONTENT MUST BE IN TURKISH. Do not use English.
    
    For each name, provide:
    1. Arabic Name (transliterated)
    2. Turkish Name (e.g. El-Vekîl)
    3. Meaning (Turkish)
    4. Psychological/Spiritual Benefits (Tags for vector search in Turkish, e.g. "Gelecek Kaygısı", "Yalnızlık", "Özgüvensizlik")
    5. Zikir/Recommendation Note (Turkish, short advice)
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EsmaList
        }
    )
    
    data = response.parsed.model_dump()
    os.makedirs("data", exist_ok=True)
    with open("data/esma_enriched.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {len(data['items'])} Esma records.")

def generate_duas():
    print("⏳ Generating Comprehensive Prophet Duas data (100+)...")
    prompt = """
    You are an expert Islamic scholar who speaks fluent Turkish.
    Generate a COMPREHENSIVE JSON list of 100 Authentic Prophetic Duas (Masnoon Duas) covering all aspects of mental health and daily spiritual resilience.
    
    Categories to cover:
    1. Anxiety, Sorrow, and Depression (Hüzün ve Kaygı)
    2. Fear and Protection (Korku ve Korunma)
    3. Sleep and Insomnia (Uyku ve Uykusuzluk)
    4. Debt and Poverty (Borç ve Fakirlik)
    5. Anger Control (Öfke Kontrolü)
    6. Waswasah and OCD (Vesvese ve Takıntı)
    7. Decision Making (İstihare ve Kararsızlık)
    8. General Well-being and Gratitude (Şükür ve Afiyet)
    9. Forgiveness and Guilt (Tövbe ve Pişmanlık)
    10. Loneliness and Abandonment (Yalnızlık)

    IMPORTANT: ALL CONTENT MUST BE IN TURKISH.
    
    For each dua provide:
    1. Source (e.g. Tirmizi, Deavat 100)
    2. Arabic Text
    3. Turkish Meaning
    4. Context (Turkish) - When to read
    5. Emotional Tags (Turkish) - (e.g. ["Kaygı", "Korku", "Borç"])
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": DuaList
        }
    )
    
    data = response.parsed.model_dump()
    with open("data/duas_enriched.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {len(data['items'])} Dua records.")

if __name__ == "__main__":
    # generate_esma()
    generate_duas()
