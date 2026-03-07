## 🚀 Senaryo: "İş stresi yaşayan Ahmet, uygulamayı ilk kez açıyor"

---

### 1. 📱 Uygulama Açılışı — Kimlik Doğrulama

**Dosya:** _layout.tsx

`RootLayout` render edilir → `AuthProvider` sarmalar → `AppNavigator` içinde `useAuth()` hook'u devreye girer.

AuthContext.tsx → uygulama açılınca `AsyncStorage`'dan token kontrol edilir. Token yoksa:
- → `router.replace('/auth/login')` → app/auth/login.tsx gösterilir

Ahmet register olur:
- `AuthContext.register()` → `services/auth.ts` → backend `POST /auth/register`
- JWT token kaydedilir, `user` state'e set edilir
- `isLoggedIn = true` → `router.replace('/(tabs)')` ile ana sayfaya yönlenir

---

### 2. 🏠 Ana Ekran — Home

**Dosya:** (tabs)/index.tsx/index.tsx) → `HomeScreen`

Ahmet şunu görür:
- Namaz vakitleri + geri sayım sayacı (statik)
- **"FLOWLY AI"** hero kartı: *"Selamun Aleykum. Bugün ruhun nasıl hissediyor?"*
- "Senin İçin Rutinler" bölümü

Hero karttaki input alanına tıklar → Chat sekmesine geçer.

---

### 3. 💬 Sohbet — IDLE fazı

**Dosya:** (tabs)/chat.tsx/chat.tsx) → `ChatScreen`

Ekran açılır:
- `AsyncStorage.getItem('chat_sessions_v1')` → `normalizeStoredSessions()` ile geçmiş sessionlar yüklenir (`hydrateSessions`)
- İlk açılışta `createEmptySession()` → bot selamlaması: *"Selamun Aleyküm, nasıl hissediyorsun bugün?"* (`createWelcomeMessage()`)

Ahmet yazar: **"İş yerimde çok fazla baskı var, dayanamıyorum artık"**

`handleSend()` → `sendMessageDirect()` çağrılır:
1. Mesaj + "Düşünüyorum..." loading balonu eklenir
2. chat.ts → `sendChatMessage(userText, conversationId)` → backend `POST /api/v1/chat`

---

### 4. 🧠 Backend — MasterBrain State Machine

**Dosya:** chat.py

chat.py endpoint'i:
1. `get_or_create_conversation()` → yeni `Conversation` DB'ye kaydedilir
2. `build_user_context()` → kullanıcı profili, aktif planlar, geçmiş anılar Redis'ten/DB'den çekilir
3. `MasterBrain.process_turn()` çağrılır

**Dosya:** master_brain.py → `process_turn()`

- Önce `check_guardrails()`: **"dayanamıyorum"** → `CRISIS_HIGH` listesinde! ⚠️
  - Empati + kriz kaynakları mesajı döner: *"Eğer kendini güvende hissetmiyorsan 182'yi ara"*
  - `crisis_level: "high"` ile yanıt döner

Frontend'de `response.intent === 'CRISIS'` dalı → kriz balonu gösterilir (kırmızı, 112/182 numaraları).

> Ahmet "dayanamıyorum" yerine şunu yazar: **"İşte çok fazla baskı var, stres içindeyim"**

---

### 5. 🔍 GATHERING Fazı — Bilgi Toplama

`check_guardrails()` → pass. `phase = "IDLE"` → `_handle_idle()`:
- `decide_intent()` → Gemini AI: "İş stresi" → `intent: "NEEDS_THERAPY"` → faz **GATHERING**'e geçer

Ahmet'e gelen yanıt tipi: `gathering_progress` → progress bar gösterilir (%25)

**`gather_info()`** çalışır:
```
readiness_score: 3  (duygu biliniyor ama sebep/süre/etki eksik)
follow_up_question: "Seni duyuyorum... Allah'ın izniyle bu da geçecek.
                     Bu durum ne zamandır böyle, biraz anlatır mısın?"
```

Ahmet 2-3 mesaj daha atar. Her turda `readiness_score` artar.

Ahmet: **"3 aydır böyle, uyuyamıyorum, ailemle de sorun yaşıyorum"**
→ `readiness_score: 8` → `proposal_summary` doldurulur → faz **PROPOSING**

---

### 6. 🗺️ PROPOSING — Yolculuk Önerisi

Frontend'de `response.intent === 'PROPOSING'` → özel bir kart gösterilir:

> *"Seni anladım. Kaygı ve iş stresi seni yıpratmış. 7 günlük özel bir manevi yolculuk hazırlayabilirim, inşaAllah."*
> 
> **[🤲 Yolculuğa Başla]** butonu

Ahmet "Yolculuğa Başla"ya basar → `sendMessageDirect('Evet, başlayalım!')` tetiklenir.

