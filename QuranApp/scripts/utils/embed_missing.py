"""
Eksik 9 ayetin embedding'ini üretir.
Bu ayetler array formatında JSON döndüğü için parse edilememişti.
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
ANALYSIS_RESULTS = "data/batch_results_merged.jsonl"
INPUT_DATA = "data/quran_final_pristine.json"
OUTPUT_FILE = "data/embeddings_768.jsonl"
EMBEDDING_MODEL = "gemini-embedding-001"
OUTPUT_DIMENSION = 768

# Eksik ayetler
MISSING_KEYS = ["3_139", "4_54", "23_100", "24_15", "30_46", "34_2", "35_44", "81_23", "90_15"]

def main():
    print("🔍 Eksik 9 ayet için embedding üretiliyor...\n")
    
    client = genai.Client(api_key=API_KEY)
    
    # Orijinal veriyi yükle
    with open(INPUT_DATA, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    key_to_doc = {}
    for doc in dataset:
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        key_to_doc[key] = doc
    
    # Batch sonuçlarından eksik ayetleri bul
    print("📂 Batch sonuçları okunuyor...")
    missing_data = {}
    
    with open(ANALYSIS_RESULTS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            result = json.loads(line)
            key = result.get('key', '')
            
            if key not in MISSING_KEYS:
                continue
            
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
                
                # JSON parse - array formatını handle et
                parsed = json.loads(text_content)
                if isinstance(parsed, list):
                    parsed = parsed[0] if parsed else {}
                
                keywords = parsed.get('keywords', [])
                explanation = parsed.get('explanation', '')
                
                if keywords:
                    missing_data[key] = {
                        'keywords': keywords,
                        'explanation': explanation
                    }
                    print(f"   ✅ {key}: {len(keywords)} keyword bulundu")
            except Exception as e:
                print(f"   ❌ {key}: Parse hatası - {e}")
    
    print(f"\n📊 {len(missing_data)}/9 ayetin analizi bulundu.\n")
    
    # Embedding üret
    print("🔄 Embedding üretiliyor...")
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for key, data in missing_data.items():
            doc = key_to_doc.get(key)
            if not doc:
                continue
            
            tr_text = doc['display'].get('turkish_text', '')
            keywords_text = " ".join(data['keywords'])
            explanation = data['explanation']
            
            text_to_embed = f"{tr_text} {keywords_text} {explanation}"
            
            try:
                response = client.models.embed_content(
                    model=f"models/{EMBEDDING_MODEL}",
                    contents=text_to_embed,
                    config={"output_dimensionality": OUTPUT_DIMENSION}
                )
                
                embedding = response.embeddings[0].values
                
                result = {
                    "key": key,
                    "embedding": embedding
                }
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
                print(f"   ✅ {key}: Embedding oluşturuldu")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ {key}: Embedding hatası - {e}")
    
    print("\n🎉 TAMAMLANDI!")
    print("📄 Eksik embeddingler 'embeddings_output.jsonl' dosyasına eklendi.")

if __name__ == "__main__":
    main()
