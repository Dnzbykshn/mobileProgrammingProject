import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

def create_tables():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    print("🛠️ Creating prescription tables...")
    
    # Esma Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS esma_ul_husna (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100), -- Arabic name
            appellation VARCHAR(100), -- Turkish name (El-Vekil)
            meaning TEXT,
            psychological_benefits TEXT[], -- Array of strings
            referral_note TEXT, -- "Gelecek kaygisinda..."
            embedding vector(768) -- For semantic search on benefits
        );
    """)
    
    # Dua Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prophet_duas (
            id SERIAL PRIMARY KEY,
            source VARCHAR(100),
            arabic_text TEXT,
            turkish_text TEXT,
            context TEXT,
            emotional_tags TEXT[],
            embedding vector(768) -- For semantic search on tags/context
        );
    """)
    
    # Indexler (HNSW for fast vector search)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS esma_embedding_idx ON esma_ul_husna USING hnsw (embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS dua_embedding_idx ON prophet_duas USING hnsw (embedding vector_cosine_ops);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables created successfully.")

if __name__ == "__main__":
    create_tables()