`_handle_proposing()` → faz **READY**'e geçer.

---

### 7. 💊 Reçete Üretimi — PrescriptionEngine

**Dosya:** prescription_engine.py

`PrescriptionEngine`:
1. **`diagnose()`** → tüm konuşma bağlamından Gemini ile teşhis:
   - `emotional_state: "Stres"`, `root_cause: "İş baskısı..."`, `spiritual_needs: ["Tevekkül", "Sabır", "Sekine"]`
2. **`retrieve_verses()`** → PostgreSQL'e pgvector sorgusu → embedding benzerliğiyle ayetler bulunur
3. **`select_best_verses()`** → Gemini editör → kötü tonlu/bağlam dışı ayetler filtrelenir (`BLACKLIST_VERSES`)
4. Reçete objesi döner: ayetler + esmalar + dualar + tavsiye

---

### 8. 🗓️ Plan Oluşturma — 7 Günlük Yolculuk

**Dosya:** plan_service.py

`PlanService.create_journey()`:
1. `plan_repository.create_plan()` → DB'ye yeni plan kaydı
2. **Day 0:** `_create_day0_tasks()` → reçeteden anlık görevler (ayet okuma, dua, "33'lük acil rutin")
3. **Days 1-7:** Gemini AI → sabah/akşam/günlük görevler, kademeli zorluk
4. `JourneyDecisionService.decide()` → AI karar: mevcut "Stres" planı var mı? Yeni plan mı, güncelleme mi?

---

### 9. 📦 Reçete Kartı Frontend'de

Frontend: `response.intent === 'PRESCRIPTION'` → `toPrescriptionCard()` → kart objesi oluşturulur

- `saveActivePlanId(response.plan_id)` → AsyncStorage'a plan ID kaydedilir
- Chat ekranında özel prescription kartı gösterilir: ayet listesi, dua, esmalar

**[Yolculuğa Devam Et]** butonu → `router.push('/action/plan?planId=...')`

---

### 10. 📅 Plan Ekranı

**Dosya:** plan.tsx → `PlanScreen`

`getPlan(planId)` → backend `GET /plans/{id}`

- **Day 0** → `Day0View.tsx` bileşeni → anlık reçete (ayetler, dua, "Hasbunallahu ve ni'mel vekîl" 33 kez)
- **Day 1-7** → görev listesi: sabah suresi, akşam duası, günlük yansıma

`handleToggleTask()` → `toggleTask()` → backend'e tamamlandı işareti
`handleCompleteDay()` → `completeDay()` → plan ilerler, `current_day` güncellenir

---

### 11. 🧩 Arkaplanda: Anı Çıkarma

**Dosya:** memory_extraction_service.py

Sohbet GENERATED fazına geçince **asenkron** çalışır:
- `extract_memories_from_conversation()` → Gemini tüm konuşmayı analiz eder
- Çıktı: `emotional_state`, `life_event`, `goal` gibi kategorilerde yapılandırılmış anılar
- Her anı için embedding üretilir → DB'ye kaydedilir

---

### 12. 🗃️ Anılar Sekmesi

**Dosya:** (tabs)/memories.tsx/memories.tsx) → `MemoriesScreen`

`getMemories()` → backend `GET /memories` → Ahmet'in tüm anıları timeline olarak listelenir:
- *"3 aydır iş stresi yaşıyor"*
- *"Aile ilişkisi de etkilenmiş"*
- *"Tevekkül ve sabra ihtiyaç duyuyor"*

Arama yapılabilir: `searchMemories()` → backend'de embedding benzerliği ile semantik arama.

---

## 🔄 Özet: Tam Akış Şeması

```
[Uygulama Açılış]
    _layout.tsx → AppNavigator → AuthContext
          ↓ (token yok)
    auth/login.tsx → services/auth.ts → /auth/login
          ↓ (token var)
    (tabs)/index.tsx → HomeScreen
          ↓ (chat'e tıkla)
    (tabs)/chat.tsx → sendMessageDirect()
          ↓
    services/chat.ts → POST /api/v1/chat
          ↓
    endpoints/chat.py → build_user_context()
          ↓
    master_brain.py → process_turn()
    ├── check_guardrails()          [kriz kontrol]
    ├── _handle_idle() → decide_intent()   [IDLE→GATHERING]
    ├── _handle_gathering() → gather_info()  [sorular]
    ├── _handle_proposing()         [PROPOSING kart]
    └── prescription_engine.py → diagnose() + retrieve() + select()
          ↓
    plan_service.py → create_journey()  [7 günlük plan]
    journey_decision_service.py → decide()  [yeni mi / güncelle mi]
          ↓ (async)
    memory_extraction_service.py → extract_memories()
          ↓
    action/plan.tsx → PlanScreen → Day0View
          ↓ (sonraki gün)
    (tabs)/memories.tsx → MemoriesScreen
```

