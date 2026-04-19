import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

CORE_TABLES = [
    "knowledge_units",
    "esma_ul_husna",
    "prophet_duas",
    "prayer_districts",
    "prayer_times",
    "keyword_canonical_map",
    "knowledge_units_graph_keywords",
    "keyword_taxonomy_map",
]


def print_postgres_summary() -> None:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    print("PostgreSQL")
    for table in CORE_TABLES:
        cur.execute("SELECT to_regclass(%s);", (f"public.{table}",))
        exists = cur.fetchone()[0] is not None
        if not exists:
            print(f"- {table}: eksik")
            continue

        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"- {table}: {count}")

    cur.execute("SELECT to_regclass('public.knowledge_units_graph_keywords');")
    if cur.fetchone()[0] is not None:
        cur.execute("SELECT COUNT(DISTINCT canonical_keyword) FROM knowledge_units_graph_keywords;")
        distinct_keywords = cur.fetchone()[0]
        print(f"- graph canonical keyword: {distinct_keywords}")

    cur.close()
    conn.close()


def print_neo4j_summary() -> None:
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("\nNeo4j")
        print("- neo4j paketi kurulu değil, kontrol atlandı")
        return

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        print("\nNeo4j")
        print("- NEO4J_PASSWORD yok, kontrol atlandı")
        return

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            try:
                indexes = session.run(
                    "SHOW VECTOR INDEXES YIELD name, state RETURN name, state ORDER BY name"
                ).data()
            except Exception:
                indexes = []
        print("\nNeo4j")
        print(f"- nodes: {nodes}")
        print(f"- relationships: {rels}")
        if indexes:
            for item in indexes:
                print(f"- vector index {item['name']}: {item['state']}")
        else:
            print("- vector index: yok")
    finally:
        driver.close()


if __name__ == "__main__":
    print_postgres_summary()
    print_neo4j_summary()
