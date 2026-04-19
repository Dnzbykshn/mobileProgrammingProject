import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import {
  Bell,
  BookOpen,
  LucideIcon,
  MapPin,
  MessageCircleMore,
  Moon,
  MoonStar,
  Sun,
  SunMedium,
  Sunrise,
  Sunset,
} from 'lucide-react-native';

import PathwayCard from '@/components/app/PathwayCard';
import ScreenWrapper from '@/components/ScreenWrapper';
import SectionTitle from '@/components/app/SectionTitle';
import {
  ArabicPhrase,
  CrescentStar,
  IslamicDivider,
  MosqueSilhouette,
} from '@/components/app/IslamicOrnaments';
import { useAuth } from '@/contexts/AuthContext';
import {
  countdownUntil,
  fetchTodayPrayerTimes,
  fetchWeekPrayerTimes,
  getDistrictId,
  getNextPrayer,
  PrayerName,
  PrayerTimesDay,
  PRAYER_LABELS,
  PRAYER_ORDER,
} from '@/services/prayerTimes';
import { fetchDistrict } from '@/services/locations';
import { getActivePathways, PathwaySummary } from '@/services/pathways';
import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

const MONTHS_TR = [
  'Ocak',
  'Şubat',
  'Mart',
  'Nisan',
  'Mayıs',
  'Haziran',
  'Temmuz',
  'Ağustos',
  'Eylül',
  'Ekim',
  'Kasım',
  'Aralık',
];
const DAYS_TR = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];

const PRAYER_ICONS: Record<PrayerName, LucideIcon> = {
  imsak: Sunrise,
  gunes: SunMedium,
  ogle: Sun,
  ikindi: SunMedium,
  aksam: Sunset,
  yatsi: MoonStar,
};

function formatHeaderDate(date: Date): string {
  return `${date.getDate()} ${MONTHS_TR[date.getMonth()].toUpperCase()} ${DAYS_TR[date.getDay()].toUpperCase()}`;
}

function getFirstName(fullName: string | null | undefined): string {
  if (!fullName) return '';
  return fullName.split(' ')[0];
}

