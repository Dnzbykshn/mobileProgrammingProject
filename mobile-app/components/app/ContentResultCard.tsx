import React from 'react';
import { Text, TouchableOpacity } from 'react-native';

import SurfaceCard from '@/components/app/SurfaceCard';
import { ContentItem } from '@/services/content';
import { colors, fonts, spacing, typography } from '@/theme';

interface ContentResultCardProps {
  result: ContentItem;
  onPress?: () => void;
}

export default function ContentResultCard({ result, onPress }: ContentResultCardProps) {
  const surahName = (result.metadata?.surah_name as string | undefined) || 'Ayet';
  const verseNumber = result.metadata?.verse_no;

  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress} disabled={!onPress}>
      <SurfaceCard compact highlighted>
        <Text
          style={{
            ...typography.labelSm,
            fontFamily: fonts.bodySm,
            color: colors.gold,
            marginBottom: spacing.sm - 2,
            textTransform: 'uppercase',
            letterSpacing: 0.8,
          }}>
          {verseNumber ? `${surahName} ${verseNumber}` : surahName}
        </Text>

        <Text
          style={{
            ...typography.bodySm,
            fontFamily: fonts.body,
            color: colors.text.muted,
            marginBottom: spacing.md - 2,
            textTransform: 'capitalize',
          }}>
          Kaynak: {result.source_type}
        </Text>

        {result.metadata?.arabic_text ? (
          <Text
            style={{
              ...typography.arabicMd,
              fontFamily: fonts.arabic,
              color: colors.text.primary,
              textAlign: 'right',
              marginBottom: spacing.md,
            }}>
            {String(result.metadata.arabic_text)}
          </Text>
        ) : null}

        <Text
          style={{
            ...typography.bodyLg,
            fontFamily: fonts.body,
            color: colors.text.primary,
            marginBottom: spacing.md - 2,
          }}>
          {result.content_text}
        </Text>

        {result.explanation ? (
          <Text
            style={{
              ...typography.bodyMd,
              fontFamily: fonts.body,
              color: colors.text.secondary,
            }}>
            {result.explanation}
          </Text>
        ) : null}
      </SurfaceCard>
    </TouchableOpacity>
  );
}
