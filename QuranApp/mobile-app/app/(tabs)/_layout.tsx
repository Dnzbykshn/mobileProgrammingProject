import { Platform, Animated, ActivityIndicator, View } from 'react-native';
import { Tabs, Redirect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useRef } from 'react';
import * as NavigationBar from 'expo-navigation-bar';
// 1. BU KÜTÜPHANEYİ EKLİYORUZ (Zorunlu)
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/contexts/AuthContext';

// Animated Chat Icon Component
function AnimatedChatIcon({ focused }: { focused: boolean }) {
  const translateY = useRef(new Animated.Value(-30)).current;
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: focused ? 0 : -30,
        duration: 800,  // 800ms = çok yavaş, akıcı
        useNativeDriver: true,
      }),
      Animated.timing(scale, {
        toValue: focused ? 0.37 : 1,  // 70px → 26px (70 * 0.37 ≈ 26)
        duration: 800,  // 800ms = çok yavaş, akıcı
        useNativeDriver: true,
      }),
    ]).start();
  }, [focused, scale, translateY]);

  return (
    <Animated.View
      style={{
        position: 'relative',
        width: 70,
        height: 70,
        borderRadius: 35,
        backgroundColor: '#C0A060',
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ translateY }, { scale }],
        // CRITICAL IMPROVEMENTS - Increased elevation and shadow
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.4,
        shadowRadius: 10,
        elevation: 15,
        borderWidth: 5,
        borderColor: '#0F3438',
        // Ensure it's above all other elements
        zIndex: 100,
      }}
    >
      <Ionicons
        name="chatbubble-ellipses"
        size={32}
        color="#0F3438"
      />
    </Animated.View>
  );
}

export default function TabLayout() {
  const { isLoading, isLoggedIn } = useAuth();
  // 2. Cihazın alt boşluğunu (Home bar / Navigasyon tuşları) alıyoruz
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (Platform.OS === 'android') {
      // Alt barı senin yeşilin yapıyoruz
      NavigationBar.setBackgroundColorAsync('#0F3438');
      NavigationBar.setButtonStyleAsync('dark'); // İkonlar beyaz olsun
    }
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" />
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
        tabBarShowLabel: false,
        sceneStyle: {
          flex: 1,
          backgroundColor: 'transparent',
        },
        tabBarStyle: {
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          elevation: 0,
          backgroundColor: '#0F3438',

          // Yuvarlak köşeler
          borderTopLeftRadius: 30,
          borderTopRightRadius: 30,
          borderTopWidth: 0,

          // --- KRİTİK DÜZELTME ---
          // Yüksekliği sabit (82) değil, dinamik yapıyoruz.
          // iOS ve Android için farklı hesaplama
          height: 32 + (Platform.OS === 'ios' ? Math.max(insets.bottom - 8, 0) : insets.bottom),

          // İkonları tuşların altında kalmasın diye yukarı itiyoruz
          paddingBottom: Platform.OS === 'ios'
            ? Math.max(insets.bottom - 8, 0)
            : 0,
          // -----------------------
        },
      }}>

      {/* 1. SOL: ANA SAYFA */}
      <Tabs.Screen
        name="index"
        options={{
          tabBarIcon: ({ focused }) => (
            <Ionicons 
              name={focused ? 'home' : 'home-outline'} 
              size={24} 
              color={focused ? '#C0A060' : '#5A7F82'} 
            />
          ),
        }}
      />

      {/* 2. SOL: KEŞFET */}
      <Tabs.Screen
        name="explore"
        options={{
          tabBarIcon: ({ focused }) => (
            <Ionicons 
              name={focused ? 'compass' : 'compass-outline'} 
              size={26} 
              color={focused ? '#C0A060' : '#5A7F82'} 
            />
          ),
        }}
      />

      {/* 3. ORTA: ASİSTAN / CHAT */}
      <Tabs.Screen
        name="chat"
        options={{
          tabBarIcon: ({ focused }) => <AnimatedChatIcon focused={focused} />,
        }}
      />

      {/* 4. SAĞ: KİTAP / AYETLER */}
      <Tabs.Screen
        name="quran"
        options={{
          tabBarIcon: ({ focused }) => (
            <Ionicons
              name={focused ? 'book' : 'book-outline'}
              size={24}
              color={focused ? '#C0A060' : '#5A7F82'}
            />
          ),
        }}
      />

      {/* MEMORIES - Tab bar'da gizli, Profile'dan erişilir */}
      <Tabs.Screen
        name="memories"
        options={{ href: null }}
      />

      {/* 5. SAĞ: PROFİL */}
      <Tabs.Screen
        name="profile"
        options={{
          tabBarIcon: ({ focused }) => (
            <Ionicons 
              name={focused ? 'person' : 'person-outline'} 
              size={24} 
              color={focused ? '#C0A060' : '#5A7F82'} 
            />
          ),
        }}
      />
    </Tabs>
  );
}
