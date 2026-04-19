import React from 'react';
import { Text, TouchableOpacity, ViewStyle } from 'react-native';

import { colors, fonts, radius, spacing, typography } from '@/theme';

type AppChipProps = {
  label: string;
  active?: boolean;
  dark?: boolean;
  onPress?: () => void;
  style?: ViewStyle;
};

export default function AppChip({
  label,
  active = false,
  dark = true,
  onPress,
  style,
}: AppChipProps) {
  const backgroundColor = active
    ? colors.gold
    : dark
      ? colors.surface.strong
      : colors.surface.paperMuted;
  const borderColor = active ? colors.border.gold : dark ? colors.border.soft : colors.border.paper;
  const textColor = active
    ? colors.text.onGold
    : dark
      ? colors.text.secondary
      : colors.text.inkMuted;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={0.82}
      style={[
        {
          paddingHorizontal: spacing.lg - 2,
          paddingVertical: spacing.sm,
          borderRadius: radius.full,
          backgroundColor,
          borderWidth: 1,
          borderColor,
        },
        style,
      ]}>
      <Text
        style={{
          ...typography.labelLg,
          fontFamily: fonts.bodyMd,
          color: textColor,
        }}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}
