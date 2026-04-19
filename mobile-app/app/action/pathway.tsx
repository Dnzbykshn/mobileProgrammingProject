import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Check, CheckCircle2, Clock3, Lock, PenSquare, Sparkles } from 'lucide-react-native';

import AppButton from '@/components/app/AppButton';
import AppChip from '@/components/app/AppChip';
import Day0View from '@/components/Day0View';
import EmptyState from '@/components/app/EmptyState';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import SectionTitle from '@/components/app/SectionTitle';
import SurfaceCard from '@/components/app/SurfaceCard';
import {
  completePathwayDay,
  createPathway,
  getPathway,
  Pathway,
  skipPathwayDay0,
  togglePathwayTask,
} from '@/services/pathways';
import { colors, fonts, radius, spacing, typography } from '@/theme';

export default function PathwayScreen() {
  const router = useRouter();
  const { pathwayId, pathwayType, userInput } = useLocalSearchParams<{
    pathwayId?: string;
    pathwayType?: string;
    userInput?: string;
  }>();

  const [pathway, setPathway] = useState<Pathway | null>(null);
  const [selectedDay, setSelectedDay] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pathwayId && !pathwayType) {
      setIsLoading(false);
      return;
    }

    const loadPathway = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const nextPathway = pathwayId
          ? await getPathway(pathwayId)
          : await createPathway(pathwayType || 'anxiety_management', userInput);

        setPathway(nextPathway);
        setSelectedDay(nextPathway.current_day);
      } catch {
        setError('Yol yüklenemedi.');
      } finally {
        setIsLoading(false);
      }
    };

    void loadPathway();
  }, [pathwayId, pathwayType, userInput]);

  const currentDayGroup = useMemo(
    () => pathway?.days.find((day) => day.day_number === selectedDay),
    [pathway, selectedDay]
  );
  const tasks = currentDayGroup?.tasks || [];
  const isDayComplete = tasks.length > 0 && tasks.every((task) => task.is_completed);

  const handleToggleTask = useCallback(
    async (taskId: string) => {
      if (!pathway) {
        return;
      }

      try {
        const result = await togglePathwayTask(pathway.id, taskId);
        setPathway((current) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            days: current.days.map((day) => ({
              ...day,
              tasks: day.tasks.map((task) =>
                task.id === taskId ? { ...task, is_completed: result.is_completed } : task
              ),
            })),
          };
        });
      } catch {
        Alert.alert('Hata', 'Görev durumu güncellenemedi.');
      }
    },
    [pathway]
  );

  const handleCompleteDay = useCallback(async () => {
    if (!pathway) {
      return;
    }

    try {
      const result = await completePathwayDay(pathway.id, selectedDay);
      Alert.alert('Tamamlandı', result.message);

      if (result.status === 'completed') {
        router.back();
        return;
      }

      setSelectedDay(result.current_day);
      setPathway((current) =>
        current ? { ...current, current_day: result.current_day } : current
      );
    } catch {
      Alert.alert('Hata', 'Gün tamamlanamadı.');
    }
  }, [pathway, router, selectedDay]);

  const handleSkipDay0 = useCallback(async () => {
    if (!pathway) {
      return;
    }

    try {
      const result = await skipPathwayDay0(pathway.id);
      setSelectedDay(result.current_day);
      setPathway((current) =>
        current ? { ...current, current_day: result.current_day, day0_skipped: true } : current
      );
    } catch {
      Alert.alert('Hata', 'Başlangıç günü atlanamadı.');
    }
  }, [pathway]);

  const getTaskIcon = (type: string) => {
    switch (type) {
      case 'journal':
      case 'reflection':
      case 'day0_reflection':
        return PenSquare;
      case 'morning':
      case 'evening':
        return Clock3;
      default:
        return Sparkles;
    }
  };

  if (isLoading) {
    return (
      <ScreenWrapper>
        <View
          style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl }}>
          <ActivityIndicator size="large" color={colors.gold} />
          <Text
            style={{
              ...typography.bodyMd,
              fontFamily: fonts.body,
              color: colors.text.inkMuted,
              marginTop: spacing.sm + 2,
            }}>
            Yol hazırlanıyor...
          </Text>
        </View>
      </ScreenWrapper>
    );
  }

  if (error || !pathway) {
    return (
      <ScreenWrapper>
        <View style={{ flex: 1, justifyContent: 'center', paddingHorizontal: spacing.lg }}>
          <PageHeader title="Yol" subtitle={error || 'Yol bulunamadı.'} back />
          <AppButton label="Geri dön" onPress={() => router.back()} />
        </View>
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 120,
        }}>
        <PageHeader
          title={pathway.title}
          subtitle={selectedDay === 0 ? 'Başlangıç günü' : `${selectedDay}. gün`}
          eyebrow="Yol"
          back
        />

        <SurfaceCard highlighted style={{ marginBottom: spacing.lg }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
            <View style={{ flex: 1, marginRight: spacing.md }}>
              {pathway.topic_summary ? (
                <Text
                  style={{
                    ...typography.bodyMd,
                    fontFamily: fonts.body,
                    color: colors.text.secondary,
                  }}>
                  {pathway.topic_summary}
                </Text>
              ) : null}
            </View>

            <AppChip label={pathway.status === 'completed' ? 'Tamamlandı' : 'Aktif'} active dark />
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: spacing.sm + 2, paddingTop: spacing.lg }}>
            {Array.from({ length: pathway.total_days }, (_, index) => index).map((day) => {
              const dayGroup = pathway.days.find((item) => item.day_number === day);
              const isComplete = dayGroup?.is_complete || false;
              const isCurrent = day === selectedDay;
              const isLocked = day > pathway.current_day;

              return (
                <TouchableOpacity
                  key={day}
                  onPress={() => !isLocked && setSelectedDay(day)}
                  disabled={isLocked}
                  activeOpacity={0.88}
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: radius.full,
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: isCurrent
                      ? colors.gold
                      : isComplete
                        ? colors.surface.goldSoft
                        : colors.surface.paperRaised,
                    borderWidth: 1,
                    borderColor: isCurrent
                      ? colors.border.gold
                      : isComplete
                        ? colors.border.paperStrong
                        : colors.border.paper,
                    opacity: isLocked ? 0.45 : 1,
                  }}>
                  {isLocked ? (
                    <Lock size={16} color={colors.text.inkMuted} />
                  ) : isComplete && !isCurrent ? (
                    <Check size={18} color={colors.ink} />
                  ) : (
                    <Text
                      style={{
                        ...typography.labelLg,
                        fontFamily: fonts.bodySm,
                        color: isCurrent ? colors.text.onGold : colors.ink,
                      }}>
                      {day === 0 ? 'B' : day}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </SurfaceCard>

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
            <SectionTitle title="Bugünün görevleri" />

            {tasks.length === 0 ? (
              <EmptyState message="Bu gün için görev bulunmuyor." />
            ) : (
              <View style={{ gap: spacing.md }}>
                {tasks.map((task) => {
                  const Icon = getTaskIcon(task.task_type);

                  return (
                    <TouchableOpacity
                      key={task.id}
                      onPress={() => {
                        void handleToggleTask(task.id);
                      }}
                      activeOpacity={0.88}>
                      <SurfaceCard compact highlighted={task.is_completed}>
                        <View
                          style={{
                            flexDirection: 'row',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                          }}>
                          <View
                            style={{
                              flexDirection: 'row',
                              alignItems: 'center',
                              flex: 1,
                              marginRight: spacing.md,
                            }}>
                            <View
                              style={{
                                width: 34,
                                height: 34,
                                borderRadius: radius.full,
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: task.is_completed
                                  ? colors.surface.goldSoft
                                  : colors.surface.strong,
                                marginRight: spacing.md,
                              }}>
                              {task.is_completed ? (
                                <CheckCircle2 size={18} color={colors.gold} />
                              ) : (
                                <Icon size={16} color={colors.text.secondary} />
                              )}
                            </View>

                            <View style={{ flex: 1 }}>
                              <Text
                                style={{
                                  ...typography.labelLg,
                                  fontFamily: fonts.bodyMd,
                                  color: colors.text.primary,
                                  textDecorationLine: task.is_completed ? 'line-through' : 'none',
                                }}>
                                {task.title}
                              </Text>

                              {task.description ? (
                                <Text
                                  style={{
                                    ...typography.bodySm,
                                    fontFamily: fonts.body,
                                    color: colors.text.secondary,
                                    marginTop: spacing.xs + 2,
                                  }}>
                                  {task.description}
                                </Text>
                              ) : null}
                            </View>
                          </View>

                          {task.duration_minutes ? (
                            <AppChip label={`${task.duration_minutes} dk`} dark />
                          ) : null}
                        </View>
                      </SurfaceCard>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

            <AppButton
              label={isDayComplete ? 'Günü tamamla' : 'Tüm görevleri bitir'}
              icon={Sparkles}
              onPress={handleCompleteDay}
              disabled={!isDayComplete}
              style={{ marginTop: spacing.xl }}
            />
          </>
        )}
      </ScrollView>
    </ScreenWrapper>
  );
}
