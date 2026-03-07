import React, { useState, useCallback } from 'react';
import { View, Text, Switch, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { X, Bell, ChevronRight, LogOut, MapPin } from 'lucide-react-native';
import { useAuth } from '../contexts/AuthContext';
import { getDistrictId } from '@/services/prayerTimes';
import { fetchDistrict } from '@/services/locations';

export default function SettingsScreen() {
    const router = useRouter();
    const { user, logout } = useAuth();
    const displayName = user?.full_name || user?.email || 'Kullanıcı';
    const initial = displayName.charAt(0).toUpperCase();
    const [notifications, setNotifications] = useState(true);
    const [locationLabel, setLocationLabel] = useState('Yükleniyor...');

    const loadLocationLabel = useCallback(async () => {
        try {
            const id = await getDistrictId();
            const district = await fetchDistrict(id);
            const name = district.name.charAt(0) + district.name.slice(1).toLowerCase();
            setLocationLabel(name);
        } catch {
            setLocationLabel('Konum seçilmedi');
        }
    }, []);

    useFocusEffect(useCallback(() => {
        loadLocationLabel();
    }, [loadLocationLabel]));

    return (
        <View className="flex-1 bg-[#0B3130] pt-4">
            {/* Drag Handle (Visual cue for modal) */}
            <View className="self-center w-12 h-1 bg-[#436F65] rounded-full mb-2 opacity-50" />

            {/* Header */}
            <View className="flex-row justify-between items-center px-4 pb-4 border-b border-[#113835]">
                <Text className="text-[#E5E9E9] text-lg font-serif font-bold">Ayarlar</Text>
                <TouchableOpacity onPress={() => router.back()} className="p-2 bg-[#15423F] rounded-full">
                    <X color="#C0CAC9" size={20} />
                </TouchableOpacity>
            </View>

            <ScrollView className="flex-1" contentContainerStyle={{ padding: 24 }}>

                {/* PROFILE SECTION */}
                <View className="items-center mb-8">
                    <View className="w-24 h-24 bg-[#15423F] rounded-full border-2 border-[#FFD700] items-center justify-center mb-4">
                        <Text className="text-[#FFD700] text-4xl font-serif font-bold">{initial}</Text>
                    </View>
                    <Text className="text-[#E5E9E9] text-xl font-bold">{displayName}</Text>
                    {user?.is_premium && (
                        <Text className="text-[#FFD700] text-sm font-medium mt-1">Premium Üye ✨</Text>
                    )}
                </View>

                {/* NAMAZ VAKTİ */}
                <Text className="text-[#436F65] text-xs font-bold uppercase tracking-widest mb-4">Namaz Vakti</Text>

                <View className="bg-[#113835] rounded-xl border border-[#436F65] overflow-hidden mb-8">
                    <TouchableOpacity
                        onPress={() => router.push('/action/location-picker')}
                        className="p-4 flex-row justify-between items-center"
                    >
                        <View className="flex-row items-center flex-1">
                            <MapPin size={20} color="#FFD700" />
                            <View className="ml-3 flex-1">
                                <Text className="text-[#E5E9E9] text-base font-medium">Konum</Text>
                                <Text className="text-[#436F65] text-sm mt-0.5">{locationLabel}</Text>
                            </View>
                        </View>
                        <ChevronRight size={20} color="#436F65" />
                    </TouchableOpacity>
                </View>

                {/* PREFERENCES */}
                <Text className="text-[#436F65] text-xs font-bold uppercase tracking-widest mb-4">Tercihler</Text>

                <View className="bg-[#113835] rounded-xl border border-[#436F65] overflow-hidden mb-8">
                    <View className="p-4 flex-row justify-between items-center">
                        <View className="flex-row items-center">
                            <Bell size={20} color="#E5E9E9" />
                            <Text className="text-[#E5E9E9] text-base ml-3 font-medium">Bildirimler</Text>
                        </View>
                        <Switch
                            value={notifications}
                            onValueChange={setNotifications}
                            trackColor={{ false: "#436F65", true: "#FFD700" }}
                            thumbColor={notifications ? "#0B3130" : "#C0CAC9"}
                        />
                    </View>
                </View>

                {/* LOGOUT */}
                <TouchableOpacity
                    onPress={() => {
                        Alert.alert(
                            'Çıkış Yap',
                            'Hesabından çıkış yapmak istediğine emin misin?',
                            [
                                { text: 'İptal', style: 'cancel' },
                                {
                                    text: 'Çıkış Yap',
                                    style: 'destructive',
                                    onPress: async () => {
                                        await logout();
                                        router.replace('/');
                                    },
                                },
                            ]
                        );
                    }}
                    className="flex-row items-center justify-center p-4 rounded-xl border border-[#ef4444]"
                >
                    <LogOut size={20} color="#ef4444" />
                    <Text className="text-[#ef4444] font-bold ml-2">Çıkış Yap</Text>
                </TouchableOpacity>

            </ScrollView>
        </View>
    );
}
