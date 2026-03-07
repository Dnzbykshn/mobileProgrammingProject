import React, { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { colors, gradients } from '@/theme';
import { Heading, Body, Caption } from '@/components/ui';
import {
    fetchTodayPrayerTimes,
    getNextPrayer,
    countdownUntil,
    PRAYER_ORDER,
    PRAYER_LABELS,
    PrayerTimesDay,
    PrayerName,
} from '@/services/prayerTimes';

const PRAYER_ICONS: Record<PrayerName, string> = {
    imsak:  'partly-sunny-outline',
    gunes:  'sunny-outline',
    ogle:   'sunny-sharp',
    ikindi: 'sunny',
    aksam:  'moon-outline',
    yatsi:  'moon-sharp',
};

const MONTHS_TR = [
    'Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
    'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık',
];

function formatDateTR(d: Date): string {
    return `${d.getDate()} ${MONTHS_TR[d.getMonth()]} ${d.getFullYear()}`;
}

export default function HomeScreen() {
    const router = useRouter();
    const [prayerTimes, setPrayerTimes] = useState<PrayerTimesDay | null>(null);
    const [loading, setLoading] = useState(true);
    const [countdown, setCountdown] = useState('--:--');
    const [nextPrayerLabel, setNextPrayerLabel] = useState('');
    const [currentPrayer, setCurrentPrayer] = useState<PrayerName | null>(null);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const loadPrayerTimes = useCallback(async () => {
        try {
            const data = await fetchTodayPrayerTimes();
            setPrayerTimes(data);
        } catch {
            // Silently fail — UI shows cached/empty state
        } finally {
            setLoading(false);
        }
    }, []);

    useFocusEffect(useCallback(() => {
        loadPrayerTimes();
    }, [loadPrayerTimes]));

    // Determine the last prayer whose time has passed
    const getCurrentPrayer = (times: PrayerTimesDay, now: Date): PrayerName | null => {
        const nowMins = now.getHours() * 60 + now.getMinutes();
        let current: PrayerName | null = null;
        for (const name of PRAYER_ORDER) {
            const [h, m] = times[name].split(':').map(Number);
            if (h * 60 + m <= nowMins) current = name;
            else break;
        }
        return current;
    };

    // Tick every second to update countdown
    useEffect(() => {
        if (!prayerTimes) return;

        const tick = () => {
            const now = new Date();
            const next = getNextPrayer(prayerTimes, now);
            setCurrentPrayer(getCurrentPrayer(prayerTimes, now));

            if (next) {
                setNextPrayerLabel(`${next.label} vaktine kalan`);
                setCountdown(countdownUntil(next.time, now));
            } else {
                setNextPrayerLabel('Tüm vakitler geçti');
                setCountdown('');
            }
        };

        tick();
        intervalRef.current = setInterval(tick, 1000);
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [prayerTimes]);

    const today = new Date();

    return (
        <LinearGradient
            colors={gradients.home}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            locations={[0, 0.4, 1]}
            style={{ flex: 1 }}
        >
            <SafeAreaView style={{ flex: 1 }} edges={['top', 'left', 'right']}>

                {/* --- HEADER --- */}
                <View className="px-6 py-4 relative">
                    <View className="flex-row justify-between items-center mb-4">
                        <Ionicons name="grid-outline" color={'white'} size={24} />
                        <View className='absolute inset-0 items-center justify-center pointer-events-none'>
                            <Text className="text-xl font-bold text-white tracking-wider">Quran App</Text>
                        </View>
                        <View className="flex-row items-center gap-4">
                            <Ionicons name="person-circle-outline" size={28} color="white" />
                            <Ionicons name="settings-outline" size={24} color="white" />
                        </View>
                    </View>

                    {/* Gregorian + Hijri date */}
                    <View className="mb-2 items-center">
                        <Caption
                            size="sm"
                            color="rgba(255,255,255,0.7)"
                            style={{ textTransform: 'uppercase', letterSpacing: 2, marginBottom: 4 }}
                        >
                            {formatDateTR(today)}
                        </Caption>
                        {prayerTimes?.hijri?.month_name && (
                            <Caption size="sm" color={colors.gold.muted} style={{ letterSpacing: 1 }}>
                                {`${prayerTimes.hijri.day} ${prayerTimes.hijri.month_name} ${prayerTimes.hijri.year}`}
                            </Caption>
                        )}
                    </View>

                    {/* Countdown clock */}
                    <View className="items-center mt-4 mb-6">
                        {loading ? (
                            <ActivityIndicator color="white" size="large" />
                        ) : (
                            <>
                                <Text className="text-white text-6xl font-bold tracking-tighter drop-shadow-lg">
                                    {countdown || '--:--'}
                                </Text>
                                <Text className="text-white/80 text-sm font-medium mt-1">
                                    {nextPrayerLabel}
                                </Text>
                            </>
                        )}
                    </View>

                    {/* Prayer times row */}
                    {prayerTimes && (
                        <View className="flex-row justify-between items-center mb-2">
                            {PRAYER_ORDER.map((name) => {
                                const isCurrent = name === currentPrayer;
                                return (
                                    <View
                                        key={name}
                                        className={`items-center gap-2 ${isCurrent ? 'opacity-100' : 'opacity-60'}`}
                                    >
                                        <Caption size="sm" color={colors.text.white} style={{ fontWeight: '500' }}>
                                            {PRAYER_LABELS[name]}
                                        </Caption>
                                        <Ionicons
                                            name={PRAYER_ICONS[name] as any}
                                            size={24}
                                            color={isCurrent ? colors.gold.muted : 'white'}
                                        />
                                        <Caption
                                            size="sm"
                                            color={isCurrent ? colors.gold.muted : colors.text.white}
                                            style={{ fontWeight: isCurrent ? '700' : '400' }}
                                        >
                                            {prayerTimes[name]}
                                        </Caption>
                                    </View>
                                );
                            })}
                        </View>
                    )}
                </View>

                {/* --- WHITE BOTTOM SHEET --- */}
                <View className="flex-1 bg-white rounded-t-[40px] px-6 pt-6 shadow-2xl relative">
                    <View className="w-12 h-1.5 bg-gray-200 rounded-full self-center mb-6" />

                    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>

                        {/* --- A. AI ASSISTANT CARD --- */}
                        <TouchableOpacity
                            onPress={() => router.push('/(tabs)/chat')}
                            style={{ backgroundColor: colors.teal.deep }}
                            className="w-full rounded-3xl p-6 mb-8 relative overflow-hidden shadow-lg shadow-teal-900/30"
                        >
                            <Ionicons name="sparkles" size={120} color="white" style={{ position: 'absolute', right: -20, top: -20, opacity: 0.05 }} />

                            <View className="flex-row items-center justify-end mb-4">
                                <View className="flex-row items-center gap-1">
                                    <View className="w-2 h-2 bg-green-400 rounded-full" />
                                    <Text className="text-white/60 text-[10px]">Çevrimiçi</Text>
                                </View>
                            </View>

                            <Text className="text-white text-2xl font-bold mb-2">Selamun Aleykum.</Text>
                            <Text className="text-white/80 text-sm mb-6 leading-5 pr-4">
                                Bugün ruhun nasıl hissediyor? Dertleşmek veya dua istemek için buradayım.
                            </Text>

                            <View className="bg-black/20 h-14 rounded-2xl flex-row items-center px-4 border border-white/10">
                                <Text className="text-white/50 text-sm flex-1">Buraya yazmaya başla...</Text>
                                <View style={{ backgroundColor: colors.gold.muted }} className="w-9 h-9 rounded-xl items-center justify-center shadow-md">
                                    <Ionicons name="arrow-forward" size={20} color={colors.teal.deep} />
                                </View>
                            </View>
                        </TouchableOpacity>

                        {/* --- B. ROUTINES --- */}
                        <View className="flex-row justify-between items-center mb-4">
                            <Heading size="md" color={colors.teal.deep}>Senin İçin Rutinler</Heading>
                            <TouchableOpacity><Caption size="md" color={colors.gold.muted} style={{ fontWeight: '700' }}>Tümü</Caption></TouchableOpacity>
                        </View>

                        <ScrollView horizontal showsHorizontalScrollIndicator={false} className="-mx-6 px-6 mb-8">
                            <TouchableOpacity className="mr-4 w-40 bg-white p-4 rounded-3xl shadow-sm shadow-teal-900/5" style={{ borderWidth: 1, borderColor: `${colors.teal.deep}1A` }}>
                                <View className="flex-row justify-between items-start mb-3">
                                    <View className="w-10 h-10 rounded-full items-center justify-center" style={{ backgroundColor: `${colors.teal.deep}0D` }}>
                                        <Ionicons name="sunny" size={20} color={colors.teal.deep} />
                                    </View>
                                    <View className="bg-gray-100 px-2 py-1 rounded-lg"><Caption size="sm" color="#6B7280" style={{ fontWeight: '700' }}>10 dk</Caption></View>
                                </View>
                                <Body size="md" color={colors.teal.deep} style={{ fontWeight: '700', marginBottom: 4 }}>Sabah Enerjisi</Body>
                                <Caption size="sm" color="#6B7280" style={{ marginBottom: 12 }}>7 Adım • Zikir & Dua</Caption>
                                <View className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden"><View style={{ width: '60%', height: '100%', backgroundColor: colors.gold.muted }} /></View>
                            </TouchableOpacity>

                            <TouchableOpacity className="mr-4 w-40 bg-white p-4 rounded-3xl shadow-sm shadow-teal-900/5" style={{ borderWidth: 1, borderColor: `${colors.teal.deep}1A` }}>
                                <View className="flex-row justify-between items-start mb-3">
                                    <View className="w-10 h-10 rounded-full items-center justify-center" style={{ backgroundColor: `${colors.teal.deep}0D` }}>
                                        <Ionicons name="moon" size={20} color={colors.teal.deep} />
                                    </View>
                                    <View className="bg-gray-100 px-2 py-1 rounded-lg"><Caption size="sm" color="#6B7280" style={{ fontWeight: '700' }}>5 dk</Caption></View>
                                </View>
                                <Body size="md" color={colors.teal.deep} style={{ fontWeight: '700', marginBottom: 4 }}>Huzurlu Uyku</Body>
                                <Caption size="sm" color="#6B7280" style={{ marginBottom: 12 }}>Mülk Suresi Dinle</Caption>
                                <View className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden"><View style={{ width: '30%', height: '100%', backgroundColor: colors.gold.muted }} /></View>
                            </TouchableOpacity>

                            <TouchableOpacity className="mr-4 w-40 bg-white p-4 rounded-3xl shadow-sm shadow-teal-900/5" style={{ borderWidth: 1, borderColor: `${colors.teal.deep}1A` }}>
                                <View className="flex-row justify-between items-start mb-3">
                                    <View className="w-10 h-10 rounded-full items-center justify-center" style={{ backgroundColor: `${colors.teal.deep}0D` }}>
                                        <Ionicons name="leaf" size={20} color={colors.teal.deep} />
                                    </View>
                                    <View className="bg-gray-100 px-2 py-1 rounded-lg"><Caption size="sm" color="#6B7280" style={{ fontWeight: '700' }}>3 dk</Caption></View>
                                </View>
                                <Body size="md" color={colors.teal.deep} style={{ fontWeight: '700', marginBottom: 4 }}>Şükür Günlüğü</Body>
                                <Caption size="sm" color="#6B7280" style={{ marginBottom: 12 }}>Günlük Not Al</Caption>
                                <View className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden"><View style={{ width: '0%', height: '100%', backgroundColor: colors.gold.muted }} /></View>
                            </TouchableOpacity>
                        </ScrollView>

                        {/* --- C. DAILY DOSE --- */}
                        <Heading size="md" color={colors.teal.deep} style={{ marginBottom: 16 }}>Günün Dozu</Heading>
                        <View className="flex-row items-center bg-gray-50 p-4 rounded-2xl border border-gray-100 mb-6">
                            <View className="w-12 h-12 bg-gray-200 rounded-xl items-center justify-center mr-4">
                                <Text className="text-2xl">💡</Text>
                            </View>
                            <View className="flex-1">
                                <Body size="md" color={colors.teal.deep} style={{ fontWeight: '700', marginBottom: 4 }}>Bir Hadis</Body>
                                <Caption size="md" color="#4B5563" style={{ fontStyle: 'italic' }}>"Kolaylaştırınız, zorlaştırmayınız; müjdeleyiniz, nefret ettirmeyiniz."</Caption>
                            </View>
                        </View>

                    </ScrollView>
                </View>

            </SafeAreaView>
        </LinearGradient>
    );
}
