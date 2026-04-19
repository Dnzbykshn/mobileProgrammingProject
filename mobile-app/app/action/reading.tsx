import React, { useMemo } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronRight, Lightbulb } from 'lucide-react-native';

import AppButton from '@/components/app/AppButton';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import SurfaceCard from '@/components/app/SurfaceCard';
import { colors, fonts, radius, spacing, typography } from '@/theme';

type ReadingVerse = {
  surah_name?: string;
  verse_number?: number;
  turkish_text?: string;
  arabic_text?: string;
  explanation?: string;
};

export default function ReadingScreen() {
  const router = useRouter();
  const { verses, index, emotion } = useLocalSearchParams<{
    verses?: string;
    index?: string;
    emotion?: string;
  }>();

  const verseList = useMemo<ReadingVerse[]>(() => {
    if (!verses) return [];
    try {
      const parsed = JSON.parse(verses);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [verses]);

  const currentIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
  const verse = verseList[currentIndex];
  const nextIndex = currentIndex + 1;
  const hasNextVerse = nextIndex < verseList.length;

  if (!verse) {
    return (
      <ScreenWrapper>
        <View style={{ flex: 1, justifyContent: 'center', paddingHorizontal: spacing.lg }}>
          <PageHeader title="Okuma" subtitle="Ayet detayı yüklenemedi." back />
          <AppButton label="Geri dön" onPress={() => router.back()} />
        </View>
      </ScreenWrapper>
    );
  }

  const title = `${verse.surah_name || 'Ayet'}${verse.verse_number ? ` ${verse.verse_number}` : ''}`;
  const translation = verse.turkish_text || 'Türkçe meal bulunamadı.';
  const arabicText = verse.arabic_text || 'Arapça metin bulunamadı.';
  const explanation = verse.explanation || 'Bu ayet mevcut bağlama göre önerildi.';

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 120,
        }}>
        <PageHeader title={title} subtitle={emotion || ''} eyebrow="Okuma" back />

        <SurfaceCard highlighted style={{ marginBottom: spacing.lg }}>
          <Text
            style={{
              ...typography.arabicLg,
              fontFamily: fonts.arabic,
              color: colors.text.primary,
              textAlign: 'right',
              marginBottom: spacing.lg,
            }}>
            {arabicText}
          </Text>

          <View
            style={{
              height: 1,
              backgroundColor: colors.border.soft,
              marginBottom: spacing.lg,
            }}
          />

          <Text
            style={{
              ...typography.h3,
              fontFamily: fonts.heading,
              color: colors.text.primary,
            }}>
            {translation}
          </Text>
        </SurfaceCard>

        <View
          style={{
            marginBottom: spacing.xl,
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            padding: spacing.lg,
          }}>
          <View
            style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm + 2 }}>
            <Lightbulb size={18} color={colors.goldDeep} />
            <Text
              style={{
                ...typography.labelLg,
                fontFamily: fonts.bodyMd,
                color: colors.goldDeep,
                marginLeft: spacing.sm,
              }}>
              Açıklama
            </Text>
          </View>

          <Text style={{ ...typography.bodyMd, fontFamily: fonts.body, color: colors.ink }}>
            {explanation}
          </Text>

          {emotion ? (
            <Text
              style={{
                ...typography.bodySm,
                fontFamily: fonts.body,
                color: colors.text.inkMuted,
                marginTop: spacing.sm + 2,
              }}>
              Bağlam: {emotion}
            </Text>
          ) : null}
        </View>

        <AppButton
          label="Sonraki ayet"
          icon={ChevronRight}
          variant={hasNextVerse ? 'primary' : 'secondary'}
          disabled={!hasNextVerse}
          onPress={() => {
            if (!hasNextVerse) {
              return;
            }

            router.replace({
              pathname: '/action/reading',
              params: {
                verses,
                index: String(nextIndex),
                emotion,
              },
            });
          }}
        />
      </ScrollView>
    </ScreenWrapper>
  );
}
