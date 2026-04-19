"""
Batch Embedding - Phase 1: JSONL Hazırlama
Bu script zenginleştirilmiş ayet metinlerini embedding batch için JSONL'e yazar.
"""

import json

# --- AYARLAR ---
INPUT_FILE = "data/quran_final_pristine.json"
BATCH_RESULTS = "data/batch_results.jsonl"
OUTPUT_JSONL = "data/embedding_requests.jsonl"

# Sure isimleri
SURAH_NAMES = {
    1: "Fâtiha", 2: "Bakara", 3: "Âl-i İmrân", 4: "Nisâ", 5: "Mâide", 6: "En'âm", 7: "A'râf", 8: "Enfâl", 9: "Tevbe", 10: "Yûnus",
    11: "Hûd", 12: "Yûsuf", 13: "Ra'd", 14: "İbrâhîm", 15: "Hicr", 16: "Nahl", 17: "İsrâ", 18: "Kehf", 19: "Meryem", 20: "Tâhâ",
    21: "Enbiyâ", 22: "Hac", 23: "Mü'minûn", 24: "Nûr", 25: "Furkân", 26: "Şuarâ", 27: "Neml", 28: "Kasas", 29: "Ankebût", 30: "Rûm",
    31: "Lokmân", 32: "Secde", 33: "Ahzâb", 34: "Sebe'", 35: "Fâtır", 36: "Yâsîn", 37: "Sâffât", 38: "Sâd", 39: "Zümer", 40: "Mü'min",
    41: "Fussilet", 42: "Şûrâ", 43: "Zuhruf", 44: "Duhân", 45: "Câsiye", 46: "Ahkâf", 47: "Muhammed", 48: "Fetih", 49: "Hucurât", 50: "Kâf",
    51: "Zâriyât", 52: "Tûr", 53: "Necm", 54: "Kamer", 55: "Rahmân", 56: "Vâkıa", 57: "Hadîd", 58: "Mücâdele", 59: "Haşr", 60: "Mümtehine",
    61: "Saff", 62: "Cuma", 63: "Münâfikûn", 64: "Teğâbün", 65: "Talâk", 66: "Tahrîm", 67: "Mülk", 68: "Kalem", 69: "Hâkka", 70: "Meâric",
    71: "Nûh", 72: "Cin", 73: "Müzzemmil", 74: "Müddessir", 75: "Kıyâmet", 76: "İnsân", 77: "Mürselât", 78: "Nebe", 79: "Nâziât", 80: "Abese",
    81: "Tekvîr", 82: "İnfitâr", 83: "Mutaffifîn", 84: "İnşikâk", 85: "Bürûc", 86: "Târık", 87: "A'lâ", 88: "Gâşiye", 89: "Fecr", 90: "Beled",
    91: "Şems", 92: "Leyl", 93: "Duhâ", 94: "İnşirah", 95: "Tîn", 96: "Alak", 97: "Kadir", 98: "Beyyine", 99: "Zilzâl", 100: "Âdiyât",
    101: "Kâria", 102: "Tekâsür", 103: "Asr", 104: "Hümeze", 105: "Fîl", 106: "Kureyş", 107: "Mâûn", 108: "Kevser", 109: "Kâfirûn", 110: "Nasr",
    111: "Tebbet", 112: "İhlâs", 113: "Felak", 114: "Nâs"
}

def main():
    print("🚀 Embedding Batch Verileri Hazırlanıyor...")
    
    # 1. Orijinal veriyi yükle
    print(f"📂 '{INPUT_FILE}' okunuyor...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Dosya bulunamadı: {INPUT_FILE}")
        return
    
    # Key -> index mapping
    key_to_index = {}
    for i, doc in enumerate(dataset):
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        key_to_index[key] = i
    
    # 2. Batch analiz sonuçlarını yükle
    print(f"📂 '{BATCH_RESULTS}' okunuyor...")
    try:
        batch_results = []
        with open(BATCH_RESULTS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    batch_results.append(json.loads(line))
    except FileNotFoundError:
        print(f"❌ Dosya bulunamadı: {BATCH_RESULTS}")
        return
    
    print(f"📊 {len(batch_results)} analiz sonucu bulundu.")
    
    # 3. Sonuçları dataset'e eşle
    for result in batch_results:
        key = result.get('key', '')
        if 'error' in result:
            continue
        
        try:
            response_obj = result.get('response', {})
            candidates = response_obj.get('candidates', [])
            if not candidates:
                continue
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                continue
            
            response_text = parts[0].get('text', '')
            parsed = json.loads(response_text)
            
            keywords = parsed.get('keywords', [])
            explanation = parsed.get('explanation', '')
            
            if key in key_to_index:
                idx = key_to_index[key]
                dataset[idx]['search_content']['keywords'] = keywords
                dataset[idx]['semantic_content']['explanation'] = explanation
        except:
            continue
    
    # 4. Embedding için JSONL oluştur
    print("📝 Embedding request'leri hazırlanıyor...")
    
    embedding_requests = []
    
    for doc in dataset:
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        key = f"{surah_no}_{verse_no}"
        
        # Keywords yoksa atla
        keywords = doc['search_content'].get('keywords', [])
        if not keywords:
            continue
        
        # Embedding metni oluştur
        tr_text = doc['display'].get('turkish_text', '')
        keywords_text = " ".join(keywords)
        explanation = doc['semantic_content'].get('explanation', '')
        
        text_to_embed = f"{tr_text} {keywords_text} {explanation}"
        
        # Batch embedding formatı
        request = {
            "key": key,
            "request": {
                "content": text_to_embed
            }
        }
        
        embedding_requests.append(request)
    
    # JSONL'e yaz
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for req in embedding_requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
    
    print(f"✅ '{OUTPUT_JSONL}' dosyası oluşturuldu!")
    print(f"📊 Toplam {len(embedding_requests)} embedding request yazıldı.")
    print(f"\n🚀 Sonraki adım: 'python batch_embedding_submit.py' çalıştırın.")

if __name__ == "__main__":
    main()
