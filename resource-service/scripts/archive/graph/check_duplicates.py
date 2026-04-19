import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path
from itertools import combinations

# Load env
PROJECT_ROOT = Path(r"c:\Users\deniz\Desktop\QuranApp")
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

def jaccard_similarity(str1, str2):
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def main():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT canonical_keyword FROM knowledge_units_graph_keywords ORDER BY 1;")
    keywords = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    print(f"Total unique canonicals: {len(keywords)}")
    
    # Check for simple substring inclusions or high Jaccard similarity (word overlap)
    # Since checking 5643^2 is 15M comparisons, we can do it quickly in python
    suspicious_pairs = []
    
    # Sort by length so we can find things like "Kaygı" vs "Gelecek Kaygısı" if needed
    # But let's just do an N^2 check on Jaccard similarity > 0.66 (e.g., 2 out of 3 words match)
    
    for i in range(len(keywords)):
        kw1 = keywords[i]
        set1 = set(kw1.lower().split())
        if len(set1) == 0: continue
            
        for j in range(i + 1, len(keywords)):
            kw2 = keywords[j]
            set2 = set(kw2.lower().split())
            if len(set2) == 0: continue
                
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            sim = len(intersection) / len(union)
            
            # If 2 out of 3 words are exactly the same
            if sim >= 0.70:
                suspicious_pairs.append((sim, kw1, kw2))

    suspicious_pairs.sort(reverse=True)
    
    print(f"Found {len(suspicious_pairs)} highly similar pairs (word overlap >= 70%):")
    for sim, k1, k2 in suspicious_pairs[:30]:
         print(f"[{sim:.2f}] '{k1}'  vs  '{k2}'")
         
if __name__ == "__main__":
    main()
