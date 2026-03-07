"""
Graph RAG Keyword Normalization Script (v3 - Hybrid NLP + Embedding + LLM)
==========================================================================
Yaklaşım:
1. NLP Phase: Regex ve basit string operasyonlarıyla bariz varyasyonları birleştir.
   (Örn: "-yoksunluğu" -> "-yitimi", "-anksiyetesi" -> "-kaygısı", küçük harf, boşluklar vb.)
2. Embedding Phase: NLP sonrası kalan unique kelimeleri Gemini ile vektörize et.
   Kosinüs benzerliği (Cosine Similarity) çok yüksek olanları (>0.90) grupla.
3. LLM Phase: Sadece oluşan bu küçük "şüpheli kümeleri" (örn: [Öz Güven, Özsaygı]) 
   Gemini'ye gönderip "bunlar aynı mı?" diye sor.

Orijinal veriye DOKUNMAZ. İki yeni tablo oluşturur:
  - keyword_canonical_map
  - knowledge_units_graph_keywords
"""

import json
import os
import sys
import time
import re
import psycopg2
from psycopg2.extras import execute_values
from google import genai
from dotenv import load_dotenv
from pathlib import Path
import numpy as np

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

# Modeller
LLM_MODEL = "models/gemini-3-flash-preview"
EMBEDDING_MODEL = "models/gemini-embedding-001"

client = genai.Client(api_key=GEMINI_API_KEY)


def get_all_keywords():
    print("📂 Veritabanından keyword'ler çekiliyor...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT unnest(keywords) FROM knowledge_units WHERE keywords IS NOT NULL ORDER BY 1;")
    keywords = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    print(f"✅ {len(keywords)} unique keyword bulundu.")
    return keywords


# ==========================================
# PHASE 1: NLP (DETERMINISTIC RULES)
# ==========================================

def nlp_normalize_string(kw: str) -> str:
    """Tek bir string'i kurallara göre normalize eder."""
    # 1. Baş/Son boşlukları al, gereksiz içerik karakterleri temizle
    kw = kw.strip()
    
    # Çoklu boşlukları teke indir
    kw = re.sub(r'\s+', ' ', kw)
    
    # 2. Tireli kelimeleri boşluklu yap (Örn: Öz-Şefkat -> Öz Şefkat)
    kw = kw.replace("-", " ")
    
    # 3. Aynı anlama gelen psikoloji eklerini sabitle (Regex)
    # i tuşu büyük I olursa problem olmaması için case insensitive kullanıyoruz ama 
    # TR harfler bazen sıkıntı çıkarır. Elbette basic bir title() işler.
    
    # Anksiyete -> Kaygı
    kw = re.sub(r'(?i)\banksiyetesi\b', 'Kaygısı', kw)
    kw = re.sub(r'(?i)\banksiyete\b', 'Kaygı', kw)
    
    # İllüzyonu/Yanılsaması/Yanılgısı -> Yanılsaması
    kw = re.sub(r'(?i)\billüzyonu\b', 'Yanılsaması', kw)
    kw = re.sub(r'(?i)\byanılgısı\b', 'Yanılsaması', kw)
    kw = re.sub(r'(?i)\billüzyon\b', 'Yanılsama', kw)
    
    # Yoksunluğu / Eksikliği / Yitimi -> Yoksunluğu
    kw = re.sub(r'(?i)\byitimi\b', 'Yoksunluğu', kw)
    kw = re.sub(r'(?i)\beksikliği\b', 'Yoksunluğu', kw)
    kw = re.sub(r'(?i)\bkaybı\b', 'Yoksunluğu', kw)
    
    # Dissonans / Çelişki / Uyumsuzluk -> Uyumsuzluk
    kw = re.sub(r'(?i)\bdissonans\b', 'Uyumsuzluk', kw)
    kw = re.sub(r'(?i)\bçelişki\b', 'Uyumsuzluk', kw)
    
    # Toleransı / Tahammülü -> Toleransı
    kw = re.sub(r'(?i)\btahammülü\b', 'Toleransı', kw)
    kw = re.sub(r'(?i)tahammül\b', 'Tolerans', kw)
    
    # Sabotaj
    kw = re.sub(r'(?i)oto\s*sabotaj', 'Öz Sabotaj', kw)
    kw = re.sub(r'(?i)kendini\s*sabote\s*etme', 'Öz Sabotaj', kw)
    
    # Katılık
    kw = re.sub(r'(?i)kognitif\b', 'Bilişsel', kw)
    
    # Spelling
    kw = re.sub(r'(?i)grandiyozite', 'Grandiyözite', kw)
    kw = re.sub(r'(?i)makyevelizm', 'Makyavelizm', kw)
    
    # 4. Title case (Her kelimenin ilk harfi büyük)
    # Türkçe I/i problemi için özel bir fonksiyon yazılabilir ama basic title yeterli:
    kw_words = kw.split()
    capitalized_words = []
    for w in kw_words:
        # TR harf düzeltmeleri manuel (çok basitçe)
        if len(w) > 0:
            first = w[0].upper()
            if first == 'I': first = 'I'
            if first == 'i': first = 'İ'
            rest = w[1:].lower()
            capitalized_words.append(first + rest)
    
    return " ".join(capitalized_words)


