"""
Graph RAG Taxonomy Categorization Script (v4)
=================================================
5643 adet canonical keyword'ü, önceden belirlenmiş (User Taxonomy) 10 Çatı ve 50 Alt Kategoriye yerleştirir.
JSON Schema / Strict Prompt tekniğiyle Gemini'nin kendi kendine kategori uydurmasını engeller.
Çıktıyı `keyword_category_map` tablosuna kaydeder.
"""

import json
import os
import sys
import time
import psycopg2
from psycopg2.extras import execute_values
from google import genai
from dotenv import load_dotenv
from pathlib import Path

# --- .env yükle ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- AYARLAR ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil.")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

MODEL = "models/gemini-3-flash-preview"
RETRY_LIMIT = 5
RETRY_DELAY = 10
BATCH_SIZE = 100

client = genai.Client(api_key=GEMINI_API_KEY)
TAXONOMY_FILE = PROJECT_ROOT / "data" / "graph_rag_taxonomy.json"
PROGRESS_FILE = PROJECT_ROOT / "data" / "categorization_progress.json"

def load_taxonomy():
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_canonical_keywords():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT canonical_keyword FROM knowledge_units_graph_keywords ORDER BY 1;")
    keywords = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return keywords

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mapped": {}}

def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def build_prompt(batch_keywords, subcategories):
    valid_categories_str = "\n".join(f"- {sc}" for sc in subcategories)
    target_kws_str = "\n".join(f"- {kw}" for kw in batch_keywords)
    
    return f"""Sen bir Türkçe klinik psikoloji ve Graph RAG ontoloji uzmanısın.
Aşağıda "GEÇERLİ ALT KATEGORİLER" listesinde tam olarak 50 adet sabit kategori var.

GÖREV:
"HEDEF KELİMELER" listesindeki her bir psikolojik kavramı, "GEÇERLİ ALT KATEGORİLER" listesindeki EN UYGUN, EN MANTIKLI TEK BİR KATEGORİ ile eşleştir.

KURALLAR (Çok Önemli):
1. ASLA kendi kafandan yeni bir kategori İCAT ETME! Cevabındaki kategori, mutlaka aşağıdaki listedeki kelimelerden birinin BİREBİR AYNISI olmalıdır.
2. Çıktıyı SADECE geçerli bir JSON objesi (dictionary) olarak ver. Anahtar (Key) hedef kelime, Değer (Value) ise seçtiğin geçerli alt kategori adı olsun.
3. Çift tırnaklara dikkat et. Markdown vb ekleme.

GEÇERLİ ALT KATEGORİLER:
{valid_categories_str}

HEDEF KELİMELER:
{target_kws_str}

SADECE JSON FORMATINDA CEVAP VER:
{{
  "İlk Hedef Kelime": "Seçilen Geçerli Alt Kategori",
  "...": "..."
}}
"""

def call_gemini(prompt, valid_subcategories, retry=0):
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            }
        )
        
        text = response.text.strip()
        
        # Temizle JSON formatı için
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            # Fallback for unescaped quotes string handling
            text = text.replace('"\n', '",\n').replace('"\r', '",\r')
            try:
                result = json.loads(text)
            except:
                raise ValueError(f"JSON Parse Error: {e}")
                
        # Validate output against allowed categories
        validated = {}
        for kw, cat in result.items():
            if cat in valid_subcategories:
                validated[kw] = cat
            else:
                # Eger AI "Gelecek ve Rızık Kaygısı" yerine "Gelecek Kaygısı" uydurmuşsa vb fuzzy fallbacks
                best_match = None
                for valid_cat in valid_subcategories:
                    if cat.lower() in valid_cat.lower() or valid_cat.lower() in cat.lower():
                        best_match = valid_cat
                        break
                if best_match:
                    validated[kw] = best_match
                else:
                    print(f"      ⚠️ Geçersiz kategori uyduruldu: '{cat}' for '{kw}', fallback to None")
                    validated[kw] = valid_subcategories[-1] # Put in some default or leave None
        
        return validated
        
    except Exception as e:
        if retry < RETRY_LIMIT:
            print(f"   ⚠️ Hata (retry {retry + 1}/{RETRY_LIMIT}): {e}")
            time.sleep(RETRY_DELAY)
            return call_gemini(prompt, valid_subcategories, retry + 1)
        else:
            print(f"   ❌ {RETRY_LIMIT} denemeden sonra başarısız: {e}")
            return None


