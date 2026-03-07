/**
 * Memory Timeline Screen
 * Displays user's memory timeline with search, filtering, and management capabilities
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import ScreenWrapper from '@/components/ScreenWrapper';
import MemoryCard from '@/components/MemoryCard';
import {
  Memory,
  getMemories,
  searchMemories,
  deleteMemory,
  MEMORY_TYPE_CONFIG,
} from '@/services/memory';

type FilterType = 'all' | 'emotional_state' | 'life_event' | 'spiritual_preference' | 'goal' | 'progress_milestone' | 'behavioral_pattern';

export default function MemoriesScreen() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [total, setTotal] = useState(0);

  // Load memories on mount
  useEffect(() => {
    loadMemories();
  }, []);

  // Filter memories when filter changes
  useEffect(() => {
    if (activeFilter === 'all') {
      setFilteredMemories(memories);
    } else {
      setFilteredMemories(memories.filter(m => m.memory_type === activeFilter));
    }
  }, [activeFilter, memories]);

  const loadMemories = async () => {
    try {
      setIsLoading(true);
      const response = await getMemories(undefined, 50, 0);

      // Debug: Log response
      console.log('Memory response:', response);

      // Handle both array and object responses
      if (Array.isArray(response)) {
        // If backend returns array directly
        setMemories(response);
        setFilteredMemories(response);
        setTotal(response.length);
      } else if (response && typeof response === 'object') {
        // If backend returns {memories: [], total: n}
        const memories = response.memories || [];
        setMemories(memories);
        setFilteredMemories(memories);
        setTotal(response.total || memories.length);
      } else {
        // Unexpected response
        console.error('Unexpected response format:', response);
        setMemories([]);
        setFilteredMemories([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('Failed to load memories:', error);
      Alert.alert('Hata', 'Anılar yüklenemedi. Lütfen tekrar deneyin.');
      setMemories([]);
      setFilteredMemories([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadMemories();
    setIsRefreshing(false);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setFilteredMemories(memories);
      setIsSearching(false);
      return;
    }

    try {
      setIsSearching(true);
      const response = await searchMemories(searchQuery, 20);
      setFilteredMemories(response.memories);
    } catch (error) {
      console.error('Search failed:', error);
      Alert.alert('Hata', 'Arama başarısız oldu.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    try {
      await deleteMemory(memoryId);
      setMemories(prev => prev.filter(m => m.id !== memoryId));
      setFilteredMemories(prev => prev.filter(m => m.id !== memoryId));
      setTotal(prev => prev - 1);
    } catch (error) {
      console.error('Failed to delete memory:', error);
      Alert.alert('Hata', 'Anı silinemedi.');
    }
  };

  const filterChips: { key: FilterType; label: string }[] = [
    { key: 'all', label: 'Tümü' },
    { key: 'emotional_state', label: '💭 Duygusal' },
    { key: 'spiritual_preference', label: '✨ Manevi' },
    { key: 'goal', label: '🎯 Hedefler' },
    { key: 'progress_milestone', label: '🏆 Başarılar' },
    { key: 'life_event', label: '📍 Olaylar' },
  ];

  return (
    <ScreenWrapper>
      <View className="flex-1 px-5 pt-6">
        {/* Header */}
        <View className="flex-row items-center justify-between mb-6">
          <View>
            <Text className="text-white text-2xl font-bold">Manevi Yolculuğum</Text>
            <Text className="text-white/60 text-sm mt-1">
              {total} anı • Kişisel hikayeniz
            </Text>
          </View>

          <TouchableOpacity
            onPress={() => router.push('/memories/privacy' as any)}
            className="bg-[#15423F]/40 p-3 rounded-xl"
          >
            <Ionicons name="shield-checkmark" size={20} color="#5EEAD4" />
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View className="bg-[#15423F]/40 rounded-xl p-3 flex-row items-center mb-4">
          <Ionicons name="search" size={20} color="#5A7F82" />
          <TextInput
            className="flex-1 ml-3 text-white text-base"
            placeholder="Anılarında ara... (örn: kaygı, namaz)"
            placeholderTextColor="#5A7F82"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {isSearching && <ActivityIndicator size="small" color="#C0A060" />}
        </View>

        {/* Filter Chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          className="mb-4"
          contentContainerStyle={{ paddingRight: 20 }}
        >
          {filterChips.map((chip) => (
            <TouchableOpacity
              key={chip.key}
              onPress={() => setActiveFilter(chip.key)}
              className={`mr-2 px-4 py-2 rounded-full ${
                activeFilter === chip.key
                  ? 'bg-[#C0A060]'
                  : 'bg-[#15423F]/40'
              }`}
            >
              <Text
                className={`text-sm font-medium ${
                  activeFilter === chip.key ? 'text-[#0F3438]' : 'text-white/70'
                }`}
              >
                {chip.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Memory List */}
        {isLoading ? (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator size="large" color="#C0A060" />
            <Text className="text-white/60 mt-4">Anılar yükleniyor...</Text>
          </View>
        ) : filteredMemories.length === 0 ? (
          <View className="flex-1 items-center justify-center px-8">
            <Text className="text-6xl mb-4">📝</Text>
            <Text className="text-white text-lg font-semibold text-center mb-2">
              Henüz anı yok
            </Text>
            <Text className="text-white/60 text-center">
              {searchQuery
                ? 'Arama sonucu bulunamadı. Farklı kelimeler deneyin.'
                : 'Asistanla konuştukça anılarınız otomatik olarak burada toplanacak.'}
            </Text>
          </View>
        ) : (
          <ScrollView
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={isRefreshing}
                onRefresh={handleRefresh}
                tintColor="#C0A060"
              />
            }
            contentContainerStyle={{ paddingBottom: 100 }}
          >
            {filteredMemories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                onDelete={handleDelete}
              />
            ))}
          </ScrollView>
        )}
      </View>
    </ScreenWrapper>
  );
}
