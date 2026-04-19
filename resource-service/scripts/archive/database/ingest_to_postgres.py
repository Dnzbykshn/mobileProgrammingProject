import json
import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

# --- AYARLAR ---
INPUT_FILE = "data/quran_complete_final.json"
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

# Google Embeddings genelde 768 boyutludur.
VECTOR_DIMENSION = 768 

def create_table(cursor):
    """
    Geleceğe yönelik esnek tablo yapısını oluşturur.
    """
    # 1. Vektör eklentisini aktif et
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 2. Tabloyu oluştur
    create_query = f"""
    CREATE TABLE IF NOT EXISTS knowledge_units (
        id SERIAL PRIMARY KEY,
        source_type VARCHAR(50) NOT NULL,  -- 'quran', 'hadith' vb.
        content_text TEXT NOT NULL,        -- Ana metin
        explanation TEXT,                  -- AI açıklaması
        keywords TEXT[],                   -- Anahtar kelimeler listesi
        metadata JSONB,                    -- Esnek alan (Sure no, Ravi, Kitap adı vb.)
        embedding vector({VECTOR_DIMENSION}), -- Vektör verisi
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Hızlı arama için HNSW index (Çok büyük verilerde performans artırır)
    CREATE INDEX IF NOT EXISTS knowledge_vec_idx ON knowledge_units USING hnsw (embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS metadata_idx ON knowledge_units USING gin (metadata);
    """
    cursor.execute(create_query)
    print("✅ Tablo ve indexler hazırlandı.")

def ingest_data():
    try:
        # DB Bağlantısı
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        
        create_table(cur)

        # JSON Dosyasını Oku
        print(f"📂 '{INPUT_FILE}' okunuyor...")
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"🚀 {len(data)} veri veritabanına aktarılıyor...")

        inserted_count = 0
        for item in data:
            # Sadece vektörü olanları ekle (Hata olmasın)
            if not item.get('vector_embedding'):
                continue

            # --- VERİ HAZIRLIĞI ---
            source_type = 'quran'
            content = item['display']['turkish_text']
            explanation = item['semantic_content']['explanation']
            keywords = item['search_content']['keywords']
            embedding = item['vector_embedding']

            # METADATA (Esnek Kısım)
            # Kuran'a özel verileri buraya gömüyoruz.
            # Yarın Hadis eklerken buraya {"ravi": "Ebu Hureyre"} yazacaksın.
            meta = {
                "surah_no": item['display'].get('surah_no'),
                "verse_no": item['display'].get('verse_no'),
                "surah_name": item['display'].get('surah_name'),
                "arabic_text": item['display'].get('arabic_text'),
                "source_provider": item['display'].get('source')
            }

            # SQL INSERT
            insert_query = """
            INSERT INTO knowledge_units 
            (source_type, content_text, explanation, keywords, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (
                source_type,
                content,
                explanation,
                keywords,
                Json(meta), # JSONB formatına çevir
                embedding
            ))
            
            inserted_count += 1
            if inserted_count % 500 == 0:
                print(f"   💾 {inserted_count} kayıt eklendi...")

        print(f"\n🎉 İŞLEM TAMAM! Toplam {inserted_count} ayet PostgreSQL'e yüklendi.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    ingest_data()