import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { Heart, BookOpen, Sparkles, Check, ChevronRight } from 'lucide-react-native';
import { PlanTask } from '@/services/plans';

interface Day0ViewProps {
    tasks: PlanTask[];
    onToggleTask: (taskId: string) => void;
    onSkipDay0: () => void;
    onCompleteDay: () => void;
    isDayComplete: boolean;
}

export default function Day0View({
    tasks,
    onToggleTask,
    onSkipDay0,
    onCompleteDay,
    isDayComplete,
}: Day0ViewProps) {
    // Group tasks by type
    const verseTasks = tasks.filter(t => t.task_type === 'day0_verse');
    const duaTasks = tasks.filter(t => t.task_type === 'day0_dua');
    const esmaTasks = tasks.filter(t => t.task_type === 'day0_esma');
    const routineTask = tasks.find(t => t.task_type === 'day0_routine');

    // Counter for routine task
    const [routineCount, setRoutineCount] = useState(0);
    const targetCount = routineTask?.task_metadata?.target_count || 33;

    const handleRoutineTap = () => {
        if (routineCount < targetCount) {
            setRoutineCount(c => c + 1);
        }
        // Auto-complete when target reached
        if (routineCount + 1 >= targetCount && routineTask && !routineTask.is_completed) {
            setTimeout(() => onToggleTask(routineTask.id), 300);
        }
    };

    return (
        <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 100 }}>
            {/* Header */}
            <View className="mb-8">
                <Text className="text-[#FFD700] text-2xl font-serif font-bold text-center mb-2">
                    Yolculuğa Hoş Geldin
                </Text>
                <Text className="text-[#C0CAC9] text-center text-sm leading-6">
                    Önce rutinni incele, sonra 7 günlük yolculuğuna başla.
                </Text>
            </View>

            {/* Verses Section */}
            {verseTasks.length > 0 && (
                <View className="mb-8">
                    <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-4">
                        Kalbine İyi Gelecek Ayetler
                    </Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-4 -mx-6 px-6">
                        {verseTasks.map((task, idx) => {
                            const verse = task.task_metadata || {};
                            return (
                                <TouchableOpacity
                                    key={task.id}
                                    onPress={() => onToggleTask(task.id)}
                                    className={`bg-[#113835] w-[280px] p-5 rounded-2xl border mr-3 ${task.is_completed ? 'border-[#FFD700]' : 'border-[#436F65]'
                                        }`}
                                >
                                    {task.is_completed && (
                                        <View className="absolute top-2 right-2 bg-[#FFD700] rounded-full p-1">
                                            <Check size={14} color="#0B3130" />
                                        </View>
                                    )}
                                    <Text className="text-[#FFD700] text-xs font-bold mb-3">{task.title}</Text>
                                    <Text className="text-[#E5E9E9] text-base font-serif mb-4 leading-6">
                                        "{task.description || verse.turkish_text}"
                                    </Text>
                                </TouchableOpacity>
                            );
                        })}
                    </ScrollView>
                </View>
            )}

            {/* Esma Section */}
            {esmaTasks.length > 0 && (
                <View className="mb-8">
                    <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-2">
                        Önerilen Esmalar
                    </Text>
                    <Text className="text-[#436F65] text-xs italic mb-4">(İsteğe Bağlı)</Text>
                    <View className="space-y-3">
                        {esmaTasks.map(task => {
                            const esma = task.task_metadata || {};
                            return (
                                <TouchableOpacity
                                    key={task.id}
                                    onPress={() => onToggleTask(task.id)}
                                    className={`bg-[#113835] p-4 rounded-xl border flex-row justify-between items-center ${task.is_completed ? 'border-[#FFD700]' : 'border-[#436F65]'
                                        }`}
                                >
                                    <View className="flex-1">
                                        <Text className="text-[#E5E9E9] text-base font-medium">{task.title}</Text>
                                        {task.description && (
                                            <Text className="text-[#C0CAC9] text-xs mt-1">{task.description}</Text>
                                        )}
                                    </View>
                                    <View className="flex-row items-center">
                                        {task.is_completed && <Check size={18} color="#FFD700" className="mr-2" />}
                                        {esma.recommended_count && (
                                            <Text className="text-[#FFD700] font-bold mr-2">
                                                {esma.recommended_count}x
                                            </Text>
                                        )}
                                        <Sparkles size={16} color="#436F65" />
                                    </View>
                                </TouchableOpacity>
                            );
                        })}
                    </View>
                </View>
            )}

            {/* Dua Section */}
            {duaTasks.length > 0 && (
                <View className="mb-8">
                    <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-4">Önerilen Dualar</Text>
                    <View className="space-y-3">
                        {duaTasks.map(task => {
                            const dua = task.task_metadata || {};
                            return (
                                <TouchableOpacity
                                    key={task.id}
                                    onPress={() => onToggleTask(task.id)}
                                    className={`bg-[#113835] p-4 rounded-xl border ${task.is_completed ? 'border-[#FFD700]' : 'border-[#436F65]'
                                        }`}
                                >
                                    <View className="flex-row items-center mb-2">
                                        <Heart size={14} color="#FFD700" />
                                        <Text className="text-[#FFD700] text-xs font-bold ml-2">{task.title}</Text>
                                        {task.is_completed && (
                                            <Check size={14} color="#FFD700" className="ml-auto" />
                                        )}
                                    </View>
                                    {dua.arabic_text && (
                                        <Text className="text-[#E5E9E9] text-lg text-right mb-2 leading-8">
                                            {dua.arabic_text}
                                        </Text>
                                    )}
                                    {task.description && (
                                        <Text className="text-[#C0CAC9] text-sm italic">"{task.description}"</Text>
                                    )}
                                </TouchableOpacity>
                            );
                        })}
                    </View>
                </View>
            )}

            {/* Routine Counter Section */}
            {routineTask && (
                <View className="mb-8">
                    <Text className="text-[#E5E9E9] text-xl font-serif font-bold mb-4">3 Dakikalık Acil Rutin</Text>
                    <View className="bg-[#1A4642] p-6 rounded-2xl border-2 border-[#FFD700]">
                        {/* Arabic Text */}
                        <View className="items-center mb-8">
                            <Text className="text-[#E5E9E9] text-3xl text-center mb-4 leading-10">
                                {routineTask.task_metadata?.arabic_text || 'حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ'}
                            </Text>
                            <Text className="text-[#C0CAC9] italic text-center text-base">
                                "{routineTask.description}"
                            </Text>
                        </View>

                        {/* Counter Circle */}
                        <TouchableOpacity
                            onPress={handleRoutineTap}
                            activeOpacity={0.8}
                            className={`self-center w-48 h-48 rounded-full justify-center items-center border-4 ${routineCount >= targetCount
                                    ? 'border-[#FFD700] bg-[#1A4642]'
                                    : 'border-[#FFD700] bg-[#113835]'
                                }`}
                            style={{
                                shadowColor: '#FFD700',
                                shadowOffset: { width: 0, height: 0 },
                                shadowOpacity: 0.3,
                                shadowRadius: 20,
                                elevation: 10,
                            }}
                        >
                            {routineCount >= targetCount ? (
                                <Check color="#FFD700" size={64} />
                            ) : (
                                <View className="items-center">
                                    <Text className="text-[#FFD700] text-6xl font-bold">{routineCount}</Text>
                                    <Text className="text-[#436F65] text-xl">/{targetCount}</Text>
                                </View>
                            )}
                        </TouchableOpacity>

                        <Text className="text-[#436F65] mt-6 italic text-center text-sm">
                            (Dokunarak sayınız)
                        </Text>
                    </View>
                </View>
            )}

            {/* Action Buttons */}
            <View className="space-y-4 mt-8">
                {/* Skip Day 0 */}
                <TouchableOpacity
                    onPress={onSkipDay0}
                    className="border-2 border-[#436F65] py-4 rounded-2xl items-center flex-row justify-center"
                >
                    <Text className="text-[#436F65] font-bold text-base mr-2">Gün 0'ı Atla → Gün 1'e Geç</Text>
                    <ChevronRight size={18} color="#436F65" />
                </TouchableOpacity>

                {/* Complete Day 0 */}
                <TouchableOpacity
                    disabled={!isDayComplete}
                    onPress={onCompleteDay}
                    className={`py-4 rounded-2xl items-center flex-row justify-center ${isDayComplete ? 'bg-[#FFD700]' : 'bg-[#436F65] opacity-50'
                        }`}
                >
                    {isDayComplete && <Sparkles size={20} color="#0B3130" className="mr-2" />}
                    <Text className={`font-bold text-lg ${isDayComplete ? 'text-[#0B3130]' : 'text-[#113835]'}`}>
                        {isDayComplete ? 'Gün 0 Tamamlandı ✓' : 'Gün 0\'ı Tamamla'}
                    </Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}
