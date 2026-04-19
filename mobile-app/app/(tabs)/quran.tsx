import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Search } from 'lucide-react-native';
import { useRouter } from 'expo-router';

import AppButton from '@/components/app/AppButton';
import AppChip from '@/components/app/AppChip';
import ContentResultCard from '@/components/app/ContentResultCard';
import EmptyState from '@/components/app/EmptyState';
import { ArabicPhrase, GeometricRosette, IslamicDivider } from '@/components/app/IslamicOrnaments';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import { ContentItem, getContentSources, searchContent } from '@/services/content';
import { colors, fonts, radius, spacing, typography } from '@/theme';

function mapVerseResult(result: ContentItem) {
  return {
    surah_name: result.metadata?.surah_name as string | undefined,
    verse_number: result.metadata?.verse_no as number | undefined,
    turkish_text: result.content_text,
    arabic_text: result.metadata?.arabic_text as string | undefined,
    explanation: result.explanation,
  };
}

export default function QuranScreen() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ContentItem[]>([]);
  const [availableSources, setAvailableSources] = useState<string[]>(['quran']);
  const [selectedSource, setSelectedSource] = useState<string>('quran');
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadSources = async () => {
      try {
        const sources = await getContentSources();
        if (!mounted || sources.length === 0) {
          return;
        }

        setAvailableSources(sources);
        if (!sources.includes(selectedSource)) {
          setSelectedSource(sources[0]);
        }
      } catch {
        // keep quran fallback
      }
    };

    void loadSources();

    return () => {
      mounted = false;
    };
  }, [selectedSource]);

  const sourceLabel = useMemo(() => {
    if (selectedSource === 'quran') return 'Kuran';
    if (selectedSource === 'hadith') return 'Hadis';
    if (selectedSource === 'book') return 'Kitap';
    return selectedSource;
  }, [selectedSource]);

  const handleSearch = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setError(null);
      return;
    }

    try {
      setIsSearching(true);
      setError(null);
      const nextResults = await searchContent(trimmed, {
        limit: 6,
        sourceTypes: [selectedSource],
      });
      setResults(nextResults);
    } catch (searchError) {
      const message =
        searchError && typeof searchError === 'object' && 'message' in searchError
          ? String(searchError.message)
          : 'Arama tamamlanamadı.';
      setResults([]);
      setError(message);
    } finally {
      setIsSearching(false);
    }
  }, [query, selectedSource]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timeout = setTimeout(() => {
      void handleSearch();
    }, 160);

    return () => clearTimeout(timeout);
  }, [handleSearch, query, selectedSource]);

  return (
    <ScreenWrapper withDecoration={false}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{
            paddingHorizontal: spacing.lg,
            paddingTop: spacing.lg,
            paddingBottom: 120,
          }}
          keyboardShouldPersistTaps="always"
          keyboardDismissMode="none">
        <View style={{ alignItems: 'center', marginBottom: spacing.md }}>
          <GeometricRosette size={48} opacity={0.5} />
          <ArabicPhrase
            text="بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"
            size={15}
            opacity={0.6}
          />
        </View>

        <PageHeader
          title="İçerik"
          subtitle="Kaynağa göre ara ve aynı formatta görüntüle."
          eyebrow="Arama"
        />
        <IslamicDivider opacity={0.18} />

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.soft,
            backgroundColor: colors.surface.raised,
            padding: spacing.lg,
            marginBottom: spacing.md,
          }}>
          <View
            style={{
              minHeight: 56,
              borderRadius: radius.lg,
              borderWidth: 1,
              borderColor: colors.border.soft,
              backgroundColor: colors.surface.nightSoft,
              paddingHorizontal: spacing.lg,
              flexDirection: 'row',
              alignItems: 'center',
            }}>
            <Search size={18} color={colors.text.secondary} />
            <TextInput
              value={query}
              onChangeText={setQuery}
              onSubmitEditing={() => {
                void handleSearch();
              }}
              placeholder="Kelime veya konu ara"
              placeholderTextColor={colors.text.muted}
              returnKeyType="search"
              selectionColor={colors.gold}
              cursorColor={colors.gold}
              keyboardAppearance="dark"
              underlineColorAndroid="transparent"
              style={{
                flex: 1,
                ...typography.bodyLg,
                fontFamily: fonts.body,
                color: colors.text.primary,
                paddingVertical: spacing.lg,
                marginLeft: spacing.md,
              }}
            />
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: spacing.sm, marginTop: spacing.md }}>
            {availableSources.map((source) => (
              <TouchableOpacity
                key={source}
                activeOpacity={0.88}
                onPress={() => setSelectedSource(source)}>
                <AppChip
                  label={
                    source === 'quran'
                      ? 'Kuran'
                      : source === 'hadith'
                        ? 'Hadis'
                        : source === 'book'
                          ? 'Kitap'
                          : source
                  }
                  active={selectedSource === source}
                />
              </TouchableOpacity>
            ))}
          </ScrollView>

          <AppButton
            label={`${sourceLabel} içinde ara`}
            onPress={() => {
              void handleSearch();
            }}
            loading={isSearching}
            style={{ marginTop: spacing.md }}
          />
        </View>

        {error ? (
          <View
            style={{
              borderRadius: radius.xl,
              borderWidth: 1,
              borderColor: colors.border.danger,
              backgroundColor: colors.surface.dangerSoft,
              padding: spacing.lg,
              marginBottom: spacing.md,
            }}>
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
                color: colors.text.danger,
              }}>
              {error}
            </Text>
          </View>
        ) : null}

        {results.length === 0 && !isSearching ? (
          <EmptyState message="Arama sonucu burada görünecek." />
        ) : (
          <View style={{ gap: spacing.md }}>
            {results.map((result, index) => {
              const surahName = (result.metadata?.surah_name as string | undefined) || 'Ayet';
              const verseNumber = result.metadata?.verse_no;

              return (
                <ContentResultCard
                  key={`${surahName}-${verseNumber ?? index}-${index}`}
                  result={result}
                  onPress={
                    result.source_type === 'quran'
                      ? () =>
                          router.push({
                            pathname: '/action/reading',
                            params: {
                              verses: JSON.stringify([mapVerseResult(result)]),
                              index: '0',
                            },
                          })
                      : undefined
                  }
                />
              );
            })}
          </View>
        )}
        </ScrollView>
      </KeyboardAvoidingView>
    </ScreenWrapper>
  );
}
