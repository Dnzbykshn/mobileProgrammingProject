import React from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Heart, Share2, ChevronRight, Lightbulb } from 'lucide-react-native';

export default function ReadingScreen() {
    const router = useRouter();

    return (
        <SafeAreaView className="flex-1 bg-[#0B3130]" edges={['top']}>
            {/* Header */}
            <View className="flex-row justify-between items-center p-4 border-b border-[#113835] bg-[#113835]">
                <TouchableOpacity onPress={() => router.back()} className="p-2">
                    <ChevronLeft color="#C0CAC9" size={24} />
                </TouchableOpacity>
                <Text className="text-[#E5E9E9] text-base font-serif font-bold">İnşirah, 5-6</Text>
                <View className="flex-row space-x-4">
                    <TouchableOpacity><Heart color="#C0CAC9" size={22} /></TouchableOpacity>
                    <TouchableOpacity><Share2 color="#C0CAC9" size={22} /></TouchableOpacity>
                </View>
            </View>

            <ScrollView className="flex-1" contentContainerStyle={{ padding: 24 }}>

                {/* ARABIC TEXT */}
                <View className="mt-8 mb-6 py-4">
                    <Text className="text-[#E5E9E9] text-3xl text-center leading-[60px] font-serif">
                        فَإِنَّ مَعَ ٱلۡعُسۡرِ يُسۡرًا{'\n'}
                        إِنَّ مَعَ ٱلۡعُسۡرِ يُسۡرًا
                    </Text>
                </View>

                <View className="h-[1px] bg-[#113835] w-full mb-8" />

                {/* TURKISH TRANSLATION */}
                <Text className="text-[#E5E9E9] text-xl font-serif leading-8 text-center mb-8">
                    "Şüphesiz zorlukla beraber bir kolaylık vardır. Muhakkak ki zorlukla beraber bir kolaylık vardır."
                </Text>

                {/* CONTEXT BOX */}
                <View className="bg-[#113835] p-5 rounded-2xl border border-[#436F65] mb-10 shadow-sm">
                    <View className="flex-row items-center mb-3">
                        <Lightbulb color="#FFD700" size={24} />
                        <Text className="text-[#FFD700] text-base font-bold ml-2">Neden Bu Ayet?</Text>
                    </View>
                    <Text className="text-[#C0CAC9] text-base leading-7">
                        Bu ayet, darlığın ardından mutlaka ferahlığın geleceğini müjdeler. Senin şu an hissettiğin sıkışmışlık hissine bir cevaptır.
                    </Text>
                </View>

                {/* NAVIGATION */}
                <TouchableOpacity className="border border-[#436F65] p-4 rounded-xl flex-row justify-between items-center active:bg-[#113835]">
                    <Text className="text-[#E5E9E9] font-medium text-base ml-2">Sonraki Ayet</Text>
                    <ChevronRight color="#FFD700" size={20} className="mr-2" />
                </TouchableOpacity>

            </ScrollView>
        </SafeAreaView>
    );
}
