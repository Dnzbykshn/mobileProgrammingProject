import json
import os
import sys
import psycopg2
from google import genai
import time
from dotenv import load_dotenv

load_dotenv()

# --- AYARLAR ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

client = genai.Client(api_key=GEMINI_API_KEY)

def get_embedding(text):
    time.sleep(1) # Rate limit korumasi
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config={"output_dimensionality": 768}
    )
    return result.embeddings[0].values

def insert_esma():
    print("🚀 Embedding & Inserting Esma Data...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    with open("data/esma_enriched.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    items = data.get("items", [])
    for item in items:
        # Vektörlenecek metin: Duygusal faydalar + Anlam
        # Örn: "Gelecek Kaygısı Yalnızlık. Her işini Allah'a bırakan"
        text_to_embed = " ".join(item["psychological_benefits"]) + " " + item["meaning"]
        vector = get_embedding(text_to_embed)
        
        cur.execute("""
            INSERT INTO esma_ul_husna 
            (name, appellation, meaning, psychological_benefits, referral_note, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            item["name"],
            item["appellation"],
            item["meaning"],
            item["psychological_benefits"],
            item["zmir_recommendation"],
            vector
        ))
        print(f"   -> Inserted: {item['appellation']}")
        
    conn.commit()
    conn.close()

def insert_duas():
    print("🚀 Embedding & Inserting Dua Data...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    with open("data/duas_enriched.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    items = data.get("items", [])
    for item in items:
        # Vektörlenecek metin: Context + Tags
        # Örn: "When feeling overwhelmed. Anxiety Fear Debt"
        text_to_embed = item["context"] + " " + " ".join(item["emotional_tags"])
        vector = get_embedding(text_to_embed)
        
        cur.execute("""
            INSERT INTO prophet_duas 
            (source, arabic_text, turkish_text, context, emotional_tags, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            item["source"],
            item["arabic_text"],
            item["turkish_text"],
            item["context"],
            item["emotional_tags"],
            vector
        ))
        print(f"   -> Inserted Dua from: {item['source']}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # insert_esma()
    insert_duas()
