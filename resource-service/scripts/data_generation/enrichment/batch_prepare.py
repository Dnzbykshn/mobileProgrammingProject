"""
Batch API - Phase 1: JSONL Input File Preparation
Bu script tüm Kuran ayetleri için batch request dosyası oluşturur.
"""

import json

# --- AYARLAR ---
INPUT_FILE = "data/quran_final_pristine.json"
OUTPUT_JSONL = "data/batch_requests.jsonl"

# Sure isimleri (DB'ye kaydetmek için)
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

def create_prompt(text, surah, verse):
    """Ayet analizi için gelişmiş prompt oluşturur."""
    return f"""**ROLE:**
Sen dünyanın en yetkin "Klinik Psikoloğu", "Dilbilimcisi" ve "İslam Felsefecisi"sin. Görevin, sana verilen Kuran ayetlerini analiz ederek, bu metinlerin modern insan psikolojisindeki karşılıklarını çıkarmaktır. Bu veriler bir Vektör Veritabanı (Vector DB) için "Semantic Embedding" (Anlamsal Gömme) oluşturmakta kullanılacaktır.

**HEDEF:**
7. yüzyılda inen bu metinler ile 21. yüzyılın modern insanın ruhsal krizleri (anksiyete, depresyon, narsisizm, tükenmişlik, değersizlik hissi vb.) arasında sarsılmaz bir "Anlam Köprüsü" kurmak.

**ANALİZ EDİLECEK AYET:**
"{text}" 
(Sure: {surah}, Ayet: {verse})

**GÖREVLER:**
Aşağıdaki JSON formatında iki çıktı üretmelisin:

1. **`keywords` (List[str]):**
    * Ayetin anlamsal alanını genişleten 5 anahtar kelime.
    * **STRATEJİ:** Ayetin içinde zaten geçen kelimeleri tekrar keyword olarak yazma. Bu israftır.
    * **HEDEF:** Ayetteki kadim bilgiyi modern insanın arama terimleriyle eşleştirmek.
    * **ÖNCELİK:** Öncelikle "Modern Psikolojik" kavramları tercih et (Örn: "Duygusal Regülasyon"). Ancak eğer ayet çok temel bir kavramı anlatıyorsa ve modern karşılığı yoksa, basit ve anlaşılır kelimeler de kullanabilirsin (Örn: "İç Huzur", "Umut", "Yalnızlık").

2. **`explanation` (str):**
    * **Amaç:** Bu ayetin ruhsal etkisini ve çözüm önerisini net bir şekilde ortaya koymak.
    * **Format:** En fazla 3 cümleden oluşan, yoğun ve akıcı bir paragraf yaz.
    * **İçerik Stratejisi:**
        1. Cümle: Teşhis (Bu ayet hangi ruhsal yaraya dokunuyor?).
        2. Cümle: Tedavi (Ayetin önerdiği zihinsel veya kalbi duruş nedir?).
        3. Cümle (Opsiyonel): Sonuç (Bu bakış açısı insana ne kazandırır?).
    * **Yasak:** Tarihsel detaylar, fıkhi tartışmalar veya mealin aynısını tekrar etmek yasaktır. Sadece psikolojik/felsefi analize odaklan.

**CRITICAL RULE FOR EXPLANATION:**
Yazdığın açıklama kesinlikle "Laf Salatası" (Fluff) olmamalıdır.
- Edebi sanat yapma.
- Dolaylı anlatım yapma.
- Konuyu dağıtma.
Her kelime, doğrudan "Sorun -> Çözüm" ekseninde olmalıdır.

**BAŞARI KRİTERLERİ (FEW-SHOT EXAMPLES):**

**ÖRNEK 1:**
*Girdi:* "O takva sahipleri ki, bollukta da darlıkta da Allah için harcarlar; öfkelerini yutarlar ve insanları affederler..."
* `keywords`: ["Dürtü Kontrolü", "Duygusal Regülasyon", "Sosyal Zeka", "Reaktif Davranış", "İçsel Özgürleşme"]
* `explanation`: "İnsanın en ilkel tepkisi olan 'saldırganlık' dürtüsüne karşı, bilinçli bir 'durma' mekanizmasını devreye sokar. Kişiyi, duygularının kölesi olmaktan çıkarıp, olaylara tepki vermek yerine yanıt veren iradi bir özne konumuna yükseltir. Bu sayede ilişkilerde yıkım önlenir ve kişi kendi içsel güç dengesini yeniden kazanır."

**ÖRNEK 2:**
*Girdi:* "Gevşemeyin, üzülmeyin. Eğer gerçekten inanıyorsanız, en üstün olan sizsiniz."
* `keywords`: ["Psikolojik Dayanıklılık", "Öğrenilmiş Çaresizlik", "Öz-Değer", "Aşağılık Kompleksi", "İçsel Motivasyon"]
* `explanation`: "Başarısızlık veya kayıp anlarında zihni ele geçiren 'yetersizlik' ve 'çaresizlik' şemasını hedef alır. Kişinin öz-değerini, değişken dış koşullara değil, sarsılmaz bir içsel inanç sistemine bağlamasını sağlar. Böylece kişi, düştüğü yerden kalkabilmek için ihtiyaç duyduğu mental enerjiyi ve onuru yeniden inşa eder."

**ÖRNEK 3:**
*Girdi:* "Şeytan sizi fakirlikle korkutur ve size cimriliği emreder..."
* `keywords`: ["Kıtlık Bilinci", "Gelecek Kaygısı", "Katastrofik Düşünce", "Finansal Anksiyete", "Bolluk Zihniyeti"]
* `explanation`: "Zihnin, geleceği sürekli bir 'yoksunluk' ve 'felaket' senaryosu üzerinden kurgulayan kaygılı yapısına ayna tutar. Bu korkunun rasyonel bir gerçeklik değil, zihinsel bir manipülasyon olduğunu fark ettirerek kişiyi cömertliğin getirdiği akış ve güven hissine davet eder."

**ÇIKTI FORMATI (Strict JSON):**
{{
  "keywords": ["Kavram1", "Kavram2", "Kavram3", "Kavram4", "Kavram5"],
  "explanation": "Derinlikli, psikolojik tabanlı analiz."
}}"""

