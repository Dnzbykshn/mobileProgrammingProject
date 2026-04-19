import React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';

import { colors, fonts, spacing, typography } from '@/theme';

type SectionTitleProps = {
  title: string;
  actionLabel?: string;
  onActionPress?: () => void;
  dark?: boolean;
};

export default function SectionTitle({
  title,
  actionLabel,
  onActionPress,
  dark = true,
}: SectionTitleProps) {
  const titleColor = dark ? colors.gold : colors.goldDeep;
  const actionColor = dark ? colors.gold : colors.text.inkMuted;

  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.md,
      }}>
      <Text
        style={{
          ...typography.labelSm,
          fontFamily: fonts.bodySm,
          color: titleColor,
          letterSpacing: 1.2,
          textTransform: 'uppercase',
        }}>
        {title}
      </Text>

      {actionLabel && onActionPress ? (
        <TouchableOpacity onPress={onActionPress} activeOpacity={0.82}>
          <Text
            style={{
              ...typography.labelLg,
              fontFamily: fonts.bodyMd,
              color: actionColor,
            }}>
            {actionLabel}
          </Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}
