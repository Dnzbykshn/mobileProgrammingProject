/**
 * Mosqui — Design System
 * QuranApp için özel tasarım sistemi.
 * Acelesiz, dinleyen, hüküm vermeyen.
 */

// ─── Renkler ─────────────────────────────────────────────────────────────────

export const colors = {
  // Temel palet
  night: '#1A1512', // Ana arka plan (sıcak koyu)
  gold: '#D8B86A', // Birincil vurgu
  paper: '#F6F1E6', // Açık yüzey
  ink: '#1A1512', // Birincil metin (koyu)
  blue: '#5F6C84', // İkincil vurgu
  goldDeep: '#8A6A2E', // Derin vurgu / pressed state

  // Yüzeyler
  surface: {
    // Night ailesi
    base: '#1A1512', // = night
    raised: '#231D19', // Kart arka planı
    overlay: '#201A16', // Modal / overlay
    muted: 'rgba(216,184,106,0.06)', // Gold transparan yüzey
    strong: 'rgba(246,241,230,0.06)', // Paper transparan yüzey
    nightSoft: '#2B241F',
    nightRaised: '#352D27',

    // Paper ailesi
    paper: '#F6F1E6',
    paperRaised: '#FBF7EE',
    paperMuted: '#EFE6D3',
    paperSoft: '#E8DDC6',
    paperStrong: '#DFD1B4',

    // Accent yüzeyler
    goldSoft: '#EADCB7',
    goldMuted: '#E2CF9F',
    dangerSoft: '#F7E2DD',
    successSoft: '#DEEDE2',
  },

  // Kenarlıklar
  border: {
    soft: 'rgba(246,241,230,0.08)', // Hafif
    muted: 'rgba(216,184,106,0.10)', // Altın tonu
    strong: 'rgba(246,241,230,0.14)', // Belirgin
    accent: 'rgba(216,184,106,0.28)', // Vurgulu
    danger: 'rgba(220,60,60,0.20)', // Hata

    // Paper odaklı kenarlıklar
    paper: '#E4D9C2',
    paperSoft: '#ECE4D2',
    paperStrong: '#D7C7A8',
    night: '#3A312B',
    gold: '#C9A75D',
  },

  // Metin
  text: {
    // Night üzeri
    primary: '#F6F1E6', // = paper
    secondary: 'rgba(246,241,230,0.65)',
    muted: 'rgba(246,241,230,0.35)',

    // Accent
    gold: '#D8B86A',

    // Paper üzeri
    ink: '#1A1512',
    inkMuted: 'rgba(26,21,18,0.55)',
    inkSoft: '#6A6050',

    // Özel
    onGold: '#1A1512',
    danger: '#A23A30',
    success: '#2F6A47',
  },

  overlay: {
    scrim: 'rgba(26,21,18,0.56)',
    soft: 'rgba(26,21,18,0.36)',
    light: 'rgba(246,241,230,0.72)',
  },

  // Durum renkleri
  status: {
    success: '#4A7C59',
    warning: '#D8B86A',
    error: '#C0392B',
    info: '#4A5A7A',
  },
} as const;

// ─── Gradyanlar ──────────────────────────────────────────────────────────────

export const gradients = {
  night: ['#2B241F', '#1A1512'] as const,
  golden: ['#2A1F0A', '#1A1512'] as const,
  paper: ['#F6F1E6', '#EDE6D6'] as const,
} as const;

// ─── Yazı Tipleri ─────────────────────────────────────────────────────────────

export const fonts = {
  heading: 'Fraunces_700Bold', // Başlık · editöryel serif
  body: 'Inter_400Regular', // Gövde · okunur sans
  bodyMd: 'Inter_500Medium',
  bodySm: 'Inter_600SemiBold',
  arabic: 'Amiri_400Regular', // Ayet metinleri
  arabicBold: 'Amiri_700Bold',
} as const;

// ─── Tipografi Skalası ────────────────────────────────────────────────────────

export const typography = {
  display: { fontSize: 40, lineHeight: 48, fontFamily: fonts.heading },
  h1: { fontSize: 32, lineHeight: 40, fontFamily: fonts.heading },
  h2: { fontSize: 24, lineHeight: 32, fontFamily: fonts.heading },
  h3: { fontSize: 20, lineHeight: 28, fontFamily: fonts.heading },
  h4: { fontSize: 18, lineHeight: 24, fontFamily: fonts.heading },

  bodyLg: { fontSize: 16, lineHeight: 26, fontFamily: fonts.body },
  bodyMd: { fontSize: 14, lineHeight: 22, fontFamily: fonts.body },
  bodySm: { fontSize: 12, lineHeight: 18, fontFamily: fonts.body },

  labelLg: { fontSize: 14, lineHeight: 20, fontFamily: fonts.bodyMd },
  labelMd: { fontSize: 12, lineHeight: 16, fontFamily: fonts.bodyMd },
  labelSm: { fontSize: 10, lineHeight: 14, fontFamily: fonts.bodySm },

  arabicLg: { fontSize: 28, lineHeight: 48, fontFamily: fonts.arabic },
  arabicMd: { fontSize: 22, lineHeight: 38, fontFamily: fonts.arabic },
  arabicSm: { fontSize: 16, lineHeight: 28, fontFamily: fonts.arabic },
} as const;

// ─── Boşluk Skalası ──────────────────────────────────────────────────────────

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
  huge: 64,
} as const;

// ─── Kenar Yarıçapı ──────────────────────────────────────────────────────────

export const radius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  full: 9999,
} as const;

// ─── Gölgeler ────────────────────────────────────────────────────────────────

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 5,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.24,
    shadowRadius: 14,
    elevation: 10,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 14 },
    shadowOpacity: 0.28,
    shadowRadius: 24,
    elevation: 14,
  },
  gold: {
    shadowColor: '#D8B86A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
} as const;

// ─── Tek nesne ihracı ─────────────────────────────────────────────────────────

export const Mosqui = {
  colors,
  gradients,
  fonts,
  typography,
  spacing,
  radius,
  shadows,
} as const;

export default Mosqui;
