// Design System Theme
// Centralized design tokens for the QuranApp

// Color palette
export const colors = {
  // Primary Teal Palette
  teal: {
    darkest: '#05181A',
    darker: '#06181C',
    dark: '#0B3130',
    base: '#0F3438',
    medium: '#113835',
    accent: '#15423F',
    deep: '#164E52',
    light: '#204545',
    lighter: '#237A80',
  },

  // Gold/Accent Colors
  gold: {
    primary: '#FFD700',
    muted: '#C0A060',
  },

  // Text Colors
  text: {
    primary: '#E5E9E9',
    secondary: '#C0CAC9',
    muted: '#436F65',
    white: '#FFFFFF',
  },

  // Status Colors
  status: {
    success: '#1A4642',
    warning: '#FFD700',
    error: '#FF6B6B',
  },
} as const;

// Gradients - Standardized
export const gradients = {
  primary: ['#204545', '#06181C'] as const,           // Main app gradient
  home: ['#237A80', '#164E52', '#05181A'] as const,  // Home screen special gradient
  card: ['#15423F', '#0B3130'] as const,             // Card backgrounds
} as const;

// Spacing scale
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 40,
} as const;

// Border radius scale
export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 30,
  xxxl: 40,
  full: 9999,
} as const;

// Typography scale
export const typography = {
  heading: {
    xl: { fontSize: 32, lineHeight: 40, fontWeight: '700' as const },
    lg: { fontSize: 24, lineHeight: 32, fontWeight: '700' as const },
    md: { fontSize: 20, lineHeight: 28, fontWeight: '700' as const },
    sm: { fontSize: 18, lineHeight: 24, fontWeight: '600' as const },
  },
  body: {
    lg: { fontSize: 16, lineHeight: 24, fontWeight: '400' as const },
    md: { fontSize: 14, lineHeight: 20, fontWeight: '400' as const },
    sm: { fontSize: 12, lineHeight: 18, fontWeight: '400' as const },
  },
  caption: {
    md: { fontSize: 12, lineHeight: 16, fontWeight: '500' as const },
    sm: { fontSize: 10, lineHeight: 14, fontWeight: '500' as const },
  },
} as const;

// Shadow presets
export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 5,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 10,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 15,
  },
} as const;
