import React from 'react';
import { View, ViewStyle } from 'react-native';

import { colors, radius, shadows, spacing } from '@/theme';

type SurfaceCardProps = {
  children: React.ReactNode;
  style?: ViewStyle;
  compact?: boolean;
  highlighted?: boolean;
};

export default function SurfaceCard({
  children,
  style,
  compact = false,
  highlighted = false,
}: SurfaceCardProps) {
  return (
    <View
      style={[
        {
          borderRadius: compact ? radius.lg : radius.xl,
          padding: compact ? spacing.lg : spacing.xl,
          backgroundColor: highlighted ? colors.surface.raised : colors.surface.base,
          borderWidth: 1,
          borderColor: highlighted ? colors.border.strong : colors.border.soft,
          ...shadows.md,
        },
        style,
      ]}>
      {children}
    </View>
  );
}
