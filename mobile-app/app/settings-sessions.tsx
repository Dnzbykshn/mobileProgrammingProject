import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { MonitorSmartphone, ShieldCheck } from 'lucide-react-native';

import AppButton from '@/components/app/AppButton';
import EmptyState from '@/components/app/EmptyState';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import SectionTitle from '@/components/app/SectionTitle';
import { useAuth } from '@/contexts/AuthContext';
import * as authService from '@/services/auth';
import { colors, fonts, radius, spacing, typography } from '@/theme';

function formatDate(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  return date.toLocaleString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getSessionLabel(session: authService.AuthSession, index: number) {
  if (session.is_current_device) {
    return 'Bu cihaz';
  }

  return `Diğer cihaz ${index + 1}`;
}

function getSessionDetail(deviceId: string) {
  if (deviceId.length <= 18) {
    return deviceId;
  }

  return `${deviceId.slice(0, 10)}...${deviceId.slice(-6)}`;
}

export default function SettingsSessionsScreen() {
  const { isLoggedIn, logoutAll } = useAuth();
  const router = useRouter();

  const [sessions, setSessions] = useState<authService.AuthSession[]>([]);
  const [isSessionsLoading, setIsSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [isLogoutAllLoading, setIsLogoutAllLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    if (!isLoggedIn) return;

    try {
      setIsSessionsLoading(true);
      setSessionsError(null);
      const nextSessions = await authService.getSessions();
      const sortedSessions = [...nextSessions].sort((a, b) => {
        if (a.is_current_device && !b.is_current_device) return -1;
        if (!a.is_current_device && b.is_current_device) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setSessions(sortedSessions);
    } catch (error) {
      const message =
        error && typeof error === 'object' && 'message' in error
          ? String(error.message)
          : 'Oturumlar yüklenemedi.';
      setSessionsError(message);
      setSessions([]);
    } finally {
      setIsSessionsLoading(false);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (isLoggedIn) {
      void loadSessions();
    }
  }, [isLoggedIn, loadSessions]);

  const handleLogoutAll = () => {
    Alert.alert(
      'Tüm cihazlardan çıkış',
      'Tüm aktif oturumlar kapatılacak. Devam etmek istiyor musun?',
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Devam et',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLogoutAllLoading(true);
              const result = await logoutAll();
              Alert.alert('Tamamlandı', `${result.revoked_sessions} oturum kapatıldı.`);
              router.replace('/');
            } catch (error) {
              const message =
                error && typeof error === 'object' && 'message' in error
                  ? String(error.message)
                  : 'İşlem tamamlanamadı.';
              Alert.alert('Hata', message);
            } finally {
              setIsLogoutAllLoading(false);
            }
          },
        },
      ]
    );
  };

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: spacing.xxxl,
        }}>
        <PageHeader
          title="Oturum Güvenliği"
          subtitle="Bu hesaba açık cihazlar."
          eyebrow="Güvenlik"
          back
        />

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            padding: spacing.lg,
            marginBottom: spacing.lg,
          }}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <View
              style={{
                width: 42,
                height: 42,
                borderRadius: radius.full,
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: colors.surface.goldSoft,
                marginRight: spacing.md,
              }}>
              <ShieldCheck size={18} color={colors.ink} />
            </View>

            <View style={{ flex: 1 }}>
              <Text style={{ ...typography.labelLg, fontFamily: fonts.bodyMd, color: colors.ink }}>
                Oturumları gözden geçir
              </Text>
              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.inkMuted,
                  marginTop: spacing.xs + 1,
                }}>
                Tanımadığın bir cihaz görürsen tüm cihazlardan çıkış yap.
              </Text>
            </View>
          </View>
        </View>

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            padding: spacing.lg,
          }}>
          <SectionTitle
            title="Aktif cihazlar"
            actionLabel="Yenile"
            onActionPress={() => void loadSessions()}
          />

          {isSessionsLoading ? <ActivityIndicator color={colors.gold} /> : null}

          {sessionsError ? (
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
                color: colors.text.danger,
                marginBottom: spacing.md,
              }}>
              {sessionsError}
            </Text>
          ) : null}

          {!isSessionsLoading && sessions.length === 0 ? (
            <EmptyState message="Aktif oturum bulunamadı." compact={false} />
          ) : (
            <View style={{ gap: spacing.sm + 2 }}>
              {sessions.map((session, index) => (
                <View
                  key={`${session.device_id}-${session.created_at}-${index}`}
                  style={{
                    borderRadius: radius.lg,
                    padding: spacing.md,
                    backgroundColor: session.is_current_device
                      ? colors.surface.goldSoft
                      : colors.surface.paper,
                    borderWidth: 1,
                    borderColor: session.is_current_device
                      ? colors.border.gold
                      : colors.border.paper,
                  }}>
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: spacing.sm,
                    }}>
                    <View
                      style={{
                        flexDirection: 'row',
                        alignItems: 'center',
                        flex: 1,
                        paddingRight: spacing.md,
                      }}>
                      <View
                        style={{
                          width: 34,
                          height: 34,
                          borderRadius: radius.full,
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: colors.surface.paperSoft,
                          marginRight: spacing.sm + 2,
                        }}>
                        <MonitorSmartphone size={16} color={colors.ink} />
                      </View>

                      <View style={{ flex: 1 }}>
                        <Text
                          style={{
                            ...typography.labelLg,
                            fontFamily: fonts.bodyMd,
                            color: colors.ink,
                          }}>
                          {getSessionLabel(session, index)}
                        </Text>
                        <Text
                          style={{
                            ...typography.bodySm,
                            fontFamily: fonts.body,
                            color: colors.text.inkMuted,
                            marginTop: spacing.xs,
                          }}>
                          Kimlik: {getSessionDetail(session.device_id)}
                        </Text>
                      </View>
                    </View>

                    {session.is_current_device ? (
                      <View
                        style={{
                          paddingHorizontal: spacing.sm + 2,
                          paddingVertical: spacing.xs,
                          borderRadius: radius.full,
                          backgroundColor: colors.surface.goldMuted,
                        }}>
                        <Text
                          style={{
                            ...typography.labelSm,
                            fontFamily: fonts.bodySm,
                            color: colors.ink,
                          }}>
                          AKTİF
                        </Text>
                      </View>
                    ) : null}
                  </View>

                  <Text
                    style={{
                      ...typography.bodySm,
                      fontFamily: fonts.body,
                      color: colors.text.inkMuted,
                    }}>
                    Açılış: {formatDate(session.created_at)}
                  </Text>
                  <Text
                    style={{
                      ...typography.bodySm,
                      fontFamily: fonts.body,
                      color: colors.text.inkMuted,
                      marginTop: spacing.xs,
                    }}>
                    Bitiş: {formatDate(session.expires_at)}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            padding: spacing.lg,
            marginTop: spacing.lg,
          }}>
          <Text
            style={{
              ...typography.bodySm,
              fontFamily: fonts.body,
              color: colors.text.inkMuted,
              marginBottom: spacing.md,
            }}>
            Tanımadığın bir erişim görüyorsan tüm cihazlardaki oturumları kapat.
          </Text>

          <AppButton
            label="Tüm cihazlardan çıkış yap"
            onPress={handleLogoutAll}
            loading={isLogoutAllLoading}
            variant="danger"
          />
        </View>
      </ScrollView>
    </ScreenWrapper>
  );
}
