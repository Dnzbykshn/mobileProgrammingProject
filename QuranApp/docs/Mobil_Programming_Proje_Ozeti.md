# Mobil Programming Dersi - Proje Ozeti

## 1) Proje Konusu

Bu proje, kullanicinin manevi ve duygusal durumunu sohbet yoluyla anlayip, ona ozel **manevi rutin/yolculuk** oneren bir mobil odakli uygulamadir.

Uygulama, kullanicinin yazdigi metni analiz ederek:

- Duygusal durumu belirler
- Gerekirse kriz seviyesini tespit eder
- Ayet, dua, esma ve gorevlerden olusan kisilestirilmis bir plan uretir
- Planin ilerleyisini gun gun takip ettirir

Kisa ifade ile: **AI destekli manevi rehberlik + gorev tabanli mobil yolculuk**.

## 2) Projenin Amaci ve Problem Tanimi

Sadece "ayet arama" yaklasimi kullanicinin ihtiyacini her zaman karsilamaz. Kullanici genelde bir duygu durumu ile gelir (kaygi, huzursuzluk, umutsuzluk vb.).

Bu proje:

- Konusma baglamini takip eden,
- Kullanicinin ihtiyacina gore yon degistiren,
- Gunluk mini gorevlerle davranisa dokunen,
- Mobil cihaz uzerinden surekli kullanilabilecek bir deneyim sunar.

## 3) Genel Sistem Mimarisi (Kisa)

- **Mobil Uygulama (React Native + Expo):** Ana kullanici arayuzu
- **Backend API (FastAPI):** Auth, chat, memory, plan, prescription servisleri
- **Veritabani (PostgreSQL + pgvector):** Kullanici, sohbet, anilar, planlar, vektor veriler
- **Redis:** Cache ve hizlandirma
- **Gemini modelleri:** Mesaj analizi, yonlendirme, icerik ve embedding uretimi

## 4) Kullanilan Teknolojiler

### Mobil Taraf

- React Native `0.81.5`
- Expo `54`
- Expo Router (dosya tabanli navigasyon)
- TypeScript
- NativeWind + TailwindCSS (stil sistemi)
- Expo Secure Store (guvenli token saklama)
- AsyncStorage (yerel gecmis ve fallback veri)
- Expo Linking (acil telefon arama)
- React Native Safe Area Context
- React Native Reanimated / Worklets (animasyon)

### Backend Taraf

- FastAPI
- SQLAlchemy (async) + Alembic
- PostgreSQL + pgvector
- Redis
- JWT tabanli kimlik dogrulama + refresh token
- Google Gemini (LLM + embedding)
- SlowAPI (rate limiting)

## 5) Mobil Tarafin Teknik Ozetini Derinlestirme

### 5.1 Uygulama Yapisi ve Navigasyon

Mobil uygulama Expo Router ile dosya tabanli yapida kurgulanmistir:

- `app/_layout.tsx`: global provider ve auth kontrolu
- `app/(tabs)/`: ana tab yapisi (home, explore, chat, memories, profile)
- `app/auth/`: giris/kayit ekranlari
- `app/action/`: prescription/reading/plan akislari

Bu yapiyla kullanici login degilse auth ekranina, login ise tab yapisina yonlendirilir.

### 5.2 Auth ve Oturum Yonetimi

Mobilde auth akisinin onemli noktalari:

- Access token + refresh token kullanimi
- Tokenlarin cihazda guvenli saklanmasi (`expo-secure-store`)
- Her cihaz icin `X-Device-ID` uretimi ve backend'e gonderimi
- `401` durumunda otomatik refresh denemesi
- Profil ekraninda aktif oturumlari listeleme ve "tum cihazlardan cikis"

Bu kisim mobil programlama dersi icin guclu bir gercek-dunya authentication ornegidir.

### 5.3 Chat Deneyimi ve Durum Makinesi

Chat ekrani klasik mesajlasmadan daha ileri bir akis uygular:

- Mesajlar session bazli tutulur (yerel gecmis)
- Backend `conversation_id` ile cok turlu konusma takibi yapar
- Fazlar: `IDLE -> GATHERING -> PROPOSING -> GENERATED/ONGOING`
- Kullanicidan yeterli bilgi toplaninca yolculuk onerisi gelir
- Onaydan sonra plan olusturulur ve mobilde plan ekranina gidilir

Ayrica kriz mesajlari icin ozel kartlar ve acil arama butonlari bulunur.

### 5.4 Plan / Yolculuk Modulu

Plan modulu mobilde gorev tamamlama odaklidir:

- 8 gunluk yapi (Gun 0 + Gun 1-7)
- Gunluk gorev tipleri: sabah, aksam, journal + day0 ozel icerikler
- Gorev tamamlandikca bir sonraki adimin acilmasi
- Gun 0 atlama secenegi
- Aktif yolculuklarin explore ekraninda ilerleme cizgisiyle gosterilmesi

Bu kisim mobil dersleri icin state yonetimi + API senkronizasyonu + UX akislarini birlikte gostermektedir.

### 5.5 Memory Timeline ve Gizlilik Ozellikleri

Uygulama, konusmalardan cikarilan "anilari" mobilde yonetir:

- Memory listesi, filtreleme, semantic arama
- Tekil memory silme
- Gizlilik raporu (memory sayisi, tur dagilimi, depolama boyutu)
- Hassas veri bilgilendirme metinleri

Bu sayede mobil istemci sadece chat degil, kisilestirme verisini de gorunur hale getirir.

### 5.6 Yerel Depolama ve Dayaniklilik

Mobil taraf baglanti problemlerine karsi dayanimi arttirir:

- Chat session gecmisini AsyncStorage'a yazar
- Prescription gecmisini yerelde tutar
- Chat servisi API erisilemezse mock akis ile calisabilir

Bu tasarim, "offline-first olmasa da fault-tolerant mobile UX" yaklasimini destekler.

## 6) Mobil-Backend Entegrasyonu (Ornek Endpoint Gruplari)

- Auth: `/api/v1/auth/*`
- Chat: `/api/v1/chat/send`
- Plans: `/api/v1/plans/*`
- Memories: `/api/v1/memories/*`
- Prescriptions: `/api/v1/prescriptions/*`

Mobil servis katmani (`mobile-app/services`) bu endpointleri tipli fonksiyonlarla kullanir.

## 7) Mobil Programming Dersi Acisindan Kazanimlar

Bu proje su basliklarda ders hedefleriyle ortusur:

- React Native ile cok ekranli uygulama gelistirme
- Navigasyon mimarisi (tab + stack + modal)
- Context tabanli global state (auth)
- REST API entegrasyonu ve hata yonetimi
- Guvenli token saklama ve oturum yenileme
- Yerel depolama (cache/gecmis)
- Kullanici odakli UI/UX ve kriz durumlari icin ozel akis tasarimi

## 8) Kisa Sonuc

QuranApp, mobil tarafta sadece bir "chat arayuzu" degil; auth, kisilestirme, gorev takibi, yerel veri yonetimi ve guvenlik ihtiyaclarini bir araya getiren kapsamli bir mobil yazilim ornegidir.

Mobil Programming dersi kapsaminda proje, hem teknik derinlik hem de gercek kullanim senaryosu acisindan guclu bir bitirme/teslim dokumani sunmaktadir.

