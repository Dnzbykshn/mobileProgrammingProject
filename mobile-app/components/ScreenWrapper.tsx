import React from 'react';
import { View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Edge, SafeAreaView } from 'react-native-safe-area-context';

import IslamicMedallion from '@/components/app/IslamicMedallion';
import { colors } from '@/theme';

type ScreenWrapperProps = {
  children: React.ReactNode;
  backgroundColor?: string;
  statusBarStyle?: 'light' | 'dark';
  edges?: Edge[];
  withDecoration?: boolean;
};

export default function ScreenWrapper({
  children,
  backgroundColor = colors.night,
  statusBarStyle = 'light',
  edges = ['top', 'left', 'right'],
  withDecoration = true,
}: ScreenWrapperProps) {
  return (
    <View style={{ flex: 1, backgroundColor }}>
      <StatusBar style={statusBarStyle} />
      {withDecoration && <IslamicMedallion variant="top" />}
      <SafeAreaView style={{ flex: 1 }} edges={edges}>
        {children}
      </SafeAreaView>
    </View>
  );
}
