"""
Ana Kur'an içeriğini PostgreSQL'e yazar.
quran_final_pristine.json, batch_results_merged.jsonl ve embeddings_768.jsonl kullanır.
"""

import json
import os
import psycopg2
from psycopg2.extras import Json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

# --- DOSYA YOLLARI ---
INPUT_DATA = PROJECT_ROOT / "data" / "quran_final_pristine.json"
ANALYSIS_RESULTS = PROJECT_ROOT / "data" / "batch_results_merged.jsonl"
EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "embeddings_768.jsonl"

# --- DB AYARLARI ---
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

VECTOR_DIMENSION = 768

# Sure isimleri
SURAH_NAMES = {
    1: "Fâtiha", 2: "Bakara", 3: "Âl-i İmrân", 4: "Nisâ", 5: "Mâide", 6: "En'âm", 7: "A'râf", 8: "Enfâl", 9: "Tevbe", 10: "Yûnus",
    11: "Hûd", 12: "Yûsuf", 13: "Ra'd", 14: "İbrâhîm", 15: "Hicr", 16: "Nahl", 17: "İsrâ", 18: "Kehf", 19: "Meryem", 20: "Tâhâ",
    21: "Enbiyâ", 22: "Hac", 23: "Mü'minûn", 24: "Nûr", 25: "Furkân", 26: "Şuarâ", 27: "Neml", 28: "Kasas", 29: "Ankebût", 30: "Rûm",
    31: "Lokmân", 32: "Secde", 33: "Ahzâb", 34: "Sebe'", 35: "Fâtır", 36: "Yâsîn", 37: "Sâffât", 38: "Sâd", 39: "Zümer", 40: "Mü'min",
    41: "Fussilet", 42: "Şûrâ", 43: "Zuhruf", 44: "Duhân", 45: "Câsiye", 46: "Ahkâf", 47: "Muhammed", 48: "Fetih", 49: "Hucurât", 50: "Kâf",
    51: "Zâriyât", 52: "Tûr", 53: "Necm", 54: "Kamer", 55: "Rahmân", 56: "Vâkıa", 57: "Hadîd", 58: "Mücâdele", 59: "Haşr", 60: "Mümtehine",
    61: "Saff", 62: "Cuma", 63: "Münâfikûn", 64: "Teğâbün", 65: "Talâk", 66: "Tahrîm", 67: "Mülk", 68: "Kalem", 69: "Hâkka", 70: "Meâric",
    71: "Nûh", 72: "Cin", 73: "Müzzemmil", 74: "Müddessir", 75: "Kıyâmet", 76: "İnsân", 77: "Mürselât", 78: "Nebe", 79: "Nâziât", 80: "Abese",
    81: "Tekvîr", 82: "İnfitâr", 83: "Mutaffifîn", 84: "İnşikâk", 85: "Bürûc", 86: "Târık", 87: "A'lâ", 88: "Gâşiye", 89: "Fecr", 90: "Beled",
    91: "Şems", 92: "Leyl", 93: "Duhâ", 94: "İnşirah", 95: "Tîn", 96: "Alak", 97: "Kadir", 98: "Beyyine", 99: "Zilzâl", 100: "Âdiyât",
    101: "Kâria", 102: "Tekâsür", 103: "Asr", 104: "Hümeze", 105: "Fîl", 106: "Kureyş", 107: "Mâûn", 108: "Kevser", 109: "Kâfirûn", 110: "Nasr",
    111: "Tebbet", 112: "İhlâs", 113: "Felak", 114: "Nâs"
}

