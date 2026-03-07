import React from 'react';
import { View, Text } from 'react-native';
import ScreenWrapper from '@/components/ScreenWrapper';

export default function QuranScreen() {
    return (
        <ScreenWrapper>
            <View className="flex-1 items-center justify-center">
                <Text className="text-white text-xl font-bold">Yakında</Text>
            </View>
        </ScreenWrapper>
    );
}
