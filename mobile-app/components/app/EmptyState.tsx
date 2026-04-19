import React from 'react';
import { Text, View } from 'react-native';

import SurfaceCard from '@/components/app/SurfaceCard';
import { colors, fonts, radius, spacing, typography } from '@/theme';

type EmptyStateProps = {
  message: string;
  compact?: boolean;
};

export default function EmptyState({ message, compact = true }: EmptyStateProps) {
  return (
    <SurfaceCard compact={compact}>
      <Text
        style={{
          ...typography.bodyMd,
          fontFamily: fonts.body,
          color: colors.text.secondary,
        }}>
        {message}
      </Text>
    </SurfaceCard>
  );
}
