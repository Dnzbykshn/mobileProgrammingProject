import React from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { ArrowRight } from 'lucide-react-native';

import ArabesquePattern from '@/components/app/ArabesquePattern';
import ScreenWrapper from '@/components/ScreenWrapper';
import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

type AuthShellProps = {
  title: string;
  subtitle: string;
  footerPrompt: string;
  footerActionLabel: string;
  onFooterPress: () => void;
  children: React.ReactNode;
};

export default function AuthShell({
  title,
  subtitle,
  footerPrompt,
  footerActionLabel,
  onFooterPress,
  children,
}: AuthShellProps) {
  return (
    <ScreenWrapper
      backgroundColor={colors.night}
      statusBarStyle="light"
      edges={['top', 'left', 'right', 'bottom']}>
      <ArabesquePattern dark />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{
            flexGrow: 1,
            justifyContent: 'center',
            paddingHorizontal: spacing.xl,
            paddingTop: spacing.lg,
            paddingBottom: spacing.xxl,
          }}>
          <View style={{ marginBottom: spacing.xl }}>
            <Text
              style={{
                ...typography.h1,
                fontFamily: fonts.heading,
                color: colors.text.primary,
                marginBottom: spacing.sm,
              }}>
              {title}
            </Text>

            <Text
              style={{
                ...typography.bodyLg,
                fontFamily: fonts.body,
                color: colors.text.secondary,
                maxWidth: 320,
              }}>
              {subtitle}
            </Text>
          </View>

          <View
            style={{
              borderRadius: radius.xxl,
              borderWidth: 1,
              borderColor: colors.border.soft,
              backgroundColor: colors.surface.raised,
              padding: spacing.xl,
              ...shadows.lg,
            }}>
            {children}
          </View>

          <TouchableOpacity
            onPress={onFooterPress}
            activeOpacity={0.85}
            style={{
              alignSelf: 'center',
              alignItems: 'center',
              marginTop: spacing.xl,
              paddingHorizontal: spacing.md,
              paddingVertical: spacing.sm,
            }}>
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
                color: colors.text.secondary,
              }}>
              {footerPrompt}
            </Text>

            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: spacing.xs + 1 }}>
              <Text
                style={{
                  ...typography.labelLg,
                  fontFamily: fonts.bodyMd,
                  color: colors.gold,
                  marginRight: spacing.xs + 2,
                }}>
                {footerActionLabel}
              </Text>
              <ArrowRight size={14} color={colors.gold} />
            </View>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </ScreenWrapper>
  );
}
