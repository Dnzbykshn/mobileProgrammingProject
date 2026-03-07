import React, { useMemo } from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { X, Share2, Play, Calendar, Sparkles, BookOpen, Heart } from 'lucide-react-native';

// Map English emotion → Turkish
const EMOTION_TR: Record<string, string> = {
    'Anxiety': 'Kaygı', 'Depression': 'Hüzün', 'Anger': 'Öfke',
    'Fear': 'Korku', 'Loneliness': 'Yalnızlık', 'Grief': 'Yas',
    'Stress': 'Stres', 'Sadness': 'Üzüntü', 'Hopelessness': 'Umutsuzluk',
    'Guilt': 'Suçluluk', 'Shame': 'Utanç', 'Jealousy': 'Kıskançlık',
    'Kaygı': 'Kaygı', 'Hüzün': 'Hüzün', 'Öfke': 'Öfke', 'Korku': 'Korku',
    'Stres': 'Stres', 'Üzüntü': 'Üzüntü', 'Umutsuzluk': 'Umutsuzluk',
};

// Map emotion → journey_type for plan creation
const EMOTION_TO_JOURNEY: Record<string, string> = {
    'Kaygı': 'anxiety_management',
    'Korku': 'anxiety_management',
    'Hüzün': 'grief_healing',
    'Üzüntü': 'grief_healing',
    'Yas': 'grief_healing',
    'Öfke': 'anger_control',
    'Stres': 'anxiety_management',
    'Umutsuzluk': 'grief_healing',
};

