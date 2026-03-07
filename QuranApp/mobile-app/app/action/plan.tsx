import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, Check, Edit2, Lock, Sparkles } from 'lucide-react-native';
import { createPlan, getPlan, toggleTask, completeDay, skipDay0, Plan, DayGroup, PlanTask } from '@/services/plans';
import Day0View from '@/components/Day0View';

export default function PlanScreen() {
    const router = useRouter();
    const { planId, journeyType, prescriptionId, userInput } = useLocalSearchParams<{
        planId?: string;
        journeyType?: string;
        prescriptionId?: string;
        userInput?: string;
    }>();

    const [plan, setPlan] = useState<Plan | null>(null);
    const [selectedDay, setSelectedDay] = useState(1);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Load or create plan — only when navigated with params
    useEffect(() => {
        // Skip if no params (screen opened from tab bar or back)
        if (!planId && !journeyType && !prescriptionId) {
            setIsLoading(false);
            return;
        }

        const loadPlan = async () => {
            setIsLoading(true);
            setError(null);
            try {
                if (planId) {
                    const result = await getPlan(planId);
                    setPlan(result);
                    setSelectedDay(result.current_day);
                } else {
                    const result = await createPlan(
                        journeyType || 'anxiety_management',
                        prescriptionId,
                        userInput,
                    );
                    setPlan(result);
                    setSelectedDay(result.current_day);
                }
            } catch (err) {
                console.error('Plan error:', err);
                setError('Plan yüklenemedi. Lütfen tekrar deneyin.');
            } finally {
                setIsLoading(false);
            }
        };
        loadPlan();
    }, [planId, journeyType, prescriptionId, userInput]);

    // Get current day's tasks
    const currentDayGroup = plan?.days.find(d => d.day_number === selectedDay);
    const tasks = currentDayGroup?.tasks || [];
    const isDayComplete = tasks.length > 0 && tasks.every(t => t.is_completed);

    // Toggle task
    const handleToggleTask = useCallback(async (taskId: string) => {
        if (!plan) return;
        try {
            const result = await toggleTask(plan.id, taskId);
            // Update local state
            setPlan(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    days: prev.days.map(day => ({
                        ...day,
                        tasks: day.tasks.map(task =>
                            task.id === taskId
                                ? { ...task, is_completed: result.is_completed }
                                : task
                        ),
                    })),
                };
            });
        } catch (err) {
            console.error('Toggle error:', err);
        }
    }, [plan]);

    // Complete day
    const handleCompleteDay = useCallback(async () => {
        if (!plan) return;
        try {
            const result = await completeDay(plan.id, selectedDay);
            Alert.alert('🎉', result.message);
            if (result.status === 'completed') {
                router.back();
            } else {
                setSelectedDay(result.current_day);
                setPlan(prev => prev ? { ...prev, current_day: result.current_day } : prev);
            }
        } catch (err) {
            console.error('Complete day error:', err);
        }
    }, [plan, selectedDay, router]);

    // Skip Day 0
    const handleSkipDay0 = useCallback(async () => {
        if (!plan) return;
        try {
            const result = await skipDay0(plan.id);
            setSelectedDay(result.current_day);
            setPlan(prev => prev ? { ...prev, current_day: result.current_day, day0_skipped: true } : prev);
        } catch (err) {
            console.error('Skip day0 error:', err);
        }
    }, [plan]);

    // Task icon based on type
    const getTaskIcon = (type: string) => {
        switch (type) {
            case 'morning': return '🌅';
            case 'evening': return '🌙';
            case 'journal': return '📝';
            default: return '📿';
        }
    };

    if (isLoading) {
        return (
            <SafeAreaView className="flex-1 bg-[#0B3130] justify-center items-center">
                <ActivityIndicator size="large" color="#FFD700" />
                <Text className="text-[#C0CAC9] mt-4">Plan hazırlanıyor...</Text>
            </SafeAreaView>
        );
    }

    if (error || !plan) {
        return (
            <SafeAreaView className="flex-1 bg-[#0B3130] justify-center items-center p-8">
                <Text className="text-[#C0CAC9] text-center text-lg mb-4">{error || 'Plan bulunamadı'}</Text>
                <TouchableOpacity onPress={() => router.back()} className="bg-[#FFD700] px-6 py-3 rounded-xl">
                    <Text className="text-[#0B3130] font-bold">Geri Dön</Text>
                </TouchableOpacity>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView className="flex-1 bg-[#0B3130]" edges={['top']}>
            {/* Header */}
            <View className="bg-[#113835] pb-4">
                <View className="flex-row items-start p-4">
                    <TouchableOpacity onPress={() => router.back()} className="p-2 -ml-2">
                        <ChevronLeft color="#C0CAC9" size={24} />
                    </TouchableOpacity>
                    <View className="ml-2 flex-1">
                        <Text className="text-[#E5E9E9] text-lg font-serif font-bold">{plan.journey_title}</Text>
                        <Text className="text-[#C0CAC9] text-sm mt-1">
                            {selectedDay}. Gün / {plan.total_days}
                        </Text>
                    </View>
                    {plan.status === 'completed' && (
                        <View className="bg-[#FFD700] px-3 py-1 rounded-full">
                            <Text className="text-[#0B3130] text-xs font-bold">Tamamlandı</Text>
                        </View>
                    )}
                </View>

                {/* Day Selector */}
                <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mt-2 px-4">
                    {Array.from({ length: plan.total_days }, (_, i) => i).map(day => {
                        const dayGroup = plan.days.find(d => d.day_number === day);
                        const isComplete = dayGroup?.is_complete || false;
                        const isCurrent = day === selectedDay;
                        const isLocked = day > plan.current_day;
                        const isDay0 = day === 0;

                        return (
                            <TouchableOpacity
                                key={day}
                                onPress={() => !isLocked && setSelectedDay(day)}
                                disabled={isLocked}
                                className={`mr-3 w-12 h-12 rounded-full items-center justify-center ${
                                    isCurrent
                                        ? 'bg-[#FFD700]'
                                        : isComplete
                                        ? 'bg-[#1A4642] border-2 border-[#FFD700]'
                                        : isLocked
                                        ? 'border border-[#1A4642] opacity-40'
                                        : 'border border-[#436F65]'
                                }`}
                            >
                                {isComplete && !isCurrent ? (
                                    <Check size={18} color="#FFD700" />
                                ) : (
                                    <Text className={`font-bold ${isCurrent ? 'text-[#0B3130]' : isLocked ? 'text-[#1A4642]' : 'text-[#436F65]'}`}>
                                        {day}
                                    </Text>
                                )}
                            </TouchableOpacity>
                        );
                    })}
                </ScrollView>
            </View>

            <ScrollView className="flex-1" contentContainerStyle={{ padding: selectedDay === 0 ? 0 : 24 }}>

                {selectedDay === 0 ? (
                    <Day0View
                        tasks={tasks}
                        onToggleTask={handleToggleTask}
                        onSkipDay0={handleSkipDay0}
                        onCompleteDay={handleCompleteDay}
                        isDayComplete={isDayComplete}
                    />
                ) : (
                    <>
                        <View className="flex-row items-center mb-6">
                            <Text className="text-[#E5E9E9] text-xl font-serif font-bold">Bugünün Görevleri</Text>
                        </View>

                        {/* Tasks */}
                        {tasks.map((task) => (
                    <TouchableOpacity
                        key={task.id}
                        onPress={() => handleToggleTask(task.id)}
                        className="bg-[#113835] p-4 rounded-2xl border border-[#436F65] mb-4 flex-row items-center justify-between"
                    >
                        <View className="flex-row items-center flex-1">
                            <View className={`w-6 h-6 rounded-md border-2 ${task.is_completed ? 'bg-[#FFD700] border-[#FFD700]' : 'border-[#436F65]'} items-center justify-center mr-3`}>
                                {task.is_completed && <Check size={16} color="#0B3130" />}
                            </View>
                            <View className="flex-1">
                                <Text className={`text-base font-medium ${task.is_completed ? 'text-[#436F65] line-through' : 'text-[#E5E9E9]'}`}>
                                    {getTaskIcon(task.task_type)} {task.title}
                                </Text>
                                {task.description && (
                                    <Text className="text-[#C0CAC9] text-sm">{task.description}</Text>
                                )}
                            </View>
                        </View>
                        {task.task_type === 'journal' ? (
                            <Edit2 size={20} color="#436F65" />
                        ) : task.duration_minutes ? (
                            <View className="bg-[#0B3130] px-2 py-1 rounded-lg">
                                <Text className="text-[#436F65] text-xs">{task.duration_minutes} dk</Text>
                            </View>
                        ) : null}
                    </TouchableOpacity>
                ))}

                        {/* Complete Day CTA */}
                        <View className="mt-8">
                            <TouchableOpacity
                                disabled={!isDayComplete}
                                onPress={handleCompleteDay}
                                className={`py-4 rounded-2xl items-center flex-row justify-center ${isDayComplete ? 'bg-[#FFD700]' : 'bg-[#436F65] opacity-50'}`}
                            >
                                {isDayComplete ? <Sparkles size={20} color="#0B3130" /> : <Lock size={18} color="#113835" />}
                                <Text className={`font-bold text-lg ml-2 ${isDayComplete ? 'text-[#0B3130]' : 'text-[#113835]'}`}>
                                    {isDayComplete ? 'Günü Tamamla ✓' : 'Günü Tamamla'}
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </>
                )}

            </ScrollView>
        </SafeAreaView>
    );
}
