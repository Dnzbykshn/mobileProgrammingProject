"""
Graph RAG Keyword Normalization Script (v2 - Optimized)
========================================================
Tüm 6308 keyword'ü Gemini'nin 1M input context'ine sığdırır.
Output'u harf aralıklarına bölerek alır.
Her çağrıda Gemini TÜM keyword listesini gördüğü için cross-batch tutarlılık garanti.

Orijinal veriye DOKUNMAZ. İki yeni tablo oluşturur:
  - keyword_canonical_map: variant → canonical eşleme
  - knowledge_units_graph_keywords: normalize edilmiş ayet-keyword ilişkileri
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

# --- .env yükle (proje kökünden) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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

MODEL = "models/gemini-3-flash-preview"
RETRY_LIMIT = 3
RETRY_DELAY = 15

client = genai.Client(api_key=GEMINI_API_KEY)

# --- Checkpoint ---
PROGRESS_FILE = PROJECT_ROOT / "data" / "normalization_progress_v2.json"

# Harf aralıkları (Türkçe alfabe uyumlu)
LETTER_RANGES = [
    ("A", "B"),   # A ile başlayanlar
    ("B", "C"),   # B ile başlayanlar  
    ("C", "D"),   # C, Ç ile başlayanlar
    ("D", "E"),   # D ile başlayanlar
    ("E", "F"),   # E ile başlayanlar
    ("F", "G"),   # F ile başlayanlar
    ("G", "H"),   # G ile başlayanlar
    ("H", "J"),   # H, I, İ ile başlayanlar
    ("J", "L"),   # J, K ile başlayanlar
    ("L", "N"),   # L, M ile başlayanlar
    ("N", "P"),   # N, O, Ö ile başlayanlar
    ("P", "S"),   # P, R ile başlayanlar
    ("S", "T"),   # S, Ş ile başlayanlar
    ("T", "V"),   # T, U, Ü ile başlayanlar
    ("V", "ZZZ"), # V, Y, Z ile başlayanlar
]


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"📂 Önceki progress yüklendi: {data['completed_ranges']} range tamamlanmış.")
            return data
    return {
        "completed_ranges": [],
        "canonical_map": {},
    }


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def get_all_keywords():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT unnest(keywords) FROM knowledge_units ORDER BY 1;")
    keywords = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return keywords


def filter_keywords_by_range(keywords, start, end):
    """Belirli harf aralığındaki keyword'leri filtrele."""
    return [kw for kw in keywords if start.upper() <= kw[0].upper() < end.upper()]


def call_gemini(prompt, retry=0):
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
        
        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON Parse Error: {e}. Trying to fix common issues...")
            # Try to fix unescaped quotes inside values
            text = text.replace('"\n', '",\n').replace('"\r', '",\r')
            try:
                result = json.loads(text)
            except:
                raise ValueError(f"Could not parse JSON. Raw text: {text[:200]}...")
        
        if not isinstance(result, list):
            raise ValueError(f"Response is not a JSON array: {text[:200]}")
        
        return result
        
    except Exception as e:
        if retry < RETRY_LIMIT:
            print(f"   ⚠️ Hata (retry {retry + 1}/{RETRY_LIMIT}): {e}")
            time.sleep(RETRY_DELAY * (retry + 1))
            return call_gemini(prompt, retry + 1)
        else:
            print(f"   ❌ {RETRY_LIMIT} denemeden sonra başarısız: {e}")
            return None