def init_db():
    """Veritabanı tablosunu hazırlar."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Tabloyu yeniden oluştur
        cur.execute("DROP TABLE IF EXISTS knowledge_units;")
        
        create_query = f"""
        CREATE TABLE knowledge_units (
            id SERIAL PRIMARY KEY,
            source_type VARCHAR(50) NOT NULL,
            content_text TEXT NOT NULL,
            explanation TEXT,
            keywords TEXT[],
            metadata JSONB,
            embedding vector({VECTOR_DIMENSION}),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX metadata_idx ON knowledge_units USING gin (metadata);
        """
        cur.execute(create_query)
        
        # IVFFlat index için önce veri eklenecek, sonra index oluşturulacak
        print("✅ Veritabanı tablosu hazır (index veriler eklendikten sonra oluşturulacak).")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ DB Hatası: {e}")
        raise

def main():
    print("🚀 Veriler PostgreSQL'e yazılıyor...")
    
    # 1. Orijinal veriyi yükle
    print(f"📂 '{INPUT_DATA}' okunuyor...")
    with open(INPUT_DATA, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    # Key -> index mapping
    key_to_index = {}
    for i, doc in enumerate(dataset):
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        key_to_index[key] = i
    
    # 2. Analiz sonuçlarını yükle
    print(f"📂 '{ANALYSIS_RESULTS}' okunuyor...")
    analysis_count = 0
    with open(ANALYSIS_RESULTS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            result = json.loads(line)
            key = result.get('key', '')
            
            try:
                response = result.get('response', {})
                candidates = response.get('candidates', [])
                if not candidates:
                    continue
                
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if not parts:
                    continue
                
                text_content = None
                for part in parts:
                    if 'text' in part:
                        text_content = part.get('text', '')
                        break
                
                if not text_content:
                    continue
                
                # JSON parse - liste veya obje olabilir
                parsed = json.loads(text_content)
                if isinstance(parsed, list):
                    parsed = parsed[0] if parsed else {}
                
                keywords = parsed.get('keywords', [])
                explanation = parsed.get('explanation', '')
                
                if key in key_to_index and keywords:
                    idx = key_to_index[key]
                    dataset[idx]['search_content']['keywords'] = keywords
                    dataset[idx]['semantic_content']['explanation'] = explanation
                    analysis_count += 1
            except:
                continue
    
    print(f"✅ {analysis_count} analiz sonucu yüklendi.")
    
    # 3. Embedding'leri yükle
    print(f"📂 '{EMBEDDINGS_FILE}' okunuyor...")
    embeddings = {}
    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                key = data.get('key', '')
                embedding = data.get('embedding', [])
                if key and embedding:
                    embeddings[key] = embedding
    
    print(f"✅ {len(embeddings)} embedding yüklendi.")
    
    # 4. DB'yi hazırla
    print("\n🗄️ Veritabanı hazırlanıyor...")
    init_db()
    
    # 5. Verileri yaz
    print("\n📝 Veriler yazılıyor...")
    
    # Kuran sırasına göre sırala
    dataset.sort(key=lambda x: (x['display'].get('surah_no', 0), x['display'].get('verse_no', 0)))
    
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
    success_count = 0
    skip_count = 0
    
    for doc in dataset:
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        
        keywords = doc['search_content'].get('keywords', [])
        embedding = embeddings.get(key)
        
        # Hem keywords hem embedding olmalı
        if not keywords or not embedding:
            skip_count += 1
            continue
        
        try:
            surah_name = f"{SURAH_NAMES.get(surah_no, 'Sure ' + str(surah_no))} Suresi"
            
            meta = {
                "surah_no": surah_no,
                "verse_no": verse_no,
                "surah_name": surah_name,
                "arabic_text": doc['display'].get('arabic_text'),
                "source_provider": doc['display'].get('source')
            }
            
            insert_query = """
            INSERT INTO knowledge_units 
            (source_type, content_text, explanation, keywords, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (
                'quran',
                doc['display']['turkish_text'],
                doc['semantic_content'].get('explanation', ''),
                keywords,
                Json(meta),
                embedding
            ))
            
            success_count += 1
            if success_count % 500 == 0:
                print(f"   💾 {success_count} kayıt yazıldı...")
                
        except Exception as e:
            print(f"⚠️ {key}: DB hatası - {e}")
    
    # 6. HNSW index oluştur
    print("\n🔧 Vector index oluşturuluyor...")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("""
        CREATE INDEX knowledge_vec_idx 
        ON knowledge_units 
        USING hnsw (embedding vector_cosine_ops);
    """)
    cur.close()
    conn.close()
    print("✅ HNSW Vector index oluşturuldu.")
    
    print(f"\n🎉 TAMAMLANDI!")
    print(f"✅ {success_count} ayet veritabanına kaydedildi.")
    print(f"⏭️ {skip_count} ayet atlandı (eksik veri).")

if __name__ == "__main__":
    main()