function getCurrentPrayer(times: PrayerTimesDay, now: Date): PrayerName | null {
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  let current: PrayerName | null = null;

  for (const name of PRAYER_ORDER) {
    const [hour, minute] = times[name].split(':').map(Number);
    if (hour * 60 + minute <= nowMinutes) {
      current = name;
    } else {
      break;
    }
  }

  return current;
}

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();

  const [prayerTimes, setPrayerTimes] = useState<PrayerTimesDay | null>(null);
  const [tomorrowPrayerTimes, setTomorrowPrayerTimes] = useState<PrayerTimesDay | null>(null);
  const [districtName, setDistrictName] = useState('');
  const [activePathways, setActivePathways] = useState<PathwaySummary[]>([]);
  const [loadingPrayerTimes, setLoadingPrayerTimes] = useState(true);
  const [loadingPathways, setLoadingPathways] = useState(true);
  const [countdown, setCountdown] = useState('--:--:--');
  const [nextPrayerLabel, setNextPrayerLabel] = useState('');
  const [currentPrayer, setCurrentPrayer] = useState<PrayerName | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const today = new Date();

  const loadPrayerData = useCallback(async () => {
    try {
      setLoadingPrayerTimes(true);
      const districtId = await getDistrictId();
      const [times, weekTimes] = await Promise.all([
        fetchTodayPrayerTimes(districtId),
        fetchWeekPrayerTimes(districtId),
      ]);

      setPrayerTimes(times);
      setTomorrowPrayerTimes(weekTimes[1] ?? null);

      try {
        const district = await fetchDistrict(districtId);
        setDistrictName(district.name);
      } catch {
        setDistrictName('');
      }
    } catch {
      setPrayerTimes(null);
    } finally {
      setLoadingPrayerTimes(false);
    }
  }, []);

  const loadPathways = useCallback(async () => {
    try {
      setLoadingPathways(true);
      const data = await getActivePathways();
      setActivePathways(data);
    } catch {
      setActivePathways([]);
    } finally {
      setLoadingPathways(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadPrayerData();
      void loadPathways();
    }, [loadPrayerData, loadPathways])
  );

  useEffect(() => {
    if (!prayerTimes) {
      setCountdown('--:--:--');
      setNextPrayerLabel('');
      setCurrentPrayer(null);
      return;
    }

    const tick = () => {
      const now = new Date();
      const nextPrayer = getNextPrayer(prayerTimes, now, tomorrowPrayerTimes);
      setCurrentPrayer(getCurrentPrayer(prayerTimes, now));

      if (nextPrayer) {
        setNextPrayerLabel(nextPrayer.label);
        setCountdown(countdownUntil(nextPrayer.time, now, nextPrayer.dayOffset));
      } else {
        setNextPrayerLabel('');
        setCountdown('00:00:00');
      }
    };

    tick();
    intervalRef.current = setInterval(tick, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [prayerTimes, tomorrowPrayerTimes]);

  const firstName = getFirstName(user?.full_name);

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 120,
        }}>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: spacing.xl,
          }}>
          <View>
            <ArabicPhrase text="اَلسَّلَامُ عَلَيْكُمْ" size={13} opacity={0.45} centered={false} />
            <Text
              style={{
                ...typography.labelSm,
                fontFamily: fonts.bodySm,
                color: colors.gold,
                letterSpacing: 1.1,
                textTransform: 'uppercase',
                marginBottom: spacing.xs,
                marginTop: spacing.xs,
              }}>
              {formatHeaderDate(today)}
            </Text>

            <Text style={{ ...typography.h1, fontFamily: fonts.heading, color: colors.text.primary }}>
              {firstName ? `Selâm, ${firstName}` : 'Selâm'}
            </Text>
          </View>

          <TouchableOpacity
            onPress={() => router.push('/settings')}
            style={{
              width: 40,
              height: 40,
              borderRadius: radius.full,
              backgroundColor: colors.surface.raised,
              borderWidth: 1,
              borderColor: colors.border.soft,
              alignItems: 'center',
              justifyContent: 'center',
              marginTop: spacing.xs,
            }}>
            <Bell size={18} color={colors.text.primary} />
          </TouchableOpacity>
        </View>

        <View
          style={{
            borderRadius: radius.xl,
            marginBottom: spacing.lg,
            backgroundColor: colors.surface.raised,
            borderWidth: 1,
            borderColor: colors.border.soft,
            padding: spacing.xl,
            overflow: 'hidden',
            ...shadows.sm,
          }}>
          {/* Cami silüeti arka plan süsü */}
          <View
            pointerEvents="none"
            style={{ position: 'absolute', bottom: 0, right: 0, left: 0, alignItems: 'center' }}>
            <MosqueSilhouette width={220} height={70} opacity={0.06} />
          </View>

          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: spacing.xl,
            }}>
            {districtName ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.xs + 2 }}>
                <MapPin size={13} color={colors.gold} />
                <Text
                  style={{
                    ...typography.labelMd,
                    fontFamily: fonts.bodyMd,
                    color: colors.gold,
                    textTransform: 'uppercase',
                    letterSpacing: 0.6,
                  }}>
                  {districtName.toUpperCase()}
                </Text>
              </View>
            ) : (
              <View />
            )}

            {prayerTimes?.hijri?.month_name ? (
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                }}>
                {`${prayerTimes.hijri.day} ${prayerTimes.hijri.month_name} ${prayerTimes.hijri.year}`}
              </Text>
            ) : null}
          </View>

          {loadingPrayerTimes ? (
            <View style={{ paddingVertical: spacing.xxxl, alignItems: 'center' }}>
              <ActivityIndicator color={colors.gold} />
            </View>
          ) : prayerTimes ? (
            <>
              <View style={{ alignItems: 'center', marginBottom: spacing.xl }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm }}>
                  <CrescentStar size={18} opacity={0.6} />
                  <ArabicPhrase text="مَوَاقِيتُ الصَّلَاةِ" size={14} opacity={0.5} centered={false} />
                  <CrescentStar size={18} opacity={0.6} />
                </View>
                {nextPrayerLabel ? (
                  <Text
                    style={{
                      ...typography.labelSm,
                      fontFamily: fonts.bodySm,
                      color: colors.gold,
                      letterSpacing: 1.2,
                      textTransform: 'uppercase',
                      marginBottom: spacing.sm,
                    }}>
                    {`${nextPrayerLabel} vaktine kalan`}
                  </Text>
                ) : null}

                <Text
                  style={{
                    ...typography.display,
                  fontFamily: fonts.heading,
                  color: colors.text.primary,
                  lineHeight: 56,
                  }}>
                  {countdown}
                </Text>

                {currentPrayer ? (
                  <View
                    style={{
                      marginTop: spacing.xs + 2,
                      paddingHorizontal: spacing.sm + 2,
                      paddingVertical: spacing.xs,
                      borderRadius: radius.full,
                      backgroundColor: colors.night,
                    }}>
                    <Text
                      style={{
                        ...typography.labelMd,
                        fontFamily: fonts.bodyMd,
                        color: colors.text.primary,
                      }}>
                      {`Şu an ${PRAYER_LABELS[currentPrayer]}`}
                    </Text>
                  </View>
                ) : null}
              </View>

              <View
                style={{ flexDirection: 'row', justifyContent: 'space-between', gap: spacing.xs }}>
                {PRAYER_ORDER.map((name) => {
                  const active = currentPrayer === name;
                  const Icon = PRAYER_ICONS[name] || Moon;

                  return (
                    <View
                      key={name}
                      style={{
                        alignItems: 'center',
                        flex: 1,
                        backgroundColor: active ? colors.surface.muted : colors.surface.nightSoft,
                        borderWidth: 1,
                        borderColor: active ? colors.border.gold : colors.border.soft,
                        borderRadius: radius.md,
                        paddingVertical: spacing.sm,
                      }}>
                      <Text
                        style={{
                          ...typography.labelSm,
                          fontFamily: fonts.bodyMd,
                          color: active ? colors.gold : colors.text.muted,
                          marginBottom: spacing.sm,
                        }}>
                        {PRAYER_LABELS[name]}
                      </Text>

                      <View
                        style={{
                          width: 32,
                          height: 32,
                          borderRadius: radius.full,
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginBottom: spacing.sm,
                          backgroundColor: active
                            ? colors.surface.nightSoft
                            : colors.surface.nightRaised,
                        }}>
                        <Icon size={16} color={active ? colors.gold : colors.text.muted} />
                      </View>

                      <Text
                        style={{
                          ...typography.bodySm,
                          fontFamily: active ? fonts.bodyMd : fonts.body,
                          color: colors.text.primary,
                        }}>
                        {prayerTimes[name]}
                      </Text>
                    </View>
                  );
                })}
              </View>
            </>
          ) : (
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
              color: colors.text.secondary,
              textAlign: 'center',
              paddingVertical: spacing.lg,
              }}>
              Namaz vakitleri yüklenemedi.
            </Text>
          )}
        </View>

        <IslamicDivider opacity={0.22} />
        <SectionTitle title="Hızlı geçiş" />
        <View style={{ flexDirection: 'row', gap: spacing.md, marginBottom: spacing.lg }}>
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/chat')}
            activeOpacity={0.88}
            style={{ flex: 1 }}>
            <View
              style={{
                backgroundColor: colors.surface.raised,
                borderRadius: radius.lg,
                borderWidth: 1,
                borderColor: colors.border.soft,
                padding: spacing.lg,
                ...shadows.sm,
              }}>
              <View
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: radius.full,
                  backgroundColor: colors.surface.muted,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: spacing.md,
                }}>
                <MessageCircleMore size={16} color={colors.gold} />
              </View>

              <Text
                style={{
                  ...typography.labelLg,
                  fontFamily: fonts.bodyMd,
                  color: colors.text.primary,
                  marginBottom: spacing.xs + 1,
                }}>
                Sohbet
              </Text>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                }}>
                Yeni konuşma başlat
              </Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => router.push('/(tabs)/quran')}
            activeOpacity={0.88}
            style={{ flex: 1 }}>
            <View
              style={{
                backgroundColor: colors.surface.raised,
                borderRadius: radius.lg,
                borderWidth: 1,
                borderColor: colors.border.soft,
                padding: spacing.lg,
                ...shadows.sm,
              }}>
              <View
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: radius.full,
                  backgroundColor: colors.surface.muted,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: spacing.md,
                }}>
                <BookOpen size={16} color={colors.gold} />
              </View>

              <Text
                style={{
                  ...typography.labelLg,
                  fontFamily: fonts.bodyMd,
                  color: colors.text.primary,
                  marginBottom: spacing.xs + 1,
                }}>
                Ayet arama
              </Text>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                }}>
                Veritabanında ara
              </Text>
            </View>
          </TouchableOpacity>
        </View>

        <IslamicDivider opacity={0.22} />
        <SectionTitle title="Aktif yollar" />
        {loadingPathways ? (
          <View style={{ paddingVertical: spacing.xl, alignItems: 'center' }}>
            <ActivityIndicator color={colors.gold} />
          </View>
        ) : activePathways.length === 0 ? (
          <View
            style={{
              borderRadius: radius.xl,
              borderWidth: 1,
            borderColor: colors.border.soft,
            backgroundColor: colors.surface.raised,
            padding: spacing.lg,
          }}>
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
                color: colors.text.secondary,
              }}>
              Aktif yol bulunmuyor. Sohbette yeni bir yol başlatabilirsin.
            </Text>
          </View>
        ) : (
          <View style={{ gap: spacing.md }}>
            {activePathways.slice(0, 3).map((pathway) => (
              <PathwayCard
                key={pathway.pathway_id}
                pathway={pathway}
                compact
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
      </ScrollView>
    </ScreenWrapper>
  );
}
