"""
Batch Embedding - Submit Embedding Job
Bu script merged batch sonuçlarından embedding JSONL oluşturup batch job başlatır.
"""

import json
import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- AYARLAR ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")
MERGED_RESULTS = "data/batch_results_merged.jsonl"
INPUT_DATA = "data/quran_final_pristine.json"
EMBEDDING_JSONL = "data/embedding_requests.jsonl"
STATUS_FILE = "data/embedding_job_status.json"
EMBEDDING_MODEL = "gemini-embedding-001"

# Eğer dosya zaten yüklendiyse, bu ismi kullan
EXISTING_FILE = None  # örn: "files/xxxxx"

def prepare_embedding_requests():
    """Merged sonuçlardan embedding request JSONL oluşturur."""
    print("📂 Veriler hazırlanıyor...")
    
    # Orijinal veriyi yükle
    with open(INPUT_DATA, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    # Key -> index mapping
    key_to_index = {}
    for i, doc in enumerate(dataset):
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        key_to_index[key] = i
    
    # Merged sonuçları oku ve dataset'e ekle
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
                
                # text alanını bul
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
    
    # Embedding JSONL oluştur
    print("📝 Embedding request'leri oluşturuluyor...")
    embedding_requests = []
    
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
        
        # Batch embedding API formatı
        request = {
            "key": key,
            "request": {
                "model": f"models/{EMBEDDING_MODEL}",
                "content": {
                    "parts": [{"text": text_to_embed}]
                }
            }
        }
        embedding_requests.append(request)
    
    with open(EMBEDDING_JSONL, "w", encoding="utf-8") as f:
        for req in embedding_requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
    
    print(f"✅ '{EMBEDDING_JSONL}' oluşturuldu: {len(embedding_requests)} request")
    return len(embedding_requests)

def main():
    print("🚀 Gemini Batch Embedding Job Başlatılıyor...")
    
    # Önce embedding JSONL'i hazırla
    count = prepare_embedding_requests()
    
    # Client oluştur
    client = genai.Client(api_key=API_KEY)
    
    # 1. JSONL dosyasını yükle
    uploaded_file_name = None
    
    if EXISTING_FILE:
        print(f"📁 Mevcut dosya kullanılıyor: {EXISTING_FILE}")
        uploaded_file_name = EXISTING_FILE
    else:
        print(f"📤 '{EMBEDDING_JSONL}' dosyası yükleniyor...")
        try:
            uploaded_file = client.files.upload(
                file=EMBEDDING_JSONL,
                config=types.UploadFileConfig(
                    display_name='quran-embedding-requests',
                    mime_type='jsonl'
                )
            )
            uploaded_file_name = uploaded_file.name
            print(f"✅ Dosya yüklendi: {uploaded_file_name}")
        except Exception as e:
            print(f"❌ Dosya yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # 2. Batch embedding job oluştur
    print(f"⚙️ Batch embedding job oluşturuluyor (Model: {EMBEDDING_MODEL})...")
    
    try:
        batch_job = client.batches.create(
            model=f"models/{EMBEDDING_MODEL}",
            src=uploaded_file_name,
            config={
                'display_name': "quran-embedding-job",
            },
        )
        
        job_name = batch_job.name
        print(f"✅ Batch embedding job oluşturuldu: {job_name}")
        
        # Job bilgisini kaydet
        status_info = {
            "job_name": job_name,
            "uploaded_file": uploaded_file_name,
            "model": EMBEDDING_MODEL,
            "request_count": count,
            "status": "SUBMITTED"
        }
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_info, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Job bilgisi '{STATUS_FILE}' dosyasına kaydedildi.")
        print(f"\n🕐 Batch job arka planda işleniyor.")
        print(f"📊 Durumu kontrol etmek için: python batch_embedding_poll.py")
        
    except Exception as e:
        print(f"❌ Batch job oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
