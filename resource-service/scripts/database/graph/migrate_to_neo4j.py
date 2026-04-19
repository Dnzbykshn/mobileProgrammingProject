import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
except ImportError:
    sys.exit("❌ neo4j paketi kurulu değil. Önce resource-service/requirements.txt kurun.")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def clear_graph(session) -> None:
    print("🧹 Neo4j temizleniyor...")
    session.run("MATCH (n) DETACH DELETE n")


def setup_neo4j_schema(session) -> None:
    print("📐 Neo4j schema hazırlanıyor...")
    constraints = [
        "CREATE CONSTRAINT root_name IF NOT EXISTS FOR (r:RootCategory) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT sub_name IF NOT EXISTS FOR (s:SubCategory) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT kw_text IF NOT EXISTS FOR (k:Keyword) REQUIRE k.text IS UNIQUE",
        "CREATE CONSTRAINT ku_id IF NOT EXISTS FOR (u:KnowledgeUnit) REQUIRE u.id IS UNIQUE",
    ]
    for constraint in constraints:
        session.run(constraint)

    session.run("""
        CREATE VECTOR INDEX keyword_embedding IF NOT EXISTS
        FOR (k:Keyword) ON k.embedding
        OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
    """)


def load_taxonomy_rows(pg_cur) -> list[dict]:
    pg_cur.execute("""
        SELECT canonical_keyword, sub_category, root_category, embedding::text
        FROM keyword_taxonomy_map
        ORDER BY root_category, sub_category, canonical_keyword;
    """)
    rows = []
    for canonical_keyword, sub_category, root_category, embedding in pg_cur.fetchall():
        rows.append(
            {
                "canonical_keyword": canonical_keyword,
                "sub_category": sub_category,
                "root_category": root_category,
                "embedding": (
                    [float(value) for value in embedding.strip("[]").split(",")]
                    if embedding is not None
                    else None
                ),
            }
        )
    return rows


def migrate_ontology(session, taxonomy_rows: list[dict]) -> None:
    root_categories = sorted({row["root_category"] for row in taxonomy_rows})
    session.run("UNWIND $roots AS root MERGE (:RootCategory {name: root})", roots=root_categories)

    subcategory_rows = sorted({(row["sub_category"], row["root_category"]) for row in taxonomy_rows})
    session.run(
        """
        UNWIND $subs AS sub
        MERGE (s:SubCategory {name: sub[0]})
        MERGE (r:RootCategory {name: sub[1]})
        MERGE (r)-[:HAS_SUBCATEGORY]->(s)
        """,
        subs=[list(item) for item in subcategory_rows],
    )

    batch_size = 500
    for index in range(0, len(taxonomy_rows), batch_size):
        batch = taxonomy_rows[index:index + batch_size]
        payload = [
            {
                "text": row["canonical_keyword"],
                "sub": row["sub_category"],
                "emb": row["embedding"],
            }
            for row in batch
        ]
        session.run(
            """
            UNWIND $keywords AS keyword
            MERGE (k:Keyword {text: keyword.text})
            SET k.embedding = CASE WHEN keyword.emb IS NOT NULL THEN keyword.emb ELSE k.embedding END
            MERGE (s:SubCategory {name: keyword.sub})
            MERGE (s)-[:HAS_KEYWORD]->(k)
            """,
            keywords=payload,
        )


def migrate_knowledge_units(session, pg_cur) -> None:
    pg_cur.execute("""
        SELECT id, source_type, content_text, explanation
        FROM knowledge_units
        ORDER BY id;
    """)
    units = pg_cur.fetchall()

    batch_size = 500
    for index in range(0, len(units), batch_size):
        batch = units[index:index + batch_size]
        payload = [
            {
                "id": row[0],
                "source_type": row[1] or "",
                "source_ref": "",
                "translation": (row[2] or "")[:2000],
                "explanation": (row[3] or "")[:3000],
            }
            for row in batch
        ]
        session.run(
            """
            UNWIND $units AS unit
            MERGE (ku:KnowledgeUnit {id: unit.id})
            SET ku.source_type = unit.source_type,
                ku.source_ref = unit.source_ref,
                ku.translation = unit.translation,
                ku.explanation = unit.explanation
            """,
            units=payload,
        )

    pg_cur.execute("""
        SELECT knowledge_unit_id, canonical_keyword
        FROM knowledge_units_graph_keywords
        ORDER BY knowledge_unit_id, canonical_keyword;
    """)
    relations = pg_cur.fetchall()
    relation_batch = 2000
    for index in range(0, len(relations), relation_batch):
        batch = relations[index:index + relation_batch]
        payload = [{"uid": row[0], "kw": row[1]} for row in batch]
        session.run(
            """
            UNWIND $relations AS relation
            MATCH (ku:KnowledgeUnit {id: relation.uid})
            MATCH (k:Keyword {text: relation.kw})
            MERGE (ku)-[:TAGGED_WITH]->(k)
            """,
            relations=payload,
        )


def main() -> None:
    print(f"📡 Neo4j: {NEO4J_URI}")

    pg_conn = psycopg2.connect(**DB_PARAMS)
    pg_cur = pg_conn.cursor()
    taxonomy_rows = load_taxonomy_rows(pg_cur)
    print(f"📂 taxonomy row: {len(taxonomy_rows)}")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            clear_graph(session)
            setup_neo4j_schema(session)
            migrate_ontology(session, taxonomy_rows)
            migrate_knowledge_units(session, pg_cur)

            nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]

        print("✅ Neo4j migration tamamlandı.")
        print(f"✅ nodes: {nodes}")
        print(f"✅ relationships: {rels}")
    finally:
        driver.close()
        pg_cur.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