def phase1_nlp(keywords):
    print("\n" + "="*50)
    print("📍 PHASE 1: NLP Rules & Regex Normalization")
    print("="*50)
    
    nlp_map = {}
    for kw in keywords:
        nlp_map[kw] = nlp_normalize_string(kw)
        
    unique_after_nlp = set(nlp_map.values())
    print(f"📊 Orijinal keyword: {len(keywords)}")
    print(f"📊 NLP sonrası unique: {len(unique_after_nlp)}")
    print(f"📉 Azalma: {len(keywords) - len(unique_after_nlp)} kelime eşleştirildi.")
    
    return nlp_map, list(unique_after_nlp)


# ==========================================
# PHASE 2: EMBEDDING & CLUSTERING
# ==========================================

def get_embeddings_batch(texts):
    """Metin listesinin vektörlerini Gemini API'den alır."""
    # Batch size limiti (örn 100) için parçalayalım
    BATCH_SIZE = 100
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            time.sleep(1) # Rate limiting
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config={"output_dimensionality": 768}
            )
            
            # API liste dönüyor
            for emb in result.embeddings:
                all_embeddings.append(emb.values)
                
            print(f"   ... Vektörize edildi: {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
        except Exception as e:
            print(f"   ❌ Embedding hatası: {e}")
            sys.exit(1)
            
    return all_embeddings

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def phase2_embeddings(unique_keywords):
    print("\n" + "="*50)
    print("📍 PHASE 2: AI Embeddings & Cosine Clustering")
    print("="*50)
    
    # 1. Her unique keyword için vektör oluştur
    print("🧠 Vektörler çıkarılıyor (Gemini Embedding API)...")
    embeddings = get_embeddings_batch(unique_keywords)
    
    # 2. Benzerlik Matrisi oluştur ve Kümele (>0.94 vs)
    THRESHOLD = 0.93  # Çok yüksek eşik, sadece aynı anlama gelenler geçsin.
    print(f"🔍 Birbirine en az %{int(THRESHOLD*100)} benzeyen kelimeler kümeleniyor...")
    
    clusters = []
    visited_indices = set()
    
    for i in range(len(unique_keywords)):
        if i in visited_indices:
            continue
            
        current_cluster = [unique_keywords[i]]
        visited_indices.add(i)
        
        for j in range(i + 1, len(unique_keywords)):
            if j in visited_indices:
                continue
                
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= THRESHOLD:
                current_cluster.append(unique_keywords[j])
                visited_indices.add(j)
                
        if len(current_cluster) > 1:
            clusters.append(current_cluster)
            
    # Gruplanmamış (yalnız kalan) kelimeleri de kendi cluster'ı olarak ekle,
    # ama onlar LLM'ye gitmeyecek.
    unclustered = [unique_keywords[i] for i in range(len(unique_keywords)) if i not in visited_indices]
    
    for kw in unclustered:
        clusters.append([kw]) # Single item cluster
        
    print(f"📊 {len(unique_keywords)} kelimeden, {len(clusters)} küme oluştu.")
    multi_item_clusters = [c for c in clusters if len(c) > 1]
    print(f"   👉 {len(multi_item_clusters)} adet şüpheli çoklu küme var. (Kalanlar tektir).")
    
    return clusters


# ==========================================
# PHASE 3: LLM FINAL JUDGEMENT
# ==========================================

def resolve_cluster_with_llm(cluster):
    """
    Örn input: ["Aidiyet Duygusu", "Aidiyet Hissi", "Aidiyet İhtiyacı"]
    LLM'ye "bunların hepsi aynı mı? Eğer aynıysa tek bir tane seç. Farklı olanları ayır" der.
    Return: {"Aidiyet Duygusu": "Aidiyet", "Aidiyet Hissi": "Aidiyet", "Aidiyet İhtiyacı": "Aidiyet İhtiyacı"}
    """
    cluster_str = "\n".join(f"- {kw}" for kw in cluster)
    prompt = f"""Sen bir Türkçe psikoloji terminolojisi uzmanısın.
Aşağıdaki kelimeler vektörel olarak birbirine çok benzediği için aynı grupta toplandı.
Görev: Bu kelimelerin GERÇEKTEN aynı psikolojik konsepti ifade edip etmediğine karar ver.

KELİMELER:
{cluster_str}

Kurallar:
1. Eğer kelimeler %100 aynı konsepti yansıtıyorsa, aralarından EN TEMEL ve DOĞRU Türkçe olanını "canonical" (kanonik) olarak seç. Tüm aynı olanları bu "canonical" kelimeye eşle.
2. Eğer gruptaki bir kelime, diğerlerinden FARKLI bir konsept ise (çok benziyor olsa bile nüans farkı varsa, örneğin "Algı Alanı" ile "Algı Kapanması" farklıdır), onu kendi haline bırak, orijinali canonical olsun.
3. Çıktıyı kesinlikle JSON formatında Dictionary {"{eski_kelime: canonical_kelime, ...}"} olarak ver, başına/sonuna (markdown) bir şey ekleme. 

SADECE geçerli JSON objesi ver:
{{
  "İlk kelime": "Seçilen Canonical",
  "İkinci Kelime": "Seçilen Canonical (eğer aynıysa)"
}}
"""
    try:
        time.sleep(2) # Rate limit
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            }
        )
        text = response.text.strip()
        
        # Temizlik: Markdown bloklarını uçur (eğer model response_mime_type takmazsa diye)
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        print(f"      ⚠️ LLM başarısız: {e}, varsayılan olarak ilk kelimeyi alıyorum.")
        # Fallback: hepsini grubun ilk elemanına ata (cosine desteksiz de kurtarmak için)
        return {kw: cluster[0] for kw in cluster}


