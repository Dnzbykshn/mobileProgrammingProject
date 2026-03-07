import { View, Text, FlatList, TouchableOpacity } from 'react-native';
import { useState, useCallback } from 'react';
import { useFocusEffect, useRouter } from 'expo-router';
import ScreenWrapper from '@/components/ScreenWrapper';
import { BookOpen, Trash2, Calendar, ChevronRight, Sparkles, Play, CheckCircle } from 'lucide-react-native';
import { getPrescriptionHistory, PrescriptionSummary, getLocalPrescriptions } from '@/services/prescriptions';
import { getActiveJourneys, JourneySummary } from '@/services/plans';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function HistoryScreen() {
    const router = useRouter();
    const [prescriptions, setPrescriptions] = useState<PrescriptionSummary[]>([]);
    const [activeJourneys, setActiveJourneys] = useState<JourneySummary[]>([]);

    useFocusEffect(
        useCallback(() => {
            loadHistory();
            loadActiveJourneys();
        }, [])
    );

    const loadActiveJourneys = async () => {
        try {
            const journeys = await getActiveJourneys();
            setActiveJourneys(journeys);
        } catch (e) {
            console.log('Failed to load active journeys', e);
            setActiveJourneys([]);
        }
    };

    const loadHistory = async () => {
        try {
            const data = await getPrescriptionHistory();
            const localData = await getLocalPrescriptions();
            const apiIds = new Set(data.map(d => d.id));
            const localOnly = localData.filter(l => !apiIds.has(l.id));
            setPrescriptions([...data, ...localOnly]);
        } catch (e) {
            console.error(e);
            const localData = await getLocalPrescriptions();
            setPrescriptions(localData);
        }
    };

    const clearHistory = async () => {
        await AsyncStorage.removeItem('saved_prescriptions');
        setPrescriptions([]);
    };

    // Helper to calculate progress for a journey
    const calculateProgress = (journey: JourneySummary) => {
        const progress = Math.round((journey.current_day / (journey.total_days - 1)) * 100);
        return Math.max(progress, 5); // Min 5% for visibility
    };

    return (
        <ScreenWrapper>
            {/* Header */}
            <View className="px-6 py-4 flex-row justify-between items-center bg-[#113835]/40 border-b border-[#1F5550]/30">
                <Text className="text-[#E5E9E9] text-xl font-serif font-bold">Yolculukların</Text>
                {prescriptions.length > 0 && (
                    <TouchableOpacity onPress={clearHistory} className="p-2 bg-[#1A4642] rounded-full">
                        <Trash2 color="#FFD700" size={20} />
                    </TouchableOpacity>
                )}
            </View>

            <FlatList
                contentContainerStyle={{ padding: 24, paddingBottom: 100 }}
                data={prescriptions}
                keyExtractor={item => item.id}
                ListHeaderComponent={
                    <>
                        {/* Active Journeys Section */}
                        {activeJourneys.length > 0 && (
                            <View className="mb-6">
                                <Text className="text-[#E5E9E9] text-sm font-bold mb-3 opacity-70">
                                    AKTİF YOLCULUKLAR
                                </Text>
                                {activeJourneys.map(journey => {
                                    const progress = calculateProgress(journey);
                                    return (
                                        <TouchableOpacity
                                            key={journey.plan_id}
                                            onPress={() => router.push({ pathname: '/action/plan', params: { planId: journey.plan_id } })}
                                            className="bg-[#113835] mb-4 rounded-2xl overflow-hidden border-2 border-[#FFD700]/30"
                                            style={{ shadowColor: '#FFD700', shadowOpacity: 0.15, shadowRadius: 12 }}
                                        >
                                            <View className="p-5">
                                                <View className="flex-row items-center mb-3">
                                                    <View className="bg-[#FFD700]/20 p-2.5 rounded-xl mr-3">
                                                        <Play size={20} color="#FFD700" fill="#FFD700" />
                                                    </View>
                                                    <View className="flex-1">
                                                        <Text className="text-[#E5E9E9] text-lg font-serif font-bold">
                                                            {journey.title}
                                                        </Text>
                                                        {journey.topic_summary && (
                                                            <Text className="text-[#436F65] text-xs mt-1">
                                                                {journey.topic_summary}
                                                            </Text>
                                                        )}
                                                    </View>
                                                    <ChevronRight size={20} color="#FFD700" />
                                                </View>

                                                {/* Progress bar */}
                                                <View className="bg-[#0B3130] h-2 rounded-full overflow-hidden mb-2">
                                                    <View
                                                        className="bg-[#FFD700] h-full rounded-full"
                                                        style={{ width: `${progress}%` }}
                                                    />
                                                </View>

                                                <View className="flex-row justify-between items-center">
                                                    <Text className="text-[#436F65] text-xs">
                                                        Gün {journey.current_day} / {journey.total_days - 1}
                                                    </Text>
                                                    <View className="flex-row items-center">
                                                        <CheckCircle size={12} color="#436F65" />
                                                        <Text className="text-[#436F65] text-xs ml-1">
                                                            {journey.today_completed}/{journey.today_total} görev
                                                        </Text>
                                                    </View>
                                                </View>
                                            </View>
                                        </TouchableOpacity>
                                    );
                                })}
                            </View>
                        )}

                        {/* Prescription History Header */}
                        {prescriptions.length > 0 && (
                            <Text className="text-[#E5E9E9] text-sm font-bold mb-3 opacity-70 mt-4">
                                GEÇMİŞ rutinLER
                            </Text>
                        )}
                    </>
                }
                ListEmptyComponent={
                    activeJourneys.length === 0 && prescriptions.length === 0 ? (
                        <View className="items-center justify-center mt-20 opacity-70">
                            <BookOpen color="#436F65" size={64} />
                            <Text className="text-[#E5E9E9] text-lg font-bold mt-6">Henüz Kayıt Yok</Text>
                            <Text className="text-[#C0CAC9] mt-2 text-center leading-6 max-w-[250px]">
                                Manevi sohbet sırasında aldığın yolculuklar burada saklanır.
                            </Text>
                        </View>
                    ) : null
                }
                renderItem={({ item }) => (
                    <View className="bg-[#113835]/40 p-5 rounded-2xl mb-6 border border-[#436F65]/20" style={{ shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 8 }}>

                        <View className="flex-row justify-between items-start mb-4">
                            <View className="flex-row items-center">
                                <View className="bg-[#1A4642]/50 p-2 rounded-lg mr-3">
                                    <Sparkles size={20} color="#FFD700" />
                                </View>
                                <View>
                                    <Text className="text-[#E5E9E9] text-lg font-serif font-bold">{item.title}</Text>
                                    <View className="flex-row items-center mt-1">
                                        <Calendar size={12} color="#436F65" />
                                        <Text className="text-[#436F65] text-xs ml-1">{item.date || item.created_at || '-'}</Text>
                                    </View>
                                </View>
                            </View>
                        </View>

                        <Text className="text-[#C0CAC9] text-sm leading-6 mb-4 border-l-2 border-[#436F65] pl-3">
                            {item.description}
                        </Text>

                        {item.items && item.items.length > 0 && (
                            <View className="bg-[#0B3130]/50 p-4 rounded-xl mb-4 border border-[#1F5550]">
                                {item.items.slice(0, 2).map((pi: any, idx: number) => (
                                    <Text key={idx} className="text-[#E5E9E9] text-sm mb-1">• {pi.text}</Text>
                                ))}
                                {item.items.length > 2 && <Text className="text-[#436F65] text-xs mt-1">ve daha fazlası...</Text>}
                            </View>
                        )}

                        <TouchableOpacity
                            onPress={() => router.push('/action/prescription')}
                            className="bg-[#15423F] py-3 rounded-xl border border-[#FFD700] flex-row justify-center items-center active:bg-[#1A4642]"
                        >
                            <Text className="text-[#FFD700] font-bold mr-2">Tekrar İncele</Text>
                            <ChevronRight size={16} color="#FFD700" />
                        </TouchableOpacity>
                    </View>
                )}
            />
        </ScreenWrapper>
    );
}
