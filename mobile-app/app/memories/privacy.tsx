import React, { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, Text, View } from 'react-native';

import AppChip from '@/components/app/AppChip';
import EmptyState from '@/components/app/EmptyState';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import SectionTitle from '@/components/app/SectionTitle';
import { getPrivacyReport, PrivacyReport } from '@/services/memory';
import { colors, fonts, radius, spacing, typography } from '@/theme';

const TYPE_LABELS: Record<string, string> = {
  emotional_state: 'Duygusal durum',
  life_event: 'Yaşam olayı',
  spiritual_preference: 'Manevi tercih',
  goal: 'Hedef',
  progress_milestone: 'İlerleme',
  behavioral_pattern: 'Davranış örüntüsü',
};

export default function MemoryPrivacyScreen() {
  const [report, setReport] = useState<PrivacyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadReport = async () => {
      try {
        setIsLoading(true);
        const nextReport = await getPrivacyReport();
        setReport(nextReport);
      } finally {
        setIsLoading(false);
      }
    };

    void loadReport();
  }, []);

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: spacing.xxxl,
        }}>
        <PageHeader title="Gizlilik" subtitle="Bellek kayıtlarının özeti." eyebrow="Anılar" back />

        {isLoading ? (
          <View style={{ paddingTop: spacing.huge, alignItems: 'center' }}>
            <ActivityIndicator size="large" color={colors.gold} />
          </View>
        ) : (
          <>
            <View
              style={{
                borderRadius: radius.xl,
                padding: spacing.lg,
                borderWidth: 1,
                borderColor: colors.border.paper,
                backgroundColor: colors.surface.paperRaised,
                marginBottom: spacing.md,
              }}>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.inkMuted,
                  marginBottom: spacing.sm,
                }}>
                Toplam kayıt
              </Text>
              <Text
                style={{
                  ...typography.display,
                  fontFamily: fonts.heading,
                  color: colors.ink,
                }}>
                {report?.total_memories || 0}
              </Text>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.inkMuted,
                  marginTop: spacing.sm,
                }}>
                Depolama: {report?.storage_size_kb || 0} KB
              </Text>
              {report?.oldest_memory ? (
                <Text
                  style={{
                    ...typography.bodySm,
                    fontFamily: fonts.body,
                    color: colors.text.inkMuted,
                    marginTop: spacing.xs,
                  }}>
                  En eski kayıt: {new Date(report.oldest_memory).toLocaleDateString('tr-TR')}
                </Text>
              ) : null}
            </View>

            <View
              style={{
                borderRadius: radius.xl,
                padding: spacing.lg,
                borderWidth: 1,
                borderColor: colors.border.paper,
                backgroundColor: colors.surface.paperRaised,
                marginBottom: spacing.md,
              }}>
              <SectionTitle title="Tür dağılımı" />

              {report?.by_type && Object.keys(report.by_type).length > 0 ? (
                <View style={{ gap: spacing.sm + 2 }}>
                  {Object.entries(report.by_type).map(([type, count]) => (
                    <View
                      key={type}
                      style={{
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}>
                      <Text
                        style={{
                          ...typography.bodyMd,
                          fontFamily: fonts.body,
                          color: colors.ink,
                        }}>
                        {TYPE_LABELS[type] || type}
                      </Text>
                      <AppChip label={String(count)} />
                    </View>
                  ))}
                </View>
              ) : (
                <EmptyState message="Kayıt bulunmuyor." compact={false} />
              )}
            </View>

            <View
              style={{
                borderRadius: radius.xl,
                padding: spacing.lg,
                borderWidth: 1,
                borderColor: colors.border.paper,
                backgroundColor: colors.surface.paperRaised,
              }}>
              <Text
                style={{
                  ...typography.labelLg,
                  fontFamily: fonts.bodyMd,
                  color: colors.ink,
                  marginBottom: spacing.sm,
                }}>
                Bilgi
              </Text>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.inkMuted,
                }}>
                Bellek kayıtları yalnızca hesabınla ilişkilidir. Bu ekran yalnızca özet bilgi
                gösterir.
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </ScreenWrapper>
  );
}
