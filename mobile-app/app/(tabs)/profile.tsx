import React from 'react';
import { ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronRight, LogOut, Mail, Settings2, ShieldCheck, UserRound } from 'lucide-react-native';

import AppButton from '@/components/app/AppButton';
import { ArabicPhrase, CrescentStar } from '@/components/app/IslamicOrnaments';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import SurfaceCard from '@/components/app/SurfaceCard';
import { useAuth } from '@/contexts/AuthContext';
import { colors, fonts, radius, spacing, typography } from '@/theme';

type QuickLinkRowProps = {
  icon: React.ComponentType<{ size?: number; color?: string }>;
  title: string;
  subtitle: string;
  onPress: () => void;
};

function QuickLinkRow({ icon: Icon, title, subtitle, onPress }: QuickLinkRowProps) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.88}>
      <View
        style={{
          borderRadius: radius.xl,
          padding: spacing.lg,
          borderWidth: 1,
          borderColor: colors.border.soft,
          backgroundColor: colors.surface.raised,
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
              backgroundColor: colors.surface.muted,
              marginRight: spacing.md,
            }}>
            <Icon size={18} color={colors.text.primary} />
          </View>

          <View style={{ flex: 1, paddingRight: spacing.md }}>
            <Text style={{ ...typography.labelLg, fontFamily: fonts.bodyMd, color: colors.text.primary }}>
              {title}
            </Text>
            <Text
              style={{
                ...typography.bodySm,
                fontFamily: fonts.body,
                color: colors.text.secondary,
                marginTop: spacing.xs + 1,
              }}>
              {subtitle}
            </Text>
          </View>

          <ChevronRight size={18} color={colors.text.muted} />
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function ProfileScreen() {
  const { user, isLoggedIn, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.replace('/');
  };

  if (!isLoggedIn) {
    return (
      <ScreenWrapper>
        <View style={{ flex: 1, justifyContent: 'center', paddingHorizontal: spacing.lg }}>
          <PageHeader title="Profil" subtitle="Devam etmek için giriş yap." eyebrow="Hesap" />

          <View
            style={{
              borderRadius: radius.xl,
              padding: spacing.xl,
              borderWidth: 1,
          borderColor: colors.border.soft,
            backgroundColor: colors.surface.raised,
          }}>
            <AppButton
              label="Giriş yap"
              onPress={() => router.push('/auth/login')}
              style={{ marginBottom: spacing.sm + 2 }}
            />
            <AppButton
              label="Kayıt ol"
              variant="secondary"
              onPress={() => router.push('/auth/register')}
            />
          </View>
        </View>
      </ScreenWrapper>
    );
  }

  const displayName = user?.full_name?.trim() || 'Kullanıcı';
  const initial = (user?.full_name || user?.email || '?').charAt(0).toUpperCase();

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 120,
        }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.md }}>
          <CrescentStar size={20} opacity={0.55} />
          <ArabicPhrase text="بِسْمِ اللَّهِ" size={13} opacity={0.45} centered={false} />
        </View>
        <PageHeader title="Profil" subtitle="Hesap özeti ve ayarlar." eyebrow="Hesap" />

        <SurfaceCard highlighted style={{ marginBottom: spacing.lg }}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <View
              style={{
                width: 64,
                height: 64,
                borderRadius: radius.full,
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: colors.surface.strong,
                borderWidth: 1,
                borderColor: colors.border.soft,
                marginRight: spacing.md,
              }}>
              <Text
                style={{
                  ...typography.h2,
                  fontFamily: fonts.heading,
                  color: colors.gold,
                }}>
                {initial}
              </Text>
            </View>

            <View style={{ flex: 1 }}>
              <Text
                style={{
                  ...typography.h4,
                  fontFamily: fonts.bodyMd,
                  color: colors.text.primary,
                  marginBottom: spacing.xs + 2,
                }}>
                {displayName}
              </Text>

              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Mail size={14} color={colors.text.secondary} />
                <Text
                  numberOfLines={1}
                  style={{
                    ...typography.bodySm,
                    fontFamily: fonts.body,
                    color: colors.text.secondary,
                    marginLeft: spacing.sm,
                    flex: 1,
                  }}>
                  {user?.email}
                </Text>
              </View>
            </View>
          </View>
        </SurfaceCard>

        <QuickLinkRow
          icon={Settings2}
          title="Ayarlar"
          subtitle="Konum, bildirim ve uygulama tercihleri."
          onPress={() => router.push('/settings')}
        />

        <QuickLinkRow
          icon={ShieldCheck}
          title="Oturum güvenliği"
          subtitle="Aktif cihazları gör ve tüm cihazlardan çıkış yap."
          onPress={() => router.push('/settings-sessions')}
        />

        <QuickLinkRow
          icon={UserRound}
          title="Anılar"
          subtitle="Kaydettiğin içerikleri ve gizlilik tercihlerini yönet."
          onPress={() => router.push('/(tabs)/memories')}
        />

        <View
          style={{
            borderRadius: radius.xl,
            padding: spacing.lg,
            borderWidth: 1,
            borderColor: colors.border.soft,
            backgroundColor: colors.surface.raised,
            marginTop: spacing.xs,
          }}>
          <Text
            style={{
              ...typography.bodySm,
              fontFamily: fonts.body,
              color: colors.text.secondary,
              marginBottom: spacing.md,
            }}>
            Bu cihazdaki oturumu kapatmak için aşağıdaki işlemi kullanabilirsin.
          </Text>

          <AppButton
            label="Bu cihazdan çıkış yap"
            icon={LogOut}
            variant="danger"
            onPress={handleLogout}
          />
        </View>
      </ScrollView>
    </ScreenWrapper>
  );
}
