import React from 'react';
import { ActivityIndicator, Text, TouchableOpacity, ViewStyle } from 'react-native';
import { LucideIcon } from 'lucide-react-native';

import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

type AppButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type AppButtonProps = {
  label: string;
  onPress?: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: AppButtonVariant;
  icon?: LucideIcon;
  style?: ViewStyle;
};

type ButtonTone = {
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  iconColor: string;
  shadow?: object | null;
};

const toneStyles: Record<AppButtonVariant, ButtonTone> = {
  primary: {
    backgroundColor: colors.gold,
    borderColor: colors.border.gold,
    textColor: colors.text.onGold,
    iconColor: colors.text.onGold,
    shadow: shadows.gold,
  },
  secondary: {
    backgroundColor: colors.surface.raised,
    borderColor: colors.border.strong,
    textColor: colors.text.primary,
    iconColor: colors.text.primary,
    shadow: shadows.sm,
  },
  ghost: {
    backgroundColor: 'transparent',
    borderColor: colors.border.strong,
    textColor: colors.text.secondary,
    iconColor: colors.text.secondary,
    shadow: null,
  },
  danger: {
    backgroundColor: colors.surface.dangerSoft,
    borderColor: colors.border.danger,
    textColor: colors.text.danger,
    iconColor: colors.text.danger,
    shadow: null,
  },
};

export default function AppButton({
  label,
  onPress,
  loading = false,
  disabled = false,
  variant = 'primary',
  icon: Icon,
  style,
}: AppButtonProps) {
  const tone = toneStyles[variant];
  const inactive = disabled || loading;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={inactive}
      activeOpacity={0.88}
      style={[
        {
          minHeight: 52,
          borderRadius: radius.xl,
          borderWidth: 1,
          borderColor: tone.borderColor,
          backgroundColor: tone.backgroundColor,
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'row',
          paddingHorizontal: spacing.lg,
          opacity: inactive ? 0.55 : 1,
        },
        tone.shadow,
        style,
      ]}>
      {loading ? (
        <ActivityIndicator color={tone.iconColor} />
      ) : (
        <>
          {Icon ? <Icon size={18} color={tone.iconColor} /> : null}
          <Text
            style={{
              ...typography.labelLg,
              color: tone.textColor,
              marginLeft: Icon ? spacing.sm + 2 : 0,
              fontFamily: fonts.bodyMd,
            }}>
            {label}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
}