def build_prompt(all_keywords, target_keywords):
    """
    all_keywords: tüm 6308 keyword (context olarak)
    target_keywords: bu çağrıda normalize edilecek keyword'ler
    """
    full_list = "\n".join(all_keywords)
    target_list = "\n".join(f"- {kw}" for kw in target_keywords)
    
    return f"""Sen bir Türkçe psikoloji ve felsefe terminolojisi uzmanısın.

GÖREV: Aşağıda "TÜM KEYWORD LİSTESİ" bölümünde veritabanındaki tüm keyword'leri göreceksin.
"HEDEF KEYWORD'LER" bölümündeki keyword'leri normalize et.

Hedef keyword'lerin her biri için:
1. TÜM LİSTEDEKİ diğer keyword'lere bak
2. Eşanlamlı/varyant olan keyword'leri tespit et  
3. En uygun kanonik (canonical) formu belirle — AYNI konseptin tüm varyantları AYNI canonical forma eşlenmeli

Normalizasyon kuralları:
- Türkçe karşılık tercih et (Anksiyete → Kaygı, Dissonans → Uyumsuzluk, İllüzyon → Yanılsama)
- Kısa tire kullanma, boşluk kullan (Öz-Şefkat → Öz Şefkat)
- Aynı konsepti ifade eden farklı tamlamaları birleştir (Kontrol İllüzyonu, Kontrol Yanılsaması → Kontrol Yanılsaması)
- Bireyleşme/Bireyselleşme gibi kavramsal farklarda psikolojide doğru formu seç
- -e Tahammül/-e Tolerans gibi eşanlamlıları birleştir
- Korkusu / Kaygısı / Anksiyetesi kelimeleri tamlama içinde eşanlamlıysa aynı sonuca bağla (Ayrılık Kaygısı, Ayrılık Anksiyetesi → Ayrılık Kaygısı)
- Yitimi / Yoksunluğu / Eksikliği / Kaybı kelimeleri kavram sonuna geliyorsa eşanlamlı say ve birleştir (Örn: Aşkınlık Yitimi, Aşkınlık Yoksunluğu → Aşkınlık Yoksunluğu)
- Grandiyözite/Grandiyozite, Makyavelizm/Makyevelizm gibi basit yazım farklarını mutlaka aynı sonuca eşle.
- Eğer keyword zaten en uygun formundaysa, canonical = original olarak döndür

⚠️ ÇOK ÖNEMLİ: Aynı konseptin farklı varyantları mutlaka AYNI canonical forma eşlenmeli.
Örneğin "Varoluşsal Kaygı" ve "Varoluşsal Anksiyete" ikisi de → "Varoluşsal Kaygı"
"Ontolojik Güven" ve "Ontolojik Güvenlik" ikisi de → "Ontolojik Güven"

TÜM KEYWORD LİSTESİ (sadece referans, hepsini normalize etme):
{full_list}

HEDEF KEYWORD'LER (sadece bunları normalize et):
{target_list}

SADECE geçerli bir JSON array döndür.
Bütün anahtarları (key) ve değerleri (value) ÇİFT TIRNAK (" ") içine almalısın. İçerideki çift tırnakları escape (\\") yapmayı unutma.
Örnek Format:
[
  {{"original": "Varoluşsal Kaygı", "canonical": "Varoluşsal Kaygı"}},
  {{"original": "Varoluşsal Anksiyete", "canonical": "Varoluşsal Kaygı"}}
]
"""


def phase1_normalize(all_keywords, progress):
    """Harf aralıklarına göre normalize et, her çağrıda tüm listeyi context olarak gönder."""
    canonical_map = progress["canonical_map"]
    completed = set(progress["completed_ranges"])
    
    # Sub-batch boyutu: max 100 keyword per API call
    SUB_BATCH_SIZE = 100
    
    total_ranges = len(LETTER_RANGES)
    
    print(f"\n📊 Toplam {len(all_keywords)} keyword, {total_ranges} harf aralığı")
    
    for idx, (start, end) in enumerate(LETTER_RANGES):
        range_key = f"{start}-{end}"
        
        if range_key in completed:
            print(f"   ⏭️ Aralık {idx + 1}/{total_ranges} [{range_key}]: zaten tamamlanmış")
            continue
        
        target_keywords = filter_keywords_by_range(all_keywords, start, end)
        
        if not target_keywords:
            print(f"   ⏭️ Aralık {idx + 1}/{total_ranges} [{range_key}]: keyword yok")
            completed.add(range_key)
            progress["completed_ranges"] = sorted(completed)
            save_progress(progress)
            continue
        
        # Zaten map'te olanları çıkar
        new_keywords = [kw for kw in target_keywords if kw not in canonical_map]
        
        if not new_keywords:
            print(f"   ⏭️ Aralık {idx + 1}/{total_ranges} [{range_key}]: tüm keyword'ler zaten eşlenmiş")
            completed.add(range_key)
            progress["completed_ranges"] = sorted(completed)
            save_progress(progress)
            continue
        
        # Sub-batch'lere böl
        sub_batches = [new_keywords[i:i + SUB_BATCH_SIZE] for i in range(0, len(new_keywords), SUB_BATCH_SIZE)]
        total_subs = len(sub_batches)
        
        print(f"\n🔄 Aralık {idx + 1}/{total_ranges} [{range_key}]: {len(new_keywords)} keyword, {total_subs} sub-batch")
        
        range_normalized = 0
        range_canonical = 0
        
        for sub_idx, sub_batch in enumerate(sub_batches):
            print(f"      Sub-batch {sub_idx + 1}/{total_subs}: {len(sub_batch)} keyword...")
            
            prompt = build_prompt(all_keywords, sub_batch)
            result = call_gemini(prompt)
            
            if result is None:
                print(f"   ❌ Sub-batch başarısız. Progress kaydedildi, script'i tekrar çalıştırın.")
                save_progress(progress)
                return False
            
            for item in result:
                original = item.get("original", "").strip()
                canonical = item.get("canonical", "").strip()
                if original and canonical:
                    canonical_map[original] = canonical
                    if original != canonical:
                        range_normalized += 1
                    else:
                        range_canonical += 1
            
            # Her sub-batch sonrası checkpoint
            progress["canonical_map"] = canonical_map
            save_progress(progress)
            
            time.sleep(3)
        
        print(f"   ✅ [{range_key}] {range_normalized} normalize, {range_canonical} canonical")
        
        completed.add(range_key)
        progress["completed_ranges"] = sorted(completed)
        save_progress(progress)
    
    return True