def main():
    print(f"📂 '{INPUT_FILE}' okunuyor...")
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Dosya bulunamadı: {INPUT_FILE}")
        return
    
    total = len(dataset)
    print(f"🔥 Toplam {total} ayet için batch request hazırlanacak.")
    
    # Zaten analiz edilmiş ayetleri atla
    skipped = 0
    requests_to_process = []
    
    for doc in dataset:
        # Eğer zaten keywords varsa atla
        if doc['search_content'].get('keywords') and len(doc['search_content']['keywords']) > 0:
            skipped += 1
            continue
        
        surah_no = doc['display'].get('surah_no', 0)
        verse_no = doc['display'].get('verse_no', 0)
        tr_text = doc['display'].get('turkish_text', '')
        
        # Sure ismini ekle
        surah_name = SURAH_NAMES.get(surah_no, f"Sure {surah_no}")
        
        # Key formatı: surah_verse (sıralama için)
        key = f"{surah_no}_{verse_no}"
        
        prompt = create_prompt(tr_text, surah_name, verse_no)
        
        # Batch API formatı
        batch_request = {
            "key": key,
            "request": {
                "contents": [
                    {
                        "parts": [{"text": prompt}],
                        "role": "user"
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
        }
        
        requests_to_process.append(batch_request)
    
    print(f"⏭️ {skipped} ayet zaten analiz edilmiş, atlanıyor.")
    print(f"📝 {len(requests_to_process)} ayet için request hazırlanıyor...")
    
    # JSONL dosyasına yaz
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for req in requests_to_process:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
    
    print(f"✅ '{OUTPUT_JSONL}' dosyası oluşturuldu!")
    print(f"📊 Toplam {len(requests_to_process)} request yazıldı.")
    print(f"\n🚀 Sonraki adım: 'batch_submit.py' çalıştırın.")

if __name__ == "__main__":
    main()
