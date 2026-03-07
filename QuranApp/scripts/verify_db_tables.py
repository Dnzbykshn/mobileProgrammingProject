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

def check_tables():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        print("🔌 Connected to database.")
        
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        if tables:
            print("\n📊 Existing Tables:")
            for table in tables:
                print(f" - {table[0]}")
            
            # Count rows for key tables
            print("\n📈 Row Counts:")
            for table in tables:
                t_name = table[0]
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t_name};")
                    count = cur.fetchone()[0]
                    print(f" - {t_name}: {count} rows")
                except Exception as e:
                    print(f" - {t_name}: Error counting ({e})")
                    conn.rollback() # Reset transaction if error
        else:
            print("\n❌ No tables found in public schema.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error connecting or querying: {e}")

if __name__ == "__main__":
    check_tables()
