import React, { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';

import AppButton from '@/components/app/AppButton';
import EmptyState from '@/components/app/EmptyState';
import PathwayCard from '@/components/app/PathwayCard';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import { getActivePathways, PathwaySummary } from '@/services/pathways';
import { colors, fonts, radius, spacing, typography } from '@/theme';

export default function ExploreScreen() {
  const router = useRouter();
  const [pathways, setPathways] = useState<PathwaySummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getActivePathways();
      setPathways(data);
    } catch (loadError) {
      const message =
        loadError && typeof loadError === 'object' && 'message' in loadError
          ? String(loadError.message)
          : 'Veriler yüklenemedi.';
      setPathways([]);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadData();
    }, [loadData])
  );

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 120,
        }}>
        <PageHeader
          title="Yollar"
          subtitle="Takip ettiğin manevi yolculukları buradan sürdürebilirsin."
          eyebrow="Takip"
        />

        {isLoading ? (
          <View style={{ paddingTop: spacing.huge, alignItems: 'center' }}>
            <ActivityIndicator size="large" color={colors.gold} />
          </View>
        ) : (
          <>
            {error ? (
              <View
                style={{
                  borderRadius: radius.xl,
                  padding: spacing.lg,
                  borderWidth: 1,
                  borderColor: colors.border.danger,
                  backgroundColor: colors.surface.dangerSoft,
                  marginBottom: spacing.lg,
                }}>
                <Text
                  style={{
                    ...typography.bodyMd,
                    fontFamily: fonts.body,
                    color: colors.text.danger,
                    marginBottom: spacing.md,
                  }}>
                  {error}
                </Text>

                <AppButton
                  label="Tekrar dene"
                  variant="secondary"
                  onPress={() => void loadData()}
                />
              </View>
            ) : null}

            {pathways.length === 0 ? (
              <EmptyState message="Aktif yol bulunmuyor." />
            ) : (
              <View style={{ gap: spacing.md }}>
                {pathways.map((pathway) => (
                  <PathwayCard
                    key={pathway.pathway_id}
                    pathway={pathway}
                    onPress={() =>
                      router.push({
                        pathname: '/action/pathway',
                        params: { pathwayId: pathway.pathway_id },
                      })
                    }
                  />
                ))}
              </View>
            )}
          </>
        )}
      </ScrollView>
    </ScreenWrapper>
  );
}
