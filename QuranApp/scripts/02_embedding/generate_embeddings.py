"""
Embedding Generator - batch_results_merged.jsonl'dan embedding üretir.
Gemini Embedding API kullanarak senkron işlem yapar (batch desteklenmiyor).
"""

import json
import os
import sys
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- AYARLAR ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")
MERGED_RESULTS = "data/batch_results_merged.jsonl"
INPUT_DATA = "data/quran_final_pristine.json"
OUTPUT_FILE = "data/embeddings_768.jsonl"  # Yeni dosya - 768 boyut
EMBEDDING_MODEL = "gemini-embedding-001"
OUTPUT_DIMENSION = 768  # HNSW için 768 boyut

# Rate limit ayarları
REQUESTS_PER_MINUTE = 1000  # Embedding modeli çok yüksek limite sahip
BATCH_SIZE = 100  # Her seferde 100 embedding

def main():
    print("🚀 Embedding Üretimi Başlıyor...")
    
    # Client oluştur
    client = genai.Client(api_key=API_KEY)
    
    # 1. Orijinal veriyi yükle
    print(f"📂 '{INPUT_DATA}' okunuyor...")
    with open(INPUT_DATA, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    # Key -> index mapping
    key_to_index = {}
    for i, doc in enumerate(dataset):
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        key_to_index[key] = i
    
    # 2. Merged sonuçları oku ve dataset'e ekle
    print(f"📂 '{MERGED_RESULTS}' okunuyor...")
    with open(MERGED_RESULTS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            result = json.loads(line)
            key = result.get('key', '')
            
            try:
                response = result.get('response', {})
                candidates = response.get('candidates', [])
                if not candidates:
                    continue
                
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if not parts:
                    continue
                
                text_content = None
                for part in parts:
                    if 'text' in part:
                        text_content = part.get('text', '')
                        break
                
                if not text_content:
                    continue
                
                parsed = json.loads(text_content)
                keywords = parsed.get('keywords', [])
                explanation = parsed.get('explanation', '')
                
                if key in key_to_index:
                    idx = key_to_index[key]
                    dataset[idx]['search_content']['keywords'] = keywords
                    dataset[idx]['semantic_content']['explanation'] = explanation
            except:
                continue
    
    # 3. Embedding için metinleri hazırla
    print("📝 Embedding metinleri hazırlanıyor...")
    embedding_data = []
    
    for doc in dataset:
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        
        keywords = doc['search_content'].get('keywords', [])
        if not keywords:
            continue
        
        tr_text = doc['display'].get('turkish_text', '')
        keywords_text = " ".join(keywords)
        explanation = doc['semantic_content'].get('explanation', '')
        
        text_to_embed = f"{tr_text} {keywords_text} {explanation}"
        
        embedding_data.append({
            "key": key,
            "text": text_to_embed
        })
    
    print(f"✅ {len(embedding_data)} ayet embedding için hazır.")
    
    # 4. Mevcut ileremeyi yükle (devam etmek için)
    existing_keys = set()
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    existing_keys.add(data.get('key', ''))
        print(f"📂 {len(existing_keys)} mevcut embedding bulundu, kaldığı yerden devam ediliyor...")
    except FileNotFoundError:
        print("📂 Yeni dosya oluşturuluyor...")
    
    # 5. Embedding üret
    print(f"\n🔄 Embedding üretimi başlıyor (Model: {EMBEDDING_MODEL})...")
    
    results = []
    total = len(embedding_data)
    skipped = 0
    
    # Dosyayı append modunda aç
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for i, item in enumerate(embedding_data):
            # Zaten işlenmiş mi kontrol et
            if item["key"] in existing_keys:
                skipped += 1
                continue
            
            try:
                # Retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.embed_content(
                            model=f"models/{EMBEDDING_MODEL}",
                            contents=item["text"],
                            config={"output_dimensionality": OUTPUT_DIMENSION}
                        )
                        break
                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            time.sleep(wait_time)
                        else:
                            raise retry_error
                
                embedding = response.embeddings[0].values
                
                result = {
                    "key": item["key"],
                    "embedding": embedding
                }
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
                f.flush()  # Hemen diske yaz
                results.append(result)
                
                processed = len(existing_keys) + len(results)
                if processed % 100 == 0:
                    print(f"   💾 {processed}/{total} tamamlandı...")
                
                # Rate limit için küçük bekleme
                if len(results) % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"   ⚠️ {item['key']}: Hata - {e}")
                time.sleep(3)  # Hata durumunda biraz bekle
    
    print(f"\n🎉 TAMAMLANDI!")
    print(f"✅ {len(results)} embedding üretildi.")
    print(f"📄 Sonuçlar '{OUTPUT_FILE}' dosyasına kaydedildi.")
    print(f"\n🚀 Sonraki adım: 'python final_db_insert.py' çalıştırın.")

if __name__ == "__main__":
    main()
