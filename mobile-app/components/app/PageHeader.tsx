import React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { ChevronLeft, LucideIcon } from 'lucide-react-native';
import { useRouter } from 'expo-router';

import { colors, fonts, radius, spacing, typography } from '@/theme';

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  back?: boolean;
  compact?: boolean;
  dark?: boolean;
  actionIcon?: LucideIcon;
  onActionPress?: () => void;
};

export default function PageHeader({
  title,
  subtitle,
  eyebrow,
  back = false,
  compact = false,
  dark = true,
  actionIcon: ActionIcon,
  onActionPress,
}: PageHeaderProps) {
  const router = useRouter();

  const titleColor = dark ? colors.text.primary : colors.ink;
  const subtitleColor = dark ? colors.text.secondary : colors.text.inkMuted;
  const eyebrowColor = dark ? colors.gold : colors.goldDeep;
  const iconTint = dark ? colors.text.primary : colors.ink;
  const iconBackground = dark ? colors.surface.strong : colors.surface.paperMuted;
  const iconBorder = dark ? colors.border.soft : colors.border.paper;

  return (
    <View
      style={{
        marginBottom: compact ? spacing.md : spacing.lg + 2,
        flexDirection: 'row',
        alignItems: 'flex-start',
      }}>
      <View style={{ flexDirection: 'row', alignItems: 'flex-start', flex: 1 }}>
        {back ? (
          <TouchableOpacity
            onPress={() => router.back()}
            style={{
              width: compact ? 32 : 36,
              height: compact ? 32 : 36,
              borderRadius: radius.full,
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: iconBackground,
              borderWidth: 1,
              borderColor: iconBorder,
              marginRight: compact ? spacing.sm : spacing.md,
            }}>
            <ChevronLeft size={compact ? 15 : 18} color={iconTint} />
          </TouchableOpacity>
        ) : null}

        <View style={{ flex: 1 }}>
          {eyebrow ? (
            <Text
              style={{
                ...typography.labelSm,
                fontFamily: fonts.bodySm,
                color: eyebrowColor,
                textTransform: 'uppercase',
                letterSpacing: 1.1,
                marginBottom: compact ? spacing.xs : spacing.sm - 1,
              }}>
              {eyebrow}
            </Text>
          ) : null}

          <Text
            style={{
              ...typography.h3,
              fontFamily: fonts.heading,
              color: titleColor,
            }}>
            {title}
          </Text>

          {subtitle ? (
            <Text
              style={{
                ...typography.bodySm,
                fontFamily: fonts.body,
                color: subtitleColor,
                marginTop: compact ? spacing.xs : spacing.sm - 1,
              }}>
              {subtitle}
            </Text>
          ) : null}
        </View>
      </View>

      {ActionIcon && onActionPress ? (
        <TouchableOpacity
          onPress={onActionPress}
          style={{
            width: compact ? 32 : 36,
            height: compact ? 32 : 36,
            borderRadius: radius.full,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: iconBackground,
            borderWidth: 1,
            borderColor: iconBorder,
            marginLeft: compact ? spacing.sm : spacing.md,
          }}>
          <ActionIcon size={compact ? 15 : 18} color={iconTint} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
}
