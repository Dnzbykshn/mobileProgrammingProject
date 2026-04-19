import React, { useCallback, useEffect, useState } from 'react';
import { Alert, ScrollView, Switch, Text, TouchableOpacity, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Bell, ChevronRight, MapPin, ShieldCheck } from 'lucide-react-native';

import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import { useAuth } from '@/contexts/AuthContext';
import { fetchDistrict } from '@/services/locations';
import { getDistrictId } from '@/services/prayerTimes';
import { colors, fonts, radius, spacing, typography } from '@/theme';

const NOTIFICATIONS_ENABLED_KEY = 'settings_notifications_enabled';

function SettingsRow({
  icon,
  title,
  subtitle,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <View
      style={{
        borderRadius: radius.xl,
        padding: spacing.lg,
        borderWidth: 1,
        borderColor: colors.border.paper,
        backgroundColor: colors.surface.paperRaised,
        marginBottom: spacing.md,
      }}>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <View
          style={{
            width: 40,
            height: 40,
            borderRadius: radius.full,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: colors.surface.goldSoft,
            marginRight: spacing.md,
          }}>
          {icon}
        </View>

        <View style={{ flex: 1, paddingRight: spacing.md }}>
          <Text style={{ ...typography.labelLg, fontFamily: fonts.bodyMd, color: colors.ink }}>
            {title}
          </Text>
          <Text
            style={{
              ...typography.bodySm,
              fontFamily: fonts.body,
              color: colors.text.inkMuted,
              marginTop: spacing.xs + 1,
            }}>
            {subtitle}
          </Text>
        </View>

        {action}
      </View>
    </View>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [notifications, setNotifications] = useState(true);
  const [locationLabel, setLocationLabel] = useState('Konum yükleniyor');

  useEffect(() => {
    const loadNotificationPreference = async () => {
      try {
        const stored = await AsyncStorage.getItem(NOTIFICATIONS_ENABLED_KEY);
        if (stored !== null) {
          setNotifications(stored === 'true');
        }
      } catch {
        setNotifications(true);
      }
    };

    void loadNotificationPreference();
  }, []);

  const loadLocationLabel = useCallback(async () => {
    try {
      const id = await getDistrictId();
      const district = await fetchDistrict(id);
      setLocationLabel(district.name);
    } catch {
      setLocationLabel('Konum seçilmedi');
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadLocationLabel();
    }, [loadLocationLabel])
  );

  const handleNotificationsChange = useCallback(async (value: boolean) => {
    setNotifications(value);
    try {
      await AsyncStorage.setItem(NOTIFICATIONS_ENABLED_KEY, String(value));
    } catch {
      Alert.alert('Kaydedilemedi', 'Bildirim tercihi kaydedilemedi.');
    }
  }, []);

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: spacing.xxxl,
        }}>
        <PageHeader title="Ayarlar" subtitle="Uygulama tercihleri." eyebrow="Uygulama" back />

        <TouchableOpacity
          activeOpacity={0.88}
          onPress={() => router.push('/action/location-picker')}>
          <SettingsRow
            icon={<MapPin size={18} color={colors.ink} />}
            title="Konum"
            subtitle={locationLabel}
            action={<ChevronRight size={18} color={colors.text.inkMuted} />}
          />
        </TouchableOpacity>

        <SettingsRow
          icon={<Bell size={18} color={colors.ink} />}
          title="Bildirimler"
          subtitle="Uygulama içi tercih"
          action={
            <Switch
              value={notifications}
              onValueChange={(value) => {
                void handleNotificationsChange(value);
              }}
              trackColor={{ false: colors.surface.paperStrong, true: colors.gold }}
              thumbColor={notifications ? colors.ink : colors.surface.paperRaised}
            />
          }
        />

        <TouchableOpacity activeOpacity={0.88} onPress={() => router.push('/settings-sessions')}>
          <SettingsRow
            icon={<ShieldCheck size={18} color={colors.ink} />}
            title="Oturum güvenliği"
            subtitle="Aktif cihazları görüntüle ve tüm cihazlardan çıkış yap."
            action={<ChevronRight size={18} color={colors.text.inkMuted} />}
          />
        </TouchableOpacity>

        <View
          style={{
            borderRadius: radius.xl,
            padding: spacing.lg,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            marginTop: spacing.xs,
          }}>
          <Text
            style={{
              ...typography.bodySm,
              fontFamily: fonts.body,
              color: colors.text.inkMuted,
            }}>
            {user?.email || 'Hesap e-postası bulunamadı.'}
          </Text>
        </View>
      </ScrollView>
    </ScreenWrapper>
  );
}
