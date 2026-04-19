import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { Fraunces_700Bold } from '@expo-google-fonts/fraunces';
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { Amiri_400Regular, Amiri_700Bold } from '@expo-google-fonts/amiri';

import { AuthProvider } from '@/contexts/AuthContext';
import { colors } from '@/theme';

void SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Fraunces_700Bold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Amiri_400Regular,
    Amiri_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      void SplashScreen.hideAsync();
    }
  }, [fontError, fontsLoaded]);

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <Stack screenOptions={{ headerShown: false, animation: 'fade' }}>
          <Stack.Screen
            name="index"
            options={{ contentStyle: { backgroundColor: colors.night } }}
          />
          <Stack.Screen
            name="(tabs)"
            options={{
              animation: 'fade',
              contentStyle: { backgroundColor: colors.night },
            }}
          />
          <Stack.Screen
            name="auth/login"
            options={{ contentStyle: { backgroundColor: colors.night } }}
          />
          <Stack.Screen
            name="auth/register"
            options={{ contentStyle: { backgroundColor: colors.night } }}
          />
          <Stack.Screen
            name="settings"
            options={{
              presentation: 'modal',
              animation: 'slide_from_bottom',
              contentStyle: { backgroundColor: colors.night },
            }}
          />
          <Stack.Screen
            name="settings-sessions"
            options={{
              presentation: 'modal',
              animation: 'slide_from_bottom',
              contentStyle: { backgroundColor: colors.night },
            }}
          />
        </Stack>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