def main():
    print("🚀 Graph RAG Kategori Eşleştirme (v4) Başlıyor...")
    
    # 1. Yüklemeler
    taxonomy = load_taxonomy()
    
    # Kök->AltKategori map (Sonrasında veritabanına yazarken root category'yi de bilmek için)
    subcategory_to_root = {}
    valid_subcategories = []
    
    for root, subs in taxonomy.items():
        for sub in subs:
            subcategory_to_root[sub] = root
            valid_subcategories.append(sub)
            
    print(f"📂 {len(taxonomy)} Çatı Kavram, {len(valid_subcategories)} Alt Kategori yüklendi.")
    
    all_keywords = get_canonical_keywords()
    print(f"📂 {len(all_keywords)} Canonical Keyword yüklendi.")
    
    progress = load_progress()
    mapped = progress["mapped"]
    
    # Kalan keywordler
    unmapped_keywords = [kw for kw in all_keywords if kw not in mapped]
    print(f"🎯 Tamamlanan: {len(mapped)}. Kalan: {len(unmapped_keywords)}")
    
    if not unmapped_keywords:
        print("✅ Tüm kelimeler zaten kategorize edilmiş!")
    else:
        # Batch processing
        batches = [unmapped_keywords[i:i + BATCH_SIZE] for i in range(0, len(unmapped_keywords), BATCH_SIZE)]
        total_batches = len(batches)
        
        print(f"\n🔄 {total_batches} Batch (her biri ~{BATCH_SIZE} kelime) işlenecek...")
        
        for idx, batch in enumerate(batches):
            print(f"   [{idx + 1}/{total_batches}] Batch işleniyor ({len(batch)} kelime)...")
            
            prompt = build_prompt(batch, valid_subcategories)
            result = call_gemini(prompt, valid_subcategories)
            
            if result is None:
                print("❌ Script API hatası nedeniyle durduruldu.")
                return
                
            # Update map
            for kw in batch:
                if kw in result:
                    mapped[kw] = result[kw]
                else:
                    # Eşleştirilememişse son çare 1.yi koyma vs ama AI genelde hepsini eşler
                    mapped[kw] = valid_subcategories[0]
                    
            progress["mapped"] = mapped
            save_progress(progress)
            time.sleep(2) # Rate limit
            
    print("\n🗄️ Verilerin Kategorizasyonu Tamamlandı. Veritabanına (Kalıcıya) İki Yeni Tablo Yazılıyor...")
    
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create taxonomy mapping table
    cur.execute("DROP TABLE IF EXISTS keyword_taxonomy_map;")
    cur.execute("""
        CREATE TABLE keyword_taxonomy_map (
            canonical_keyword TEXT PRIMARY KEY,
            root_category TEXT NOT NULL,
            sub_category TEXT NOT NULL
        );
        CREATE INDEX idx_taxonomy_root ON keyword_taxonomy_map(root_category);
        CREATE INDEX idx_taxonomy_sub ON keyword_taxonomy_map(sub_category);
    """)
    
    values = []
    for kw, sub_cat in mapped.items():
        root = subcategory_to_root.get(sub_cat, "Uncategorized")
        values.append((kw, root, sub_cat))
        
    execute_values(
        cur,
        "INSERT INTO keyword_taxonomy_map (canonical_keyword, root_category, sub_category) VALUES %s",
        values,
        page_size=5000
    )
    
    cur.close()
    conn.close()
    
    print(f"✅ Başarıyla `keyword_taxonomy_map` tablosuna {len(values)} kavram kaydedildi!")
    
    # Küçük bir rapor
    from collections import Counter
    sub_counts = Counter(mapped.values())
    print("\n📊 EN ÇOK KELİME DÜŞEN İLK 5 KATEGORİ:")
    for sub, count in sub_counts.most_common(5):
        print(f"   - {sub}: {count} kelime")

if __name__ == "__main__":
    main()
