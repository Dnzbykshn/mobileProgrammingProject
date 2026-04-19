import json

# Eksik ayetler
missing_keys = ["3_139", "4_54", "23_100", "24_15", "30_46", "34_2", "35_44", "81_23", "90_15"]

print("🔍 Eksik ayetlerin batch sonuçlarını kontrol ediyorum...\n")

with open('data/batch_results_merged.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            key = data.get('key', '')
            
            if key in missing_keys:
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"📍 AYET: {key}")
                
                # Error var mı?
                if 'error' in data:
                    print(f"❌ ERROR: {data['error']}")
                    continue
                
                # Response var mı?
                response = data.get('response', {})
                candidates = response.get('candidates', [])
                
                if not candidates:
                    print("❌ Candidates boş!")
                    continue
                
                # Finish reason
                finish_reason = candidates[0].get('finishReason', 'N/A')
                print(f"📋 Finish Reason: {finish_reason}")
                
                # Content var mı?
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                
                if not parts:
                    print("❌ Parts boş!")
                    continue
                
                # Text bul
                for part in parts:
                    if 'text' in part:
                        text = part['text']
                        print(f"📝 Text (ilk 300 char):")
                        print(text[:300])
                        
                        # JSON parse dene
                        try:
                            parsed = json.loads(text)
                            print(f"✅ JSON parse başarılı!")
                            print(f"   Keywords: {parsed.get('keywords', [])}")
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON parse hatası: {e}")
                        break
                
                print()