export default function PrescriptionScreen() {
    const router = useRouter();
    const { data } = useLocalSearchParams<{ data: string }>();

    // Parse prescription data from route params
    const rx = useMemo(() => {
        try {
            return data ? JSON.parse(data) : null;
        } catch {
            return null;
        }
    }, [data]);

    // Extract fields with fallbacks
    const diagnosis = rx?.diagnosis || {};
    const emotionRaw = diagnosis.emotional_state || 'Kaygı';
    const emotion = EMOTION_TR[emotionRaw] || emotionRaw;
    const rootCause = diagnosis.root_cause || '';
    const advice = rx?.advice || '';
    const journeyType = EMOTION_TO_JOURNEY[emotion] || 'spiritual_growth';

    // Extract prescription items
    const verses = rx?.verses || [];
    const esmas = rx?.esmas || [];
    const duas = rx?.duas || [];

    // Build quick routine items from first items
    const quickRoutine: string[] = [];
    quickRoutine.push('3 Derin Nefes Al');
    if (verses.length > 0) quickRoutine.push(verses[0]?.surah_name || 'Kısa Sure Oku');
    if (duas.length > 0) quickRoutine.push(duas[0]?.name || 'Dua Et');

    return (
        <SafeAreaView className="flex-1 bg-[#0B3130]" edges={['top']}>
            {/* Header */}
            <View className="flex-row justify-between items-center p-4 border-b border-[#113835] bg-[#113835]">
                <TouchableOpacity onPress={() => router.back()} className="p-2">
                    <X color="#C0CAC9" size={24} />
                </TouchableOpacity>
                <Text className="text-[#E5E9E9] text-lg font-serif font-bold">Senin İçin Hazırlandı</Text>
                <TouchableOpacity className="p-2">
                    <Share2 color="#C0CAC9" size={24} />
                </TouchableOpacity>
            </View>

            <ScrollView className="flex-1" contentContainerStyle={{ padding: 24, paddingBottom: 40 }}>

                {/* BÖLÜM A: TEŞHİS */}
                <View className="bg-[#113835] p-5 rounded-xl border border-[#436F65] mb-6">
                    <View className="flex-row items-center mb-3">
                        <Text className="text-2xl mr-3">🍃</Text>
                        <Text className="text-[#E5E9E9] text-base font-medium flex-1">
                            Bu durum {emotion} ile ilgili görünüyor.
                        </Text>
                    </View>
                    {rootCause ? (
                        <Text className="text-[#C0CAC9] text-sm italic">{rootCause}</Text>
                    ) : (
                        <Text className="text-[#C0CAC9] text-sm italic">
                            Yalnız değilsin, Allah (c.c) sana şah damarından daha yakın.
                        </Text>
                    )}
                </View>


                {/* BÖLÜM C: AYETLER */}
                {verses.length > 0 && (
                    <>
                        <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-4">Kalbine İyi Gelecek Ayetler</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-8 -mx-6 px-6">
                            {verses.map((verse: any, idx: number) => (
                                <TouchableOpacity
                                    key={idx}
                                    onPress={() => router.push('/action/reading')}
                                    className={`bg-[#113835] w-[280px] p-5 rounded-2xl border border-[#436F65] mr-3 ${idx > 0 ? 'opacity-80' : ''}`}
                                >
                                    <Text className="text-[#FFD700] text-xs font-bold mb-3">
                                        {verse.surah_name || 'Ayet'} {verse.verse_number || ''}
                                    </Text>
                                    <Text className="text-[#E5E9E9] text-lg font-serif mb-4 leading-6">
                                        "{verse.turkish_text || verse.text || 'Ayet metni'}"
                                    </Text>
                                    <View className="self-start bg-[#0B3130] px-3 py-1 rounded-full border border-[#436F65]">
                                        <Text className="text-[#C0CAC9] text-xs">{emotion} için</Text>
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </ScrollView>
                    </>
                )}

                {/* BÖLÜM D: ESMA LİSTESİ */}
                {esmas.length > 0 && (
                    <>
                        <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-2">Önerilen Esmalar</Text>
                        <Text className="text-[#436F65] text-xs italic mb-4">(İsteğe Bağlı)</Text>

                        <View className="space-y-3 mb-8">
                            {esmas.map((esma: any, idx: number) => (
                                <View key={idx} className="bg-[#113835] p-4 rounded-xl border border-[#436F65] flex-row justify-between items-center">
                                    <View className="flex-1">
                                        <Text className="text-[#E5E9E9] text-base font-medium">{esma.name || esma.esma_name || 'Esma'}</Text>
                                        {esma.meaning && (
                                            <Text className="text-[#C0CAC9] text-xs mt-1">{esma.meaning}</Text>
                                        )}
                                    </View>
                                    <View className="flex-row items-center">
                                        <Text className="text-[#FFD700] font-bold mr-2">{esma.recommended_count || 33}x</Text>
                                        <Sparkles size={16} color="#436F65" />
                                    </View>
                                </View>
                            ))}
                            <Text className="text-[#436F65] text-xs italic text-center mt-2">Sayılar zorunlu değildir, rutin oluşturmak içindir.</Text>
                        </View>
                    </>
                )}

                {/* BÖLÜM E: DUALAR */}
                {duas.length > 0 && (
                    <>
                        <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-4">Önerilen Dualar</Text>
                        <View className="space-y-3 mb-8">
                            {duas.map((dua: any, idx: number) => (
                                <View key={idx} className="bg-[#113835] p-4 rounded-xl border border-[#436F65]">
                                    <View className="flex-row items-center mb-2">
                                        <Heart size={14} color="#FFD700" />
                                        <Text className="text-[#FFD700] text-xs font-bold ml-2">{dua.name || 'Dua'}</Text>
                                    </View>
                                    {dua.arabic_text && (
                                        <Text className="text-[#E5E9E9] text-lg text-right mb-2 leading-8">{dua.arabic_text}</Text>
                                    )}
                                    {(dua.turkish_text || dua.text) && (
                                        <Text className="text-[#C0CAC9] text-sm italic">"{dua.turkish_text || dua.text}"</Text>
                                    )}
                                </View>
                            ))}
                        </View>
                    </>
                )}

                {/* BÖLÜM F: TAVSIYE */}
                {advice ? (
                    <View className="bg-[#113835] p-5 rounded-xl border border-[#436F65] mb-8">
                        <View className="flex-row items-center mb-3">
                            <BookOpen size={16} color="#FFD700" />
                            <Text className="text-[#FFD700] text-sm font-bold ml-2">Manevi Tavsiye</Text>
                        </View>
                        <Text className="text-[#C0CAC9] text-sm leading-5">{advice}</Text>
                    </View>
                ) : null}

                {/* BÖLÜM G: YOLCULUĞA GİT */}
                <View className="bg-[#1A4642] p-6 rounded-2xl border-2 border-[#FFD700] items-center mb-8">
                    <Calendar color="#FFD700" size={32} className="mb-3" />
                    <Text className="text-[#E5E9E9] text-base text-center font-medium mb-5 leading-6">
                        Senin için 8 günlük bir manevi yolculuk hazırlandı.
                    </Text>
                    <TouchableOpacity
                        onPress={() => router.push({ pathname: '/action/plan' })}
                        className="bg-[#FFD700] py-4 px-6 rounded-xl w-full items-center active:bg-[#E5C100]"
                    >
                        <Text className="text-[#0B3130] font-bold text-lg">Yolculuğa Git →</Text>
                    </TouchableOpacity>
                </View>

                {/* DISCLAIMER */}
                <View className="bg-[#0B3130] p-4 rounded-lg border border-[#1A4642] mb-4">
                    <Text className="text-[#436F65] text-xs text-center leading-4">
                        📿 Bu manevi rutin Kuran-ı Kerim, hadisler ve İslami gelenekten oluşmaktadır.
                        Tıbbi tedavi gerektiren durumlar için mutlaka doktorunuza başvurun.
                    </Text>
                </View>

            </ScrollView>
        </SafeAreaView>
    );
}
