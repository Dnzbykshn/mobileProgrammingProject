/**
 * Memory Privacy Dashboard
 * Shows memory statistics and privacy controls
 */
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import ScreenWrapper from '@/components/ScreenWrapper';
import { getPrivacyReport, PrivacyReport } from '@/services/memory';

export default function MemoryPrivacyScreen() {
  const [report, setReport] = useState<PrivacyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    try {
      setIsLoading(true);
      const data = await getPrivacyReport();
      setReport(data);
    } catch (error) {
      console.error('Failed to load privacy report:', error);
      Alert.alert('Hata', 'Gizlilik raporu yüklenemedi.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <ScreenWrapper>
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#C0A060" />
        </View>
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper>
      <ScrollView className="flex-1 px-5 pt-6">
        {/* Header */}
        <View className="flex-row items-center mb-6">
          <TouchableOpacity
            onPress={() => router.back()}
            className="mr-4"
          >
            <Ionicons name="arrow-back" size={24} color="#C0A060" />
          </TouchableOpacity>
          <View>
            <Text className="text-white text-2xl font-bold">Gizlilik & Verilerim</Text>
            <Text className="text-white/60 text-sm mt-1">
              Anılarınızı yönetin
            </Text>
          </View>
        </View>

        {/* Statistics Card */}
        <View className="bg-gradient-to-br from-teal-500/20 to-teal-700/20 p-5 rounded-xl mb-4">
          <View className="flex-row items-center mb-4">
            <Ionicons name="stats-chart" size={24} color="#5EEAD4" />
            <Text className="text-white font-bold text-lg ml-3">
              İstatistikler
            </Text>
          </View>

          <View className="space-y-3">
            <View className="flex-row justify-between">
              <Text className="text-white/70">Toplam Anı:</Text>
              <Text className="text-white font-semibold">{report?.total_memories || 0}</Text>
            </View>

            <View className="flex-row justify-between">
              <Text className="text-white/70">Depolama:</Text>
              <Text className="text-white font-semibold">{report?.storage_size_kb || 0} KB</Text>
            </View>

            {report?.oldest_memory && (
              <View className="flex-row justify-between">
                <Text className="text-white/70">En Eski Anı:</Text>
                <Text className="text-white font-semibold">
                  {new Date(report.oldest_memory).toLocaleDateString('tr-TR')}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Memory Types Breakdown */}
        {report?.by_type && Object.keys(report.by_type).length > 0 && (
          <View className="bg-[#15423F]/40 p-5 rounded-xl mb-4">
            <Text className="text-white font-bold text-lg mb-4">
              Anı Türleri
            </Text>

            {Object.entries(report.by_type).map(([type, count]) => (
              <View key={type} className="flex-row justify-between mb-3">
                <Text className="text-white/70 capitalize">
                  {type.replace('_', ' ')}:
                </Text>
                <Text className="text-white font-semibold">{count}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Privacy Info */}
        <View className="bg-[#15423F]/40 p-5 rounded-xl mb-4">
          <View className="flex-row items-center mb-3">
            <Ionicons name="shield-checkmark" size={20} color="#5EEAD4" />
            <Text className="text-white font-semibold ml-2">
              Gizliliğiniz Korunuyor
            </Text>
          </View>

          <Text className="text-white/70 text-sm leading-6">
            • Anılarınız tamamen kişiseldir ve yalnızca size aittir{'\n'}
            • Verileriniz şifrelenmiş olarak saklanır{'\n'}
            • Hassas anılar özel olarak işaretlenir{'\n'}
            • Otomatik süre dolumu politikaları vardır{'\n'}
            • İstediğiniz zaman tüm anılarınızı silebilirsiniz
          </Text>
        </View>

        {/* Danger Zone - Placeholder */}
        <View className="bg-red-900/20 border border-red-500/30 p-5 rounded-xl mb-20">
          <View className="flex-row items-center mb-3">
            <Ionicons name="warning" size={20} color="#EF4444" />
            <Text className="text-red-400 font-semibold ml-2">
              Tehlikeli Alan
            </Text>
          </View>

          <Text className="text-white/70 text-sm mb-4">
            Tüm anılarınızı kalıcı olarak silmek isterseniz, profil sayfanızdan bu işlemi yapabilirsiniz.
          </Text>

          <TouchableOpacity
            className="bg-red-600/30 py-3 rounded-lg"
            onPress={() => Alert.alert(
              'Yakında',
              'Toplu silme özelliği yakında eklenecek.'
            )}
          >
            <Text className="text-red-400 text-center font-semibold">
              Tüm Anıları Sil
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenWrapper>
  );
}
