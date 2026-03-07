import React, { useEffect, useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    ActivityIndicator,
    Alert,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { useRouter } from 'expo-router';

import ScreenWrapper from '@/components/ScreenWrapper';
import { useAuth } from '@/contexts/AuthContext';

export default function RegisterScreen() {
    const router = useRouter();
    const { register, isLoggedIn } = useAuth();

    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (isLoggedIn) {
            router.replace('/(tabs)');
        }
    }, [isLoggedIn, router]);

    const handleRegister = async () => {
        const normalizedEmail = email.trim().toLowerCase();
        const normalizedName = fullName.trim();

        if (!normalizedEmail || !password) {
            Alert.alert('Eksik Bilgi', 'Lutfen email ve sifre gir.');
            return;
        }
        if (password !== confirmPassword) {
            Alert.alert('Sifre Hatasi', 'Sifreler ayni degil.');
            return;
        }
        if (password.length < 8) {
            Alert.alert('Sifre Kisa', 'Sifre en az 8 karakter olmali.');
            return;
        }
        if (!/[A-Z]/.test(password)) {
            Alert.alert('Sifre Zayif', 'Sifre en az bir buyuk harf icermeli.');
            return;
        }
        if (!/\d/.test(password)) {
            Alert.alert('Sifre Zayif', 'Sifre en az bir rakam icermeli.');
            return;
        }

        try {
            setSubmitting(true);
            await register(normalizedEmail, password, normalizedName || undefined);
            router.replace('/(tabs)');
        } catch (error: any) {
            Alert.alert('Kayit Basarisiz', error?.message || 'Kayit olusturulamadi.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <ScreenWrapper>
            <KeyboardAvoidingView
                style={{ flex: 1 }}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            >
                <View className="flex-1 px-6 justify-center bg-[#0B3130]">
                    <Text className="text-[#FFD700] text-3xl font-bold mb-2">Kayit Ol</Text>
                    <Text className="text-[#C0CAC9] mb-8">
                        Hesabini olustur, manevi yolculugunu kaydet.
                    </Text>

                    <TextInput
                        value={fullName}
                        onChangeText={setFullName}
                        placeholder="Ad Soyad (opsiyonel)"
                        placeholderTextColor="#84A5A2"
                        className="bg-[#15423F] text-white rounded-xl px-4 py-4 mb-3 border border-[#436F65]"
                    />

                    <TextInput
                        value={email}
                        onChangeText={setEmail}
                        autoCapitalize="none"
                        keyboardType="email-address"
                        placeholder="Email"
                        placeholderTextColor="#84A5A2"
                        className="bg-[#15423F] text-white rounded-xl px-4 py-4 mb-3 border border-[#436F65]"
                    />

                    <TextInput
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        placeholder="Sifre (en az 8 karakter)"
                        placeholderTextColor="#84A5A2"
                        className="bg-[#15423F] text-white rounded-xl px-4 py-4 mb-3 border border-[#436F65]"
                    />

                    <TextInput
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        secureTextEntry
                        placeholder="Sifre Tekrar"
                        placeholderTextColor="#84A5A2"
                        className="bg-[#15423F] text-white rounded-xl px-4 py-4 mb-5 border border-[#436F65]"
                    />

                    <TouchableOpacity
                        onPress={handleRegister}
                        disabled={submitting}
                        className="bg-[#FFD700] rounded-xl py-4 items-center"
                    >
                        {submitting ? (
                            <ActivityIndicator color="#0B3130" />
                        ) : (
                            <Text className="text-[#0B3130] font-bold text-lg">Kayit Ol</Text>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity
                        onPress={() => router.push('/auth/login')}
                        className="mt-4 items-center"
                    >
                        <Text className="text-[#C0CAC9]">
                            Zaten hesabin var mi? <Text className="text-[#FFD700] font-bold">Giris Yap</Text>
                        </Text>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </ScreenWrapper>
    );
}