def phase2_dedup(progress):
    """Canonical formlar arasında son kontrol."""
    canonical_map = progress["canonical_map"]
    canonical_set = sorted(set(canonical_map.values()))
    
    print(f"\n🔍 {len(canonical_set)} unique canonical form dedup kontrolü...")
    
    # 500'lük batch'ler
    batches = [canonical_set[i:i + 500] for i in range(0, len(canonical_set), 500)]
    
    dedup_map = {}
    
    for batch_idx, batch in enumerate(batches):
        print(f"   🔄 Dedup batch {batch_idx + 1}/{len(batches)}...")
        
        kw_list = "\n".join(f"- {kw}" for kw in batch)
        
        prompt = f"""Sen bir Türkçe psikoloji terminolojisi uzmanısın.
Aşağıdaki kanonik keyword listesinde hâlâ birbirine çok benzeyen veya aynı anlama gelen 
terimler var mı kontrol et.

KEYWORD LİSTESİ:
{kw_list}

Eğer eşanlamlı/duplicate olanlar varsa bunları birleştir:
[{{"original": "eski_form", "canonical": "doğru_form"}}, ...]

Eğer hiç duplicate yoksa: []

Kurallar:
- Sadece GERÇEKTEN aynı anlama gelenleri birleştir
- Nüans farkı olanları AYRI TUT  
- Türkçe formu tercih et
- Kısa tire kullanma
"""
        
        result = call_gemini(prompt)
        
        if result:
            for item in result:
                old = item.get("original", "").strip()
                new = item.get("canonical", "").strip()
                if old and new and old != new and old in set(canonical_map.values()):
                    dedup_map[old] = new
        
        time.sleep(3)
    
    if dedup_map:
        print(f"\n   🔧 {len(dedup_map)} canonical birleştirildi:")
        for old, new in sorted(dedup_map.items()):
            print(f"      {old} → {new}")
        
        for original in canonical_map:
            canonical = canonical_map[original]
            # Chain resolution: a → b → c  ise a → c olmalı
            while canonical in dedup_map:
                canonical = dedup_map[canonical]
            canonical_map[original] = canonical
        
        progress["canonical_map"] = canonical_map
        save_progress(progress)
    else:
        print("   ✅ Duplicate bulunamadı!")


