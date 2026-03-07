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

export default function LoginScreen() {
    const router = useRouter();
    const { login, isLoggedIn } = useAuth();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (isLoggedIn) {
            router.replace('/(tabs)');
        }
    }, [isLoggedIn, router]);

    const handleLogin = async () => {
        const normalizedEmail = email.trim().toLowerCase();
        if (!normalizedEmail || !password) {
            Alert.alert('Eksik Bilgi', 'Lutfen email ve sifre gir.');
            return;
        }

        try {
            setSubmitting(true);
            await login(normalizedEmail, password);
            router.replace('/(tabs)');
        } catch (error: any) {
            Alert.alert('Giris Basarisiz', error?.message || 'Email veya sifre hatali.');
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
                    <Text className="text-[#FFD700] text-3xl font-bold mb-2">Giris Yap</Text>
                    <Text className="text-[#C0CAC9] mb-8">
                        Hesabina girerek kisilesmis deneyime devam et.
                    </Text>

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
                        placeholder="Sifre"
                        placeholderTextColor="#84A5A2"
                        className="bg-[#15423F] text-white rounded-xl px-4 py-4 mb-5 border border-[#436F65]"
                    />

                    <TouchableOpacity
                        onPress={handleLogin}
                        disabled={submitting}
                        className="bg-[#FFD700] rounded-xl py-4 items-center"
                    >
                        {submitting ? (
                            <ActivityIndicator color="#0B3130" />
                        ) : (
                            <Text className="text-[#0B3130] font-bold text-lg">Giris Yap</Text>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity
                        onPress={() => router.push('/auth/register')}
                        className="mt-4 items-center"
                    >
                        <Text className="text-[#C0CAC9]">
                            Hesabin yok mu? <Text className="text-[#FFD700] font-bold">Kayit Ol</Text>
                        </Text>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </ScreenWrapper>
    );
}
