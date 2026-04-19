import React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { PlayCircle } from 'lucide-react-native';

import { PathwaySummary } from '@/services/pathways';
import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

function buildProgress(pathway: PathwaySummary): number {
  const total = Math.max(pathway.total_days - 1, 1);
  return Math.max(5, Math.round((pathway.current_day / total) * 100));
}

interface PathwayCardProps {
  pathway: PathwaySummary;
  onPress: () => void;
  compact?: boolean;
}

export default function PathwayCard({ pathway, onPress, compact = false }: PathwayCardProps) {
  return (
    <TouchableOpacity activeOpacity={0.88} onPress={onPress}>
      <View
        style={{
          borderRadius: compact ? radius.lg : radius.xl,
          padding: compact ? spacing.lg : spacing.xl,
          backgroundColor: colors.surface.raised,
          borderWidth: 1,
          borderColor: colors.border.soft,
          ...shadows.sm,
        }}>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: spacing.sm + 2,
          }}>
          <View style={{ flex: 1, marginRight: spacing.md }}>
            <Text
              style={{
                ...typography.h4,
                fontFamily: fonts.bodyMd,
                color: colors.text.primary,
                fontSize: compact ? 15 : typography.h4.fontSize,
                lineHeight: compact ? 22 : typography.h4.lineHeight,
                marginBottom: pathway.topic_summary ? spacing.xs : 0,
              }}>
              {pathway.title}
            </Text>

            {pathway.topic_summary ? (
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                }}
                numberOfLines={compact ? 2 : 3}>
                {pathway.topic_summary}
              </Text>
            ) : null}
          </View>

          <PlayCircle size={compact ? 18 : 20} color={colors.gold} />
        </View>

        <View
          style={{
            height: 6,
            borderRadius: radius.full,
            overflow: 'hidden',
            backgroundColor: colors.surface.nightSoft,
            marginBottom: spacing.sm,
          }}>
          <View
            style={{
              width: `${buildProgress(pathway)}%`,
              height: '100%',
              backgroundColor: colors.gold,
            }}
          />
        </View>

        <Text
          style={{
            ...typography.bodySm,
            fontFamily: fonts.body,
          color: colors.text.secondary,
        }}>
          Gün {pathway.current_day} · {pathway.today_completed}/{pathway.today_total} görev
        </Text>
      </View>
    </TouchableOpacity>
  );
}
