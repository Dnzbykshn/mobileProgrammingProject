import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from 'react-native';
import React, { useCallback, useEffect, useState } from 'react';
import ScreenWrapper from '@/components/ScreenWrapper';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'expo-router';
import { User, Settings, LogOut, Crown, Mail, ChevronRight, BookMarked } from 'lucide-react-native';
import * as authService from '@/services/auth';

export default function Profile() {
    const { user, isLoggedIn, logout, logoutAll } = useAuth();
    const router = useRouter();
    const [sessions, setSessions] = useState<authService.AuthSession[]>([]);
    const [isSessionsLoading, setIsSessionsLoading] = useState(false);
    const [sessionsError, setSessionsError] = useState<string | null>(null);
    const [isLogoutAllLoading, setIsLogoutAllLoading] = useState(false);

    const handleLogout = async () => {
        await logout();
        router.replace('/');
    };

    const formatDate = (iso: string): string => {
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
    };

    const loadSessions = useCallback(async () => {
        if (!isLoggedIn) return;
        try {
            setIsSessionsLoading(true);
            setSessionsError(null);
            const data = await authService.getSessions();
            setSessions(data);
        } catch (error: any) {
            setSessionsError(error?.message || 'Oturumlar yüklenemedi.');
        } finally {
            setIsSessionsLoading(false);
        }
    }, [isLoggedIn]);

    const handleLogoutAll = () => {
        Alert.alert(
            'Tüm Cihazlardan Çıkış',
            'Tüm aktif oturumların kapatılacak. Bu cihaz da dahil tekrar giriş yapman gerekecek. Devam etmek istiyor musun?',
            [
                { text: 'İptal', style: 'cancel' },
                {
                    text: 'Devam Et',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            setIsLogoutAllLoading(true);
                            const result = await logoutAll();
                            Alert.alert('Tamamlandı', `${result.revoked_sessions} oturum kapatıldı.`);
                            router.replace('/');
                        } catch (error: any) {
                            Alert.alert('Hata', error?.message || 'Tüm oturumlar kapatılamadı.');
                        } finally {
                            setIsLogoutAllLoading(false);
                        }
                    },
                },
            ]
        );
    };

    useEffect(() => {
        if (isLoggedIn) {
            void loadSessions();
            return;
        }
        setSessions([]);
        setSessionsError(null);
    }, [isLoggedIn, loadSessions]);

    if (!isLoggedIn) {
        return (
            <ScreenWrapper>
                <View className="flex-1 items-center justify-center px-8">
                    <View className="w-20 h-20 bg-[#15423F] rounded-full items-center justify-center mb-6">
                        <User size={40} color="#FFD700" />
                    </View>
                    <Text className="text-white text-2xl font-bold mb-2">Hoş Geldin</Text>
                    <Text className="text-[#C0CAC9] text-center mb-8">
                        Manevi yolculuğuna başlamak için giriş yap veya kayıt ol.
                    </Text>
                    <TouchableOpacity
                        onPress={() => router.push('/auth/login' as any)}
                        className="bg-[#FFD700] w-full py-4 rounded-xl items-center mb-3"
                    >
                        <Text className="text-[#0B3130] font-bold text-lg">Giriş Yap</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        onPress={() => router.push('/auth/register' as any)}
                        className="border border-[#FFD700] w-full py-4 rounded-xl items-center"
                    >
                        <Text className="text-[#FFD700] font-bold text-lg">Kayıt Ol</Text>
                    </TouchableOpacity>
                </View>
            </ScreenWrapper>
        );
    }

    return (
        <ScreenWrapper>
            <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
                {/* Profile Header */}
                <View className="items-center pt-10 pb-6 border-b border-[#15423F]/40">
                    <View className="w-24 h-24 bg-[#15423F] rounded-full items-center justify-center mb-4 border-2 border-[#FFD700]">
                        <Text className="text-[#FFD700] text-3xl font-bold">
                            {(user?.full_name || user?.email || '?')[0].toUpperCase()}
                        </Text>
                    </View>
                    <Text className="text-white text-xl font-bold">{user?.full_name || 'Kullanıcı'}</Text>
                    <View className="flex-row items-center mt-2">
                        <Mail size={14} color="#C0CAC9" />
                        <Text className="text-[#C0CAC9] text-sm ml-2">{user?.email}</Text>
                    </View>
                    {user?.is_premium && (
                        <View className="flex-row items-center mt-3 bg-[#FFD700]/20 px-4 py-2 rounded-full">
                            <Crown size={14} color="#FFD700" />
                            <Text className="text-[#FFD700] font-bold text-xs ml-2">Premium Üye</Text>
                        </View>
                    )}
                </View>

                {/* Menu Items */}
                <View className="px-6 pt-6">
                    <TouchableOpacity
                        onPress={() => router.push('/settings')}
                        className="flex-row items-center justify-between bg-[#15423F]/40 p-4 rounded-xl mb-3"
                    >
                        <View className="flex-row items-center">
                            <Settings size={20} color="#C0CAC9" />
                            <Text className="text-white font-medium ml-4">Ayarlar</Text>
                        </View>
                        <ChevronRight size={18} color="#C0CAC9" />
                    </TouchableOpacity>

                    <TouchableOpacity
                        onPress={() => router.push('/(tabs)/memories')}
                        className="flex-row items-center justify-between bg-[#15423F]/40 p-4 rounded-xl mb-3"
                    >
                        <View className="flex-row items-center">
                            <BookMarked size={20} color="#C0CAC9" />
                            <Text className="text-white font-medium ml-4">Anılarım</Text>
                        </View>
                        <ChevronRight size={18} color="#C0CAC9" />
                    </TouchableOpacity>

                    <View className="bg-[#15423F]/25 p-4 rounded-xl border border-[#15423F]/60 mt-1">
                        <View className="flex-row items-center justify-between mb-3">
                            <Text className="text-white font-semibold">Aktif Oturumlar</Text>
                            <TouchableOpacity onPress={() => void loadSessions()}>
                                <Text className="text-[#FFD700] text-xs font-semibold">Yenile</Text>
                            </TouchableOpacity>
                        </View>

                        {isSessionsLoading ? (
                            <View className="py-2">
                                <ActivityIndicator color="#FFD700" />
                            </View>
                        ) : null}

                        {sessionsError ? (
                            <Text className="text-[#FF6B6B] text-xs mb-2">{sessionsError}</Text>
                        ) : null}

                        {!isSessionsLoading && !sessionsError && sessions.length === 0 ? (
                            <Text className="text-[#C0CAC9] text-xs">Aktif oturum bulunamadı.</Text>
                        ) : null}

                        {!isSessionsLoading && sessions.length > 0
                            ? sessions.map((session, index) => (
                                  <View
                                      key={`${session.device_id}-${session.created_at}-${index}`}
                                      className="bg-[#0F3438] rounded-lg p-3 mb-2"
                                  >
                                      <View className="flex-row items-center justify-between">
                                          <Text className="text-white text-xs font-semibold" numberOfLines={1}>
                                              {session.device_id}
                                          </Text>
                                          {session.is_current_device ? (
                                              <Text className="text-[#FFD700] text-[10px] font-bold">BU CİHAZ</Text>
                                          ) : null}
                                      </View>
                                      <Text className="text-[#C0CAC9] text-[11px] mt-1">
                                          Açılış: {formatDate(session.created_at)}
                                      </Text>
                                      <Text className="text-[#C0CAC9] text-[11px]">
                                          Bitiş: {formatDate(session.expires_at)}
                                      </Text>
                                  </View>
                              ))
                            : null}

                        <TouchableOpacity
                            onPress={handleLogoutAll}
                            disabled={isLogoutAllLoading}
                            className="mt-2 bg-[#3D1515]/50 border border-red-900/30 rounded-lg p-3 items-center"
                        >
                            {isLogoutAllLoading ? (
                                <ActivityIndicator color="#FF6B6B" />
                            ) : (
                                <Text className="text-[#FF6B6B] text-sm font-semibold">Tüm Cihazlardan Çıkış Yap</Text>
                            )}
                        </TouchableOpacity>
                    </View>

                    <TouchableOpacity
                        onPress={handleLogout}
                        className="flex-row items-center bg-[#3D1515]/40 p-4 rounded-xl mt-6 border border-red-900/30"
                    >
                        <LogOut size={20} color="#FF6B6B" />
                        <Text className="text-[#FF6B6B] font-medium ml-4">Çıkış Yap</Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </ScreenWrapper>
    );
}
