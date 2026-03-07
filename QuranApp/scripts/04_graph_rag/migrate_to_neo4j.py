"""
Neo4j Graph Migration Script
============================
PostgreSQL'deki tüm Graph RAG verisini Neo4j'e aktarır.

Yüklenen Graf Yapısı:
  (:RootCategory {name}) -[:HAS_SUBCATEGORY]-> (:SubCategory {name})
  (:SubCategory {name}) -[:HAS_KEYWORD]-> (:Keyword {text, embedding})
  (:KnowledgeUnit {id, verse_ref, translation, explanation}) -[:TAGGED_WITH]-> (:Keyword {text})

Kullanım:
  1. Neo4j Docker container'ı çalışır durumda olmalı (docker compose up neo4j)
  2. pip install neo4j
  3. python scripts/04_graph_rag/migrate_to_neo4j.py
"""

import os
import sys
import time
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

try:
    from neo4j import GraphDatabase
except ImportError:
    sys.exit("❌ neo4j paketi kurulu değil! Önce: pip install neo4j")



# --- .env yükle ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- PostgreSQL Bağlantısı ---
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

# --- Neo4j Bağlantısı ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")



def setup_neo4j_schema(session):
    """Constraints ve Vector Index'leri oluşturur."""
    print("📐 Neo4j Schema (Constraints + Indexes) oluşturuluyor...")
    constraints = [
        "CREATE CONSTRAINT root_name IF NOT EXISTS FOR (r:RootCategory) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT sub_name IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT kw_text IF NOT EXISTS FOR (k:Keyword) REQUIRE k.text IS UNIQUE",
        "CREATE CONSTRAINT ku_id IF NOT EXISTS FOR (u:KnowledgeUnit) REQUIRE u.id IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)

    # Neo4j 5.11+ Vector Index for Keyword embeddings
    try:
        session.run("""
            CREATE VECTOR INDEX keyword_embedding IF NOT EXISTS
            FOR (k:Keyword) ON k.embedding
            OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
        """)
        print("  ✅ Keyword Vector Index oluşturuldu.")
    except Exception as e:
        print(f"  ⚠️ Vector Index oluşturulamadı (Neo4j versiyonu eski olabilir): {e}")

    print("  ✅ Schema hazır.")

def migrate_ontology(session, taxonomy_rows):
    """RootCategory, SubCategory ve Keyword node'larını ve aralarındaki ilişkileri yükler."""
    print("\n📍 ADIM 1: Ontoloji Hiyerarşisi (10 Çatı → 50 Alt → 5643 Keyword) yükleniyor...")

    # RootCategory node'ları
    root_cats = list({row["root_category"] for row in taxonomy_rows})
    session.run("""
        UNWIND $roots AS root
        MERGE (:RootCategory {name: root})
    """, roots=root_cats)
    print(f"  ✅ {len(root_cats)} RootCategory node'u oluşturuldu.")

    # SubCategory node'ları ve HAS_SUBCATEGORY ilişkileri
    sub_data = list({(row["sub_category"], row["root_category"]) for row in taxonomy_rows})
    session.run("""
        UNWIND $subs AS sub
        MERGE (s:SubCategory {name: sub[0]})
        MERGE (r:RootCategory {name: sub[1]})
        MERGE (r)-[:HAS_SUBCATEGORY]->(s)
    """, subs=[list(s) for s in sub_data])
    print(f"  ✅ {len(sub_data)} SubCategory node'u ve HAS_SUBCATEGORY ilişkileri oluşturuldu.")

    # Keyword node'ları ve HAS_KEYWORD ilişkileri (batch'ler halinde)
    # Embedding'ler PostgreSQL'den zaten okundu — tekrar Gemini'ye gitmiyoruz
    has_emb = sum(1 for r in taxonomy_rows if r["embedding"] is not None)
    print(f"  🧠 {has_emb}/{len(taxonomy_rows)} keyword'ün embedding'i PostgreSQL'den okundu.")

    KEYWORD_BATCH = 500
    for i in range(0, len(taxonomy_rows), KEYWORD_BATCH):
        batch = taxonomy_rows[i:i + KEYWORD_BATCH]
        kw_data = []
        for row in batch:
            entry = {
                "text": row["canonical_keyword"],
                "sub": row["sub_category"],
            }
            if row["embedding"] is not None:
                entry["emb"] = row["embedding"]
            else:
                entry["emb"] = None
            kw_data.append(entry)

        # Embedding'i olanları SET et, olmayanları atla
        session.run("""
            UNWIND $kws AS kw
            MERGE (k:Keyword {text: kw.text})
            SET k.embedding = CASE WHEN kw.emb IS NOT NULL THEN kw.emb ELSE k.embedding END
            MERGE (s:SubCategory {name: kw.sub})
            MERGE (s)-[:HAS_KEYWORD]->(k)
        """, kws=kw_data)
        print(f"  ... {min(i + KEYWORD_BATCH, len(taxonomy_rows))}/{len(taxonomy_rows)} Keyword işlendi.")

    print(f"  ✅ {len(taxonomy_rows)} Keyword node'u oluşturuldu.")

def migrate_knowledge_units(session, pg_cur):
    """KnowledgeUnit (Ayet, Hadis, Esma) node'larını ve TAGGED_WITH ilişkilerini yükler."""
    print("\n📍 ADIM 2: KnowledgeUnit (Ayet) node'ları yükleniyor...")

    # Tüm knowledge_units'i PostgreSQL'den çek
    pg_cur.execute("""
        SELECT ku.id, ku.source_type, ku.content_text, ku.explanation
        FROM knowledge_units ku
    """)
    units = pg_cur.fetchall()
    unit_cols = [desc[0] for desc in pg_cur.description]
    print(f"  📂 {len(units)} KnowledgeUnit PostgreSQL'den çekildi.")

    # Neo4j'e batch batch yükle
    BATCH = 500
    for i in range(0, len(units), BATCH):
        batch = units[i:i + BATCH]
        unit_data = []
        for row in batch:
            row_dict = dict(zip(unit_cols, row))
            unit_data.append({
                "id": row_dict.get("id"),
                "source_type": row_dict.get("source_type", ""),
                "source_ref": "",
                "translation": row_dict.get("content_text", "")[:2000] if row_dict.get("content_text") else "",
                "explanation": row_dict.get("explanation", "")[:3000] if row_dict.get("explanation") else "",
            })
        session.run("""
            UNWIND $units AS u
            MERGE (ku:KnowledgeUnit {id: u.id})
            SET ku.source_type = u.source_type,
                ku.source_ref = u.source_ref,
                ku.translation = u.translation,
                ku.explanation = u.explanation
        """, units=unit_data)
        print(f"  ... {min(i + BATCH, len(units))}/{len(units)} KnowledgeUnit işlendi.")

    print(f"  ✅ {len(units)} KnowledgeUnit node'u yüklendi.")

    # TAGGED_WITH ilişkileri
    print("\n📍 ADIM 3: KnowledgeUnit -> Keyword ilişkileri (TAGGED_WITH) oluşturuluyor...")
    pg_cur.execute("""
        SELECT knowledge_unit_id, canonical_keyword FROM knowledge_units_graph_keywords
    """)
    relations = pg_cur.fetchall()
    print(f"  📂 {len(relations)} KnowledgeUnit-Keyword ilişkisi çekildi.")

    REL_BATCH = 2000
    for i in range(0, len(relations), REL_BATCH):
        batch = relations[i:i + REL_BATCH]
        rel_data = [{"uid": r[0], "kw": r[1]} for r in batch]
        session.run("""
            UNWIND $rels AS rel
            MATCH (ku:KnowledgeUnit {id: rel.uid})
            MATCH (k:Keyword {text: rel.kw})
            MERGE (ku)-[:TAGGED_WITH]->(k)
        """, rels=rel_data)
        print(f"  ... {min(i + REL_BATCH, len(relations))}/{len(relations)} ilişki işlendi.")

    print(f"  ✅ {len(relations)} TAGGED_WITH ilişkisi oluşturuldu.")

def main():
    print("🚀 Neo4j Graph Migration Başlıyor!\n")
    print(f"📡 Neo4j Bağlantısı: {NEO4J_URI}")
    
    # PostgreSQL bağlantısı
    pg_conn = psycopg2.connect(**DB_PARAMS)
    pg_cur = pg_conn.cursor()
    
    # Taxonomy verisini çek
    pg_cur.execute("""
        SELECT canonical_keyword, sub_category, root_category, embedding::text
        FROM keyword_taxonomy_map
        ORDER BY root_category, sub_category;
    """)
    taxonomy_rows = []
    for r in pg_cur.fetchall():
        emb = None
        if r[3] is not None:
            # pgvector text formatı: "[0.1,0.2,...]" → Python list'e çevir
            emb = [float(x) for x in r[3].strip("[]").split(",")]
        taxonomy_rows.append({
            "canonical_keyword": r[0],
            "sub_category": r[1],
            "root_category": r[2],
            "embedding": emb,
        })
    print(f"✅ {len(taxonomy_rows)} keyword taxonomy verisi PostgreSQL'den yüklendi.")

    emb_count = sum(1 for r in taxonomy_rows if r["embedding"] is not None)
    print(f"✅ {emb_count}/{len(taxonomy_rows)} keyword'ün embedding'i PostgreSQL'den yüklendi.")
    if emb_count == 0:
        print("⚠️  Hiç embedding bulunamadı! Önce embed_keywords_v5.py'yi çalıştırın.")
    
    # Neo4j bağlantısı
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Schema
            setup_neo4j_schema(session)
            
            # Ontoloji
            migrate_ontology(session, taxonomy_rows)
            
            # Knowledge Units & TAGGED_WITH
            migrate_knowledge_units(session, pg_cur)

        print("\n" + "="*55)
        print("✅ NEO4J MIGRATION TAMAMLANDI!")
        print("="*55)
        print("🌐 Neo4j Browser için: http://localhost:7474")
        print(f"   Kullanıcı: {NEO4J_USER}")
        print("   (Şifreyi .env'den kontrol edin)")
        print("\nTest sorgusu Neo4j Browser'da:")
        print("  MATCH (root:RootCategory)-[:HAS_SUBCATEGORY]->(sub)-[:HAS_KEYWORD]->(kw)")
        print("  RETURN root.name, sub.name, kw.text LIMIT 25")
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        raise
    finally:
        driver.close()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    main()
