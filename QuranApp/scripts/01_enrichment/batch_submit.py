"""
Batch API - Phase 2: Submit Batch Job
Bu script JSONL dosyasını yükler ve batch job başlatır.
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
INPUT_JSONL = "data/batch_requests.jsonl"
STATUS_FILE = "data/batch_job_status.json"
MODEL = "models/gemini-3-pro-preview"

# Eğer dosya zaten yüklendiyse, bu ismi kullan (rate limit sonrası tekrar yüklemeden devam için)
# None yaparsanız dosyayı tekrar yükler
EXISTING_FILE = "files/th61piw3glur"

def main():
    print("🚀 Gemini Batch API Job Başlatılıyor...")
    
    # Client oluştur
    client = genai.Client(api_key=API_KEY)
    
    # 1. JSONL dosyasını yükle (veya mevcut olanı kullan)
    uploaded_file_name = None
    
    if EXISTING_FILE:
        print(f"📁 Mevcut dosya kullanılıyor: {EXISTING_FILE}")
        uploaded_file_name = EXISTING_FILE
    else:
        print(f"📤 '{INPUT_JSONL}' dosyası yükleniyor...")
        try:
            uploaded_file = client.files.upload(
                file=INPUT_JSONL,
                config=types.UploadFileConfig(
                    display_name='quran-batch-requests',
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
    
    # 2. Batch job oluştur
    print(f"⚙️ Batch job oluşturuluyor (Model: {MODEL})...")
    
    try:
        batch_job = client.batches.create(
            model=MODEL,
            src=uploaded_file_name,
            config={
                'display_name': "quran-enrichment-job",
            },
        )
        
        job_name = batch_job.name
        print(f"✅ Batch job oluşturuldu: {job_name}")
        
        # Job bilgisini kaydet
        status_info = {
            "job_name": job_name,
            "uploaded_file": uploaded_file_name,
            "model": MODEL,
            "status": "SUBMITTED"
        }
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_info, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Job bilgisi '{STATUS_FILE}' dosyasına kaydedildi.")
        print(f"\n🕐 Batch job arka planda işleniyor (genelde 1-24 saat).")
        print(f"📊 Durumu kontrol etmek için: python batch_poll.py")
        
    except Exception as e:
        print(f"❌ Batch job oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
