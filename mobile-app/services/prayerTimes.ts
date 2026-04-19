/**
 * Prayer Times service — wraps the backend /prayer-times API.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from './api';

export const DISTRICT_KEY = 'prayer_district_id';
export const DEFAULT_DISTRICT_ID = '9541'; // İstanbul - Fatih (Diyanet default)

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface HijriDate {
  day: number | null;
  month: number | null;
  month_name: string | null;
  year: number | null;
}

export interface PrayerTimesDay {
  date: string; // "2026-02-25"
  district_id: string;
  imsak: string; // "05:26"
  gunes: string;
  ogle: string;
  ikindi: string;
  aksam: string;
  yatsi: string;
  hijri: HijriDate;
}

export type PrayerName = 'imsak' | 'gunes' | 'ogle' | 'ikindi' | 'aksam' | 'yatsi';

export const PRAYER_LABELS: Record<PrayerName, string> = {
  imsak: 'İmsak',
  gunes: 'Güneş',
  ogle: 'Öğle',
  ikindi: 'İkindi',
  aksam: 'Akşam',
  yatsi: 'Yatsı',
};

export const PRAYER_ORDER: PrayerName[] = ['imsak', 'gunes', 'ogle', 'ikindi', 'aksam', 'yatsi'];

// ---------------------------------------------------------------------------
// District preference
// ---------------------------------------------------------------------------

export async function getDistrictId(): Promise<string> {
  const stored = await AsyncStorage.getItem(DISTRICT_KEY);
  return stored ?? DEFAULT_DISTRICT_ID;
}

export async function setDistrictId(districtId: string): Promise<void> {
  await AsyncStorage.setItem(DISTRICT_KEY, districtId);
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function fetchTodayPrayerTimes(districtId?: string): Promise<PrayerTimesDay> {
  const id = districtId ?? (await getDistrictId());
  return api.get<PrayerTimesDay>(`/prayer-times/today?district_id=${id}`);
}

export async function fetchWeekPrayerTimes(districtId?: string): Promise<PrayerTimesDay[]> {
  const id = districtId ?? (await getDistrictId());
  return api.get<PrayerTimesDay[]>(`/prayer-times/week?district_id=${id}`);
}

// ---------------------------------------------------------------------------
// Countdown helpers
// ---------------------------------------------------------------------------

/**
 * Returns the name and time string of the next upcoming prayer for today.
 */
export function getNextPrayer(
  times: PrayerTimesDay,
  now: Date = new Date(),
  nextDay?: PrayerTimesDay | null
): { name: PrayerName; label: string; time: string; dayOffset: number } | null {
  const [hNow, mNow] = [now.getHours(), now.getMinutes()];
  const nowMinutes = hNow * 60 + mNow;

  for (const name of PRAYER_ORDER) {
    const timeStr = times[name];
    const [h, m] = timeStr.split(':').map(Number);
    if (h * 60 + m > nowMinutes) {
      return { name, label: PRAYER_LABELS[name], time: timeStr, dayOffset: 0 };
    }
  }

  if (nextDay) {
    return {
      name: 'imsak',
      label: 'Yarın İmsak',
      time: nextDay.imsak,
      dayOffset: 1,
    };
  }

  return null; // all passed today and no next day data
}

/**
 * Returns a formatted countdown string "HH:SS" until the target time string "HH:MM".
 */
export function countdownUntil(timeStr: string, now: Date = new Date(), dayOffset = 0): string {
  const [targetH, targetM] = timeStr.split(':').map(Number);

  const targetDate = new Date(now);
  if (dayOffset !== 0) {
    targetDate.setDate(targetDate.getDate() + dayOffset);
  }
  targetDate.setHours(targetH, targetM, 0, 0);

  let diffMs = targetDate.getTime() - now.getTime();
  if (diffMs < 0) return '00:00';

  const totalSeconds = Math.floor(diffMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }
  return `${pad(minutes)}:${pad(seconds)}`;
}

function pad(n: number): string {
  return n.toString().padStart(2, '0');
}
