import { ActivityIndicator, Platform, View } from 'react-native';
import { Redirect, Tabs } from 'expo-router';
import React, { useEffect } from 'react';
import * as NavigationBar from 'expo-navigation-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BookOpen, Home, MessageCircleMore, ScrollText, UserRound } from 'lucide-react-native';

import { useAuth } from '@/contexts/AuthContext';
import { colors, fonts, radius, shadows } from '@/theme';

export default function TabLayout() {
  const { isLoading, isLoggedIn } = useAuth();
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (Platform.OS === 'android') {
      void NavigationBar.setBackgroundColorAsync(colors.surface.raised);
      void NavigationBar.setButtonStyleAsync('light');
    }
  }, []);

  if (isLoading) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: colors.night,
        }}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  if (!isLoggedIn) {
    return <Redirect href="/auth/login" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: 'transparent' },
        tabBarActiveTintColor: colors.gold,
        tabBarInactiveTintColor: colors.text.muted,
        tabBarHideOnKeyboard: false,
        tabBarLabelStyle: {
          fontSize: 11,
          fontFamily: fonts.bodyMd,
          marginTop: 2,
        },
        tabBarStyle: {
          position: 'absolute',
          left: 14,
          right: 14,
          bottom: 12,
          height: 70 + Math.max(insets.bottom - 4, 0),
          paddingTop: 10,
          paddingBottom: 10 + Math.max(insets.bottom - 4, 0),
          backgroundColor: colors.surface.raised,
          borderTopWidth: 1,
          borderTopColor: colors.border.soft,
          borderRadius: radius.xxl,
          ...shadows.md,
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Bugün',
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Yollar',
          tabBarIcon: ({ color, size }) => <ScrollText size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Sohbet',
          tabBarIcon: ({ color, size }) => <MessageCircleMore size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="quran"
        options={{
          title: 'İçerik',
          tabBarIcon: ({ color, size }) => <BookOpen size={size} color={color} />,
        }}
      />
      <Tabs.Screen name="memories" options={{ href: null }} />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profil',
          tabBarIcon: ({ color, size }) => <UserRound size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