def write_to_db(progress):
    canonical_map = progress["canonical_map"]
    
    print("\n🗄️ Veritabanına yazılıyor...")
    
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. keyword_canonical_map
    print("   📋 keyword_canonical_map tablosu oluşturuluyor...")
    cur.execute("DROP TABLE IF EXISTS knowledge_units_graph_keywords;")
    cur.execute("DROP TABLE IF EXISTS keyword_canonical_map;")
    cur.execute("""
        CREATE TABLE keyword_canonical_map (
            id SERIAL PRIMARY KEY,
            original_keyword TEXT NOT NULL UNIQUE,
            canonical_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_canonical_keyword ON keyword_canonical_map(canonical_keyword);
    """)
    
    values = [(orig, canon) for orig, canon in canonical_map.items()]
    execute_values(
        cur,
        "INSERT INTO keyword_canonical_map (original_keyword, canonical_keyword) VALUES %s",
        values
    )
    print(f"   ✅ {len(values)} keyword eşlemesi kaydedildi.")
    
    # 2. knowledge_units_graph_keywords
    print("   📋 knowledge_units_graph_keywords tablosu oluşturuluyor...")
    cur.execute("""
        CREATE TABLE knowledge_units_graph_keywords (
            id SERIAL PRIMARY KEY,
            knowledge_unit_id INTEGER NOT NULL REFERENCES knowledge_units(id),
            canonical_keyword TEXT NOT NULL
        );
        CREATE INDEX idx_graph_kw_unit ON knowledge_units_graph_keywords(knowledge_unit_id);
        CREATE INDEX idx_graph_kw_keyword ON knowledge_units_graph_keywords(canonical_keyword);
    """)
    
    cur.execute("SELECT id, keywords FROM knowledge_units WHERE keywords IS NOT NULL;")
    rows = cur.fetchall()
    
    graph_values = []
    unmapped = set()
    
    for unit_id, keywords in rows:
        if keywords:
            for kw in keywords:
                canonical = canonical_map.get(kw, kw)
                if kw not in canonical_map:
                    unmapped.add(kw)
                graph_values.append((unit_id, canonical))
    
    if unmapped:
        print(f"   ⚠️ {len(unmapped)} keyword canonical map'te bulunamadı (kendilerine eşlendi)")
    
    execute_values(
        cur,
        "INSERT INTO knowledge_units_graph_keywords (knowledge_unit_id, canonical_keyword) VALUES %s",
        graph_values,
        page_size=5000
    )
    print(f"   ✅ {len(graph_values)} ayet-keyword ilişkisi kaydedildi.")
    
    cur.close()
    conn.close()


def print_report(progress):
    canonical_map = progress["canonical_map"]
    unique_canonicals = set(canonical_map.values())
    
    total = len(canonical_map)
    canons = len(unique_canonicals)
    merged = total - canons
    
    # En çok varyantı olan gruplar
    groups = {}
    for orig, canon in canonical_map.items():
        if orig != canon:
            groups.setdefault(canon, []).append(orig)
    
    print("\n" + "=" * 60)
    print("📊 NORMALIZASYON RAPORU")
    print("=" * 60)
    print(f"   Orijinal keyword:   {total}")
    print(f"   Canonical keyword:  {canons}")
    print(f"   Birleştirilen:      {merged} ({merged/total*100:.1f}%)")
    print()
    
    if groups:
        top = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        print("🔝 En çok varyantı olan 20 canonical:")
        for canon, variants in top[:20]:
            print(f"   {canon} ← {', '.join(variants)}")
    
    print("\n✅ Tamamlandı!")


def main():
    print("🚀 Graph RAG Keyword Normalization v2 Başlıyor...")
    print(f"   Model: {MODEL}")
    
    print("\n📂 Keyword'ler çekiliyor...")
    all_keywords = get_all_keywords()
    print(f"   {len(all_keywords)} unique keyword bulundu.")
    
    progress = load_progress()
    
    print("\n" + "=" * 50)
    print("📍 AŞAMA 1: Keyword Normalizasyonu (Harf Aralıkları)")
    print("=" * 50)
    
    success = phase1_normalize(all_keywords, progress)
    if not success:
        print("\n❌ Tamamlanamadı. Script'i tekrar çalıştırarak kaldığı yerden devam edebilirsiniz.")
        return
    
    print("\n" + "=" * 50)
    print("📍 AŞAMA 2: Deduplication Kontrolü")
    print("=" * 50)
    
    phase2_dedup(progress)
    
    print("\n" + "=" * 50)
    print("📍 AŞAMA 3: Veritabanına Yazma")
    print("=" * 50)
    
    write_to_db(progress)
    
    print_report(progress)


if __name__ == "__main__":
    main()
