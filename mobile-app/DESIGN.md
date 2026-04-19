# Mosqui — Tasarım Sistemi

> *"Acelesiz, dinleyen, hüküm vermeyen. Cevap değil; eşik. Karar değil; tefekkür."*

Uygulama: `mobile-app/theme/mosqui.ts`
İçe aktarma: `import { colors, fonts, typography, spacing, radius, shadows } from '@/theme'`
veya: `import Mosqui from '@/theme'`

---

## Renkler

| Token             | Hex       | Kullanım                          |
|-------------------|-----------|-----------------------------------|
| `colors.night`    | `#0B1020` | Ana arka plan                     |
| `colors.gold`     | `#D8B86A` | Birincil vurgu, aktif öğeler      |
| `colors.paper`    | `#F6F1E6` | Açık yüzey, kart arka planı       |
| `colors.ink`      | `#1A1512` | Açık yüzey üzeri birincil metin   |
| `colors.blue`     | `#4A5A7A` | İkincil vurgu, bilgi öğeleri      |
| `colors.goldDeep` | `#8A6A2E` | Derin vurgu, pressed state        |

### Yüzey ve Kenarlık Tokenleri
```ts
colors.surface.base      // #0B1020 — ana arka plan
colors.surface.raised    // #111827 — kart arka planı
colors.surface.muted     // rgba(gold, 0.06)
colors.border.soft       // rgba(paper, 0.08)
colors.border.accent     // rgba(gold, 0.28)
colors.text.primary      // #F6F1E6 (= paper) — night üzeri metin
colors.text.gold         // #D8B86A
colors.text.ink          // #1A1512 — paper üzeri metin
```

---

## Yazı Tipleri

| Token            | Font                 | Kullanım                    |
|------------------|----------------------|-----------------------------|
| `fonts.heading`  | Fraunces_700Bold     | Başlıklar, hero metinler    |
| `fonts.body`     | Inter_400Regular     | Gövde metni, UI öğeleri     |
| `fonts.bodyMd`   | Inter_500Medium      | Label, buton                |
| `fonts.bodySm`   | Inter_600SemiBold    | Küçük etiket, caption       |
| `fonts.arabic`   | Amiri_400Regular     | Ayet metinleri              |
| `fonts.arabicBold` | Amiri_700Bold      | Arapça başlık               |

### Kullanım
```ts
// Başlık
style={{ fontFamily: fonts.heading, fontSize: 32 }}

// Ayet
style={{ fontFamily: fonts.arabic, fontSize: 24, writingDirection: 'rtl' }}
```

---

## Tipografi Skalası

```ts
typography.display   // 40px heading
typography.h1        // 32px heading
typography.h2        // 24px heading
typography.h3        // 20px heading
typography.h4        // 18px heading
typography.bodyLg    // 16px body
typography.bodyMd    // 14px body
typography.bodySm    // 12px body
typography.labelLg   // 14px medium
typography.arabicLg  // 28px amiri
typography.arabicMd  // 22px amiri
typography.arabicSm  // 16px amiri
```

---

## Ses ve Ton

**Yapılacaklar**
- Sadelik ve boşluk kullan
- Kaynak göster

**Yapılmayacaklar**
- Emoji veya slogan kullanma
- Hüküm verme

---

## Paketler

```bash
@expo-google-fonts/fraunces   # heading
@expo-google-fonts/inter      # body
@expo-google-fonts/amiri      # arabic
```