def phase3_llm_resolution(clusters):
    print("\n" + "="*50)
    print("📍 PHASE 3: LLM Final Hakemlik")
    print("="*50)
    
    final_canonical_map_from_clusters = {}
    
    # Sadece birden fazla elemanı olan (anlaşmazlık olan) kümeleri LLM'ye yolla
    multi_clusters = [c for c in clusters if len(c) > 1]
    single_clusters = [c for c in clusters if len(c) == 1]
    
    # Teklileri zaten kendilerine map'le
    for c in single_clusters:
        final_canonical_map_from_clusters[c[0]] = c[0]
        
    print(f"🤖 LLM'ye {len(multi_clusters)} adet şüpheli küme gönderiliyor...")
    
    for idx, cluster in enumerate(multi_clusters):
        print(f"   [{idx+1}/{len(multi_clusters)}] İnceleniyor: {', '.join(cluster[:3])}...")
        resolved_dict = resolve_cluster_with_llm(cluster)
        
        # Gelen kararları ana listeye ekle
        for kw in cluster:
            if kw in resolved_dict:
                final_canonical_map_from_clusters[kw] = resolved_dict[kw]
            else:
                # LLM unuttuysa kendini dön
                final_canonical_map_from_clusters[kw] = kw
                
    return final_canonical_map_from_clusters


# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    print("🚀 NLP/Vektör Hibrit Graph RAG Keyword Normalizasyonu Başlıyor!")
    
    # 0. Veriyi çek
    raw_keywords = get_all_keywords()
    
    # 1. NLP ile temizle (Hızlı kural tabanlı birleştirme)
    # nlp_map: {"Varoluşsal Kaygısı": "Varoluşsal Kaygı", ...}
    nlp_map, unique_after_nlp = phase1_nlp(raw_keywords)
    
    # 2. Embedding Cluster (Benzerleri bulma)
    # clusters: [["Varoluşsal Kaygı", "Varoluşsal Anksiyete"], ["Öz Şefkat"], ...]
    clusters = phase2_embeddings(unique_after_nlp)
    
    # 3. LLM Resolution (Hakem kararı)
    # llm_map: {"Varoluşsal Anksiyete": "Varoluşsal Kaygı", "Varoluşsal Kaygı": "Varoluşsal Kaygı"}
    llm_map = phase3_llm_resolution(clusters)
    
    # 4. Mapleri Birleştir (Raw -> NLP -> LLM)
    final_raw_to_canonical = {}
    for raw_kw in raw_keywords:
        nlp_kw = nlp_map[raw_kw]
        canonical_kw = llm_map.get(nlp_kw, nlp_kw)
        final_raw_to_canonical[raw_kw] = canonical_kw
        
    # 5. DB Yazma (Tablolar)
    print("\n🗄️ Veritabanına (Kalıcıya) İki Yeni Tablo Yazılıyor...")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    
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
    values = [(orig, canon) for orig, canon in final_raw_to_canonical.items()]
    execute_values(
        cur,
        "INSERT INTO keyword_canonical_map (original_keyword, canonical_keyword) VALUES %s",
        values
    )
    
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
    for unit_id, kws in rows:
        if kws:
            for kw in kws:
                canon = final_raw_to_canonical.get(kw, kw)
                graph_values.append((unit_id, canon))
                
    execute_values(
        cur,
        "INSERT INTO knowledge_units_graph_keywords (knowledge_unit_id, canonical_keyword) VALUES %s",
        graph_values,
        page_size=5000
    )
    cur.close()
    conn.close()
    
    # 6. Rapor
    unique_final = set(final_raw_to_canonical.values())
    print("\n" + "="*50)
    print("✅ BÜTÜN İŞLEMLER BAŞARIYLA TAMAMLANDI!")
    print(f"📊 Başlangıç Keyword Sayısı : {len(raw_keywords)}")
    print(f"📊 Bitiş Canonical Sayısı   : {len(unique_final)}")
    print(f"📉 Düşüş                    : %{100 - (len(unique_final)/len(raw_keywords)*100):.1f}")
    
    # En çok daralan top 5 grubu bulalım
    grouped = {}
    for raw, canon in final_raw_to_canonical.items():
        if raw != canon:
            grouped.setdefault(canon, []).append(raw)
            
    print("\n🔝 ÖRNEK BİRLEŞTİRMELER:")
    for canon, raw_list in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"   [ {canon} ]  <--  {', '.join(raw_list)}")

if __name__ == "__main__":
    main()
