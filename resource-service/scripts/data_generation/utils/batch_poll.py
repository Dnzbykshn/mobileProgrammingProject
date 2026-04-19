"""
Batch API - Phase 3: Poll Status & Download Results
Bu script batch job durumunu izler ve tamamlandığında sonuçları indirir.
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
STATUS_FILE = "data/batch_job_status.json"
RESULTS_FILE = "data/batch_results.jsonl"
POLL_INTERVAL = 30  # saniye

def main():
    print("🔍 Batch Job Durumu Kontrol Ediliyor...")
    
    # Status dosyasını oku
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_info = json.load(f)
    except FileNotFoundError:
        print(f"❌ '{STATUS_FILE}' bulunamadı. Önce 'batch_submit.py' çalıştırın.")
        return
    
    job_name = status_info.get("job_name")
    if not job_name:
        print("❌ Job name bulunamadı!")
        return
    
    print(f"📋 Job: {job_name}")
    
    # Client oluştur
    client = genai.Client(api_key=API_KEY)
    
    # Tamamlanma durumları
    completed_states = {
        'JOB_STATE_SUCCEEDED',
        'JOB_STATE_FAILED',
        'JOB_STATE_CANCELLED',
        'JOB_STATE_EXPIRED',
    }
    
    # Durumu kontrol et
    try:
        batch_job = client.batches.get(name=job_name)
        current_state = batch_job.state.name if hasattr(batch_job.state, 'name') else str(batch_job.state)
        
        print(f"📊 Mevcut Durum: {current_state}")
        
        if current_state not in completed_states:
            print(f"\n⏳ Job hala işleniyor. {POLL_INTERVAL} saniyede bir kontrol ediliyor...")
            print("   (Ctrl+C ile çıkabilirsiniz, job arka planda devam eder)")
            
            while current_state not in completed_states:
                time.sleep(POLL_INTERVAL)
                batch_job = client.batches.get(name=job_name)
                current_state = batch_job.state.name if hasattr(batch_job.state, 'name') else str(batch_job.state)
                print(f"   🔄 Durum: {current_state}")
        
        print(f"\n✅ Job tamamlandı: {current_state}")
        
        # Başarılıysa sonuçları indir
        if current_state == 'JOB_STATE_SUCCEEDED':
            print("📥 Sonuçlar indiriliyor...")
            
            # Inline responses varsa
            if batch_job.dest and batch_job.dest.inlined_responses:
                print("   Inline responses bulundu...")
                with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                    for resp in batch_job.dest.inlined_responses:
                        if resp.response:
                            f.write(json.dumps({
                                "key": getattr(resp, 'key', 'unknown'),
                                "response": resp.response.text if hasattr(resp.response, 'text') else str(resp.response)
                            }, ensure_ascii=False) + "\n")
                        elif resp.error:
                            f.write(json.dumps({
                                "key": getattr(resp, 'key', 'unknown'),
                                "error": str(resp.error)
                            }, ensure_ascii=False) + "\n")
            
            # File response varsa
            elif batch_job.dest and batch_job.dest.file_name:
                result_file_name = batch_job.dest.file_name
                print(f"   Dosyadan indiriliyor: {result_file_name}")
                
                file_content = client.files.download(file=result_file_name)
                
                with open(RESULTS_FILE, "wb") as f:
                    f.write(file_content)
                
                print(f"✅ Sonuçlar '{RESULTS_FILE}' dosyasına kaydedildi.")
            
            else:
                print("⚠️ Sonuç bulunamadı!")
                return
            
            # Status güncelle
            status_info["status"] = "COMPLETED"
            status_info["results_file"] = RESULTS_FILE
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(status_info, f, ensure_ascii=False, indent=2)
            
            print(f"\n🎉 İşlem tamamlandı!")
            print(f"📊 Sonraki adım: 'python enrich_from_batch.py' çalıştırın.")
            
        elif current_state == 'JOB_STATE_FAILED':
            print(f"❌ Job başarısız oldu!")
            if hasattr(batch_job, 'error'):
                print(f"   Hata: {batch_job.error}")
        
        elif current_state == 'JOB_STATE_CANCELLED':
            print("⚠️ Job iptal edildi.")
        
        elif current_state == 'JOB_STATE_EXPIRED':
            print("⚠️ Job süresi doldu (48 saat).")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
