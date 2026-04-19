import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, View } from 'react-native';
import { router } from 'expo-router';
import { Search, ShieldCheck } from 'lucide-react-native';

import AppChip from '@/components/app/AppChip';
import AppInput from '@/components/app/AppInput';
import EmptyState from '@/components/app/EmptyState';
import MemoryCard from '@/components/MemoryCard';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import { colors, radius, spacing } from '@/theme';
import { Memory, deleteMemory, getMemories, searchMemories } from '@/services/memory';

type FilterType =
  | 'all'
  | 'emotional_state'
  | 'life_event'
  | 'spiritual_preference'
  | 'goal'
  | 'progress_milestone'
  | 'behavioral_pattern';

const FILTERS: { key: FilterType; label: string }[] = [
  { key: 'all', label: 'Tümü' },
  { key: 'emotional_state', label: 'Duygusal' },
  { key: 'spiritual_preference', label: 'Manevi' },
  { key: 'goal', label: 'Hedef' },
  { key: 'progress_milestone', label: 'Başarı' },
  { key: 'life_event', label: 'Olay' },
];

export default function MemoriesScreen() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [error, setError] = useState<string | null>(null);

  const filteredMemories = useMemo(() => {
    if (activeFilter === 'all') return memories;
    return memories.filter((memory) => memory.memory_type === activeFilter);
  }, [activeFilter, memories]);

  const loadMemories = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getMemories(undefined, 50, 0);
      setMemories(response.memories || []);
    } catch (loadError) {
      console.error('Failed to load memories:', loadError);
      setMemories([]);
      setError('Anılar yüklenemedi.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMemories();
  }, [loadMemories]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadMemories();
    setIsRefreshing(false);
  }, [loadMemories]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      await loadMemories();
      return;
    }

    try {
      setError(null);
      const response = await searchMemories(searchQuery, 20);
      setMemories(response.memories);
    } catch (searchError) {
      console.error('Search failed:', searchError);
      setError('Arama tamamlanamadı.');
    }
  };

  const handleDelete = async (memoryId: string) => {
    try {
      await deleteMemory(memoryId);
      setMemories((previous) => previous.filter((memory) => memory.id !== memoryId));
    } catch (deleteError) {
      console.error('Failed to delete memory:', deleteError);
      Alert.alert('Hata', 'Anı silinemedi.');
    }
  };

  return (
    <ScreenWrapper>
      <View
        style={{
          flex: 1,
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 110,
        }}>
        <PageHeader
          title="Anılar"
          subtitle={`${filteredMemories.length} kayıt`}
          eyebrow="Hafıza"
          actionIcon={ShieldCheck}
          onActionPress={() => router.push('/memories/privacy' as never)}
        />

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.soft,
            backgroundColor: colors.surface.raised,
            padding: spacing.md,
            marginBottom: spacing.md,
          }}>
          <AppInput
            icon={Search}
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={() => {
              void handleSearch();
            }}
            returnKeyType="search"
            placeholder="Anılarda ara"
          />
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ marginBottom: spacing.md }}
          contentContainerStyle={{ gap: spacing.sm, paddingRight: spacing.md }}>
          {FILTERS.map((filter) => {
            const active = activeFilter === filter.key;
            return (
              <AppChip
                key={filter.key}
                label={filter.label}
                active={active}
                onPress={() => setActiveFilter(filter.key)}
              />
            );
          })}
        </ScrollView>

        {isLoading ? (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator size="large" color={colors.gold} />
          </View>
        ) : (
          <ScrollView
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={isRefreshing}
                onRefresh={handleRefresh}
                tintColor={colors.gold}
              />
            }
            contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xl }}>
            {error ? <EmptyState message={error} /> : null}

            {filteredMemories.length === 0 ? (
              <EmptyState
                message={searchQuery ? 'Arama sonucu bulunamadı.' : 'Henüz anı kaydı bulunmuyor.'}
              />
            ) : (
              filteredMemories.map((memory) => (
                <MemoryCard key={memory.id} memory={memory} onDelete={handleDelete} />
              ))
            )}
          </ScrollView>
        )}
      </View>
    </ScreenWrapper>
  );
}
