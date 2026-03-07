import React from 'react';
import { View, ViewStyle } from 'react-native';
import { colors, radius, shadows, spacing } from '@/theme';

type CardVariant = 'default' | 'hero' | 'outlined' | 'flat';

interface CardProps {
  variant?: CardVariant;
  children: React.ReactNode;
  style?: ViewStyle;
}

const variantStyles: Record<CardVariant, ViewStyle> = {
  default: {
    backgroundColor: colors.teal.medium,
    borderRadius: radius.xxl,
    padding: spacing.lg,
    ...shadows.md,
  },
  hero: {
    backgroundColor: colors.teal.deep,
    borderRadius: radius.xxxl,
    padding: spacing.xl,
    ...shadows.lg,
  },
  outlined: {
    backgroundColor: colors.teal.accent,
    borderRadius: radius.xxl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.text.muted,
  },
  flat: {
    backgroundColor: colors.teal.medium,
    borderRadius: radius.xl,
    padding: spacing.md,
  },
};

export function Card({ variant = 'default', children, style }: CardProps) {
  return (
    <View style={[variantStyles[variant], style]}>
      {children}
    </View>
  );
}

export function HeroCard({ children, style }: Omit<CardProps, 'variant'>) {
  return <Card variant="hero" style={style}>{children}</Card>;
}

export function InfoCard({ children, style }: Omit<CardProps, 'variant'>) {
  return <Card variant="outlined" style={style}>{children}</Card>;
}
