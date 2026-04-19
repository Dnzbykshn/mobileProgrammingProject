import React, { useEffect, useMemo, useState } from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { BookOpen, Check, ChevronRight, Heart, NotebookPen, Sparkles } from 'lucide-react-native';

import AppButton from '@/components/app/AppButton';
import AppChip from '@/components/app/AppChip';
import SectionTitle from '@/components/app/SectionTitle';
import SurfaceCard from '@/components/app/SurfaceCard';
import { PathwayTask } from '@/services/pathways';
import { colors, fonts, radius, spacing, typography } from '@/theme';

interface Day0ViewProps {
  tasks: PathwayTask[];
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
  const verseTasks = tasks.filter((task) => task.task_type === 'day0_verse');
  const duaTasks = tasks.filter((task) => task.task_type === 'day0_dua');
  const esmaTasks = tasks.filter((task) => task.task_type === 'day0_esma');
  const routineTask = tasks.find((task) => task.task_type === 'day0_routine');
  const introTasks = useMemo(
    () =>
      tasks.filter(
        (task) =>
          task.task_type === 'day0_intro' ||
          task.task_type === 'day0_reflection' ||
          (task.task_type.startsWith('day0_') &&
            !['day0_verse', 'day0_dua', 'day0_esma', 'day0_routine'].includes(task.task_type))
      ),
    [tasks]
  );

  const targetCount = routineTask?.task_metadata?.target_count || 33;
  const [routineCount, setRoutineCount] = useState(routineTask?.is_completed ? targetCount : 0);

  useEffect(() => {
    setRoutineCount(routineTask?.is_completed ? targetCount : 0);
  }, [routineTask?.id, routineTask?.is_completed, targetCount]);

  const handleRoutineTap = () => {
    if (routineCount < targetCount) {
      setRoutineCount((count: number) => count + 1);
    }

    if (routineCount + 1 >= targetCount && routineTask && !routineTask.is_completed) {
      setTimeout(() => onToggleTask(routineTask.id), 220);
    }
  };

  return (
    <View>
      <SurfaceCard highlighted style={{ marginBottom: spacing.lg }}>
        <Text
          style={{
            ...typography.h2,
            fontFamily: fonts.heading,
            color: colors.text.primary,
            marginBottom: spacing.sm,
          }}>
          Başlangıç Günü
        </Text>
        <Text
          style={{
            ...typography.bodyLg,
            fontFamily: fonts.body,
            color: colors.text.secondary,
          }}>
          İlk adımları tamamla, sonra yolun açılır.
        </Text>
      </SurfaceCard>

      {introTasks.length > 0 ? (
        <View style={{ marginBottom: spacing.lg }}>
          <SectionTitle title="Yola giriş" dark />

          <View style={{ gap: spacing.md }}>
            {introTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                onPress={() => onToggleTask(task.id)}
                activeOpacity={0.85}>
                <SurfaceCard compact highlighted={task.is_completed}>
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      marginBottom: spacing.sm + 2,
                    }}>
                    <NotebookPen size={16} color={colors.gold} />
                    <Text
                      style={{
                        ...typography.labelLg,
                        fontFamily: fonts.bodyMd,
                        color: colors.gold,
                        marginLeft: spacing.sm,
                        flex: 1,
                      }}>
                      {task.title}
                    </Text>
                    {task.is_completed ? <Check size={16} color={colors.gold} /> : null}
                  </View>

                  {task.description ? (
                    <Text
                      style={{
                        ...typography.bodyMd,
                        fontFamily: fonts.body,
                        color: colors.text.secondary,
                      }}>
                      {task.description}
                    </Text>
                  ) : null}
                </SurfaceCard>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}

      {verseTasks.length > 0 ? (
        <View style={{ marginBottom: spacing.lg }}>
          <SectionTitle title="Ayetler" dark />
          <View style={{ gap: spacing.md }}>
            {verseTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                onPress={() => onToggleTask(task.id)}
                activeOpacity={0.85}>
                <SurfaceCard compact highlighted={task.is_completed}>
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      marginBottom: spacing.sm + 2,
                    }}>
                    <BookOpen size={16} color={colors.gold} />
                    <Text
                      style={{
                        ...typography.labelLg,
                        fontFamily: fonts.bodyMd,
                        color: colors.gold,
                        marginLeft: spacing.sm,
                        flex: 1,
                      }}>
                      {task.title}
                    </Text>
                    {task.is_completed ? <Check size={16} color={colors.gold} /> : null}
                  </View>

                  <Text
                    style={{
                      ...typography.bodyLg,
                      fontFamily: fonts.body,
                      color: colors.text.primary,
                    }}>
                    {task.description || String(task.task_metadata?.turkish_text || '')}
                  </Text>
                </SurfaceCard>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}

      {esmaTasks.length > 0 ? (
        <View style={{ marginBottom: spacing.lg }}>
          <SectionTitle title="Esmalar" dark />
          <View style={{ gap: spacing.md }}>
            {esmaTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                onPress={() => onToggleTask(task.id)}
                activeOpacity={0.85}>
                <SurfaceCard compact highlighted={task.is_completed}>
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}>
                    <View style={{ flex: 1, marginRight: spacing.md }}>
                      <Text
                        style={{
                          ...typography.bodyLg,
                          fontFamily: fonts.bodyMd,
                          color: colors.text.primary,
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
                    <AppChip
                      label={`${task.task_metadata?.recommended_count || 33}x`}
                      active={task.is_completed}
                      dark
                    />
                  </View>
                </SurfaceCard>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}

      {duaTasks.length > 0 ? (
        <View style={{ marginBottom: spacing.lg }}>
          <SectionTitle title="Dualar" dark />

          <View style={{ gap: spacing.md }}>
            {duaTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                onPress={() => onToggleTask(task.id)}
                activeOpacity={0.85}>
                <SurfaceCard compact highlighted={task.is_completed}>
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      marginBottom: spacing.sm + 2,
                    }}>
                    <Heart size={16} color={colors.gold} />
                    <Text
                      style={{
                        ...typography.labelLg,
                        fontFamily: fonts.bodyMd,
                        color: colors.gold,
                        marginLeft: spacing.sm,
                        flex: 1,
                      }}>
                      {task.title}
                    </Text>
                    {task.is_completed ? <Check size={16} color={colors.gold} /> : null}
                  </View>

                  {task.task_metadata?.arabic_text ? (
                    <Text
                      style={{
                        ...typography.arabicMd,
                        fontFamily: fonts.arabic,
                        color: colors.text.primary,
                        textAlign: 'right',
                        marginBottom: spacing.sm + 2,
                      }}>
                      {task.task_metadata.arabic_text}
                    </Text>
                  ) : null}

                  {task.description ? (
                    <Text
                      style={{
                        ...typography.bodyMd,
                        fontFamily: fonts.body,
                        color: colors.text.secondary,
                      }}>
                      {task.description}
                    </Text>
                  ) : null}
                </SurfaceCard>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}

      {routineTask ? (
        <View style={{ marginBottom: spacing.xl }}>
          <SectionTitle title="Zikir sayacı" dark />

          <SurfaceCard highlighted>
            <Text
              style={{
                ...typography.bodyLg,
                fontFamily: fonts.body,
                color: colors.text.primary,
                textAlign: 'center',
                marginBottom: spacing.sm + 2,
              }}>
              {routineTask.description}
            </Text>

            {routineTask.task_metadata?.arabic_text ? (
              <Text
                style={{
                  ...typography.arabicLg,
                  fontFamily: fonts.arabic,
                  color: colors.text.primary,
                  textAlign: 'center',
                  marginBottom: spacing.lg,
                }}>
                {routineTask.task_metadata.arabic_text}
              </Text>
            ) : null}

            <TouchableOpacity
              onPress={handleRoutineTap}
              activeOpacity={0.85}
              style={{
                alignSelf: 'center',
                width: 180,
                height: 180,
                borderRadius: radius.full,
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor:
                  routineCount >= targetCount ? colors.surface.goldSoft : colors.surface.muted,
                borderWidth: 2,
                borderColor: colors.border.accent,
              }}>
              {routineCount >= targetCount ? (
                <Check size={54} color={colors.gold} />
              ) : (
                <>
                  <Text
                    style={{
                      ...typography.display,
                      fontFamily: fonts.heading,
                      color: colors.gold,
                    }}>
                    {routineCount}
                  </Text>
                  <Text
                    style={{
                      ...typography.bodyLg,
                      fontFamily: fonts.body,
                      color: colors.text.muted,
                    }}>
                    /{targetCount}
                  </Text>
                </>
              )}
            </TouchableOpacity>
          </SurfaceCard>
        </View>
      ) : null}

      <AppButton
        label="Doğrudan Gün 1'e geç"
        icon={ChevronRight}
        variant="secondary"
        onPress={onSkipDay0}
        style={{ marginBottom: spacing.md }}
      />

      <AppButton
        label={isDayComplete ? 'Başlangıcı tamamla' : 'Tüm başlangıç adımlarını tamamla'}
        icon={Sparkles}
        onPress={onCompleteDay}
        disabled={!isDayComplete}
      />
    </View>
  );
}
