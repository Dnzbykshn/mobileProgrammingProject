import React from 'react';
import { Alert, Text, TouchableOpacity, View } from 'react-native';
import { ShieldAlert, Trash2 } from 'lucide-react-native';

import SurfaceCard from '@/components/app/SurfaceCard';
import { Memory, MEMORY_TYPE_CONFIG, formatTimeAgo } from '@/services/memory';
import { colors, fonts, spacing, typography } from '@/theme';

interface MemoryCardProps {
  memory: Memory;
  onDelete: (memoryId: string) => void;
}

export default function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  const config = MEMORY_TYPE_CONFIG[memory.memory_type] || MEMORY_TYPE_CONFIG.emotional_state;

  return (
    <SurfaceCard compact>
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: spacing.md,
        }}>
        <View
          style={{ flexDirection: 'row', alignItems: 'center', flex: 1, marginRight: spacing.md }}>
          <View style={{ flex: 1 }}>
            <Text
              style={{
                ...typography.labelSm,
                fontFamily: fonts.bodySm,
                color: colors.gold,
                letterSpacing: 0.8,
                textTransform: 'uppercase',
              }}>
              {config.label}
            </Text>
            <Text
              style={{
                ...typography.bodySm,
                fontFamily: fonts.body,
                color: colors.text.muted,
                marginTop: spacing.xs - 1,
              }}>
              {formatTimeAgo(memory.created_at)}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          onPress={() =>
            Alert.alert('Anıyı sil', 'Bu anıyı silmek istediğine emin misin?', [
              { text: 'İptal', style: 'cancel' },
              { text: 'Sil', style: 'destructive', onPress: () => onDelete(memory.id) },
            ])
          }
          hitSlop={10}>
          <Trash2 size={16} color={colors.status.error} />
        </TouchableOpacity>
      </View>

      <Text
        style={{
          ...typography.bodyLg,
          fontFamily: fonts.body,
          color: colors.text.primary,
        }}>
        {memory.content}
      </Text>

      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          marginTop: spacing.md + 2,
          gap: spacing.md,
        }}>
        <Text style={{ ...typography.bodySm, fontFamily: fonts.body, color: colors.text.muted }}>
          Önem {memory.importance_score}/100
        </Text>
        <Text style={{ ...typography.bodySm, fontFamily: fonts.body, color: colors.text.muted }}>
          {memory.access_count} görüntüleme
        </Text>

        {memory.is_sensitive ? (
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ShieldAlert size={12} color={colors.gold} />
            <Text
              style={{
                ...typography.bodySm,
                fontFamily: fonts.body,
                color: colors.gold,
                marginLeft: spacing.xs,
              }}>
              Hassas
            </Text>
          </View>
        ) : null}
      </View>

      {memory.context && Object.keys(memory.context).length > 0 ? (
        <Text
          style={{
            ...typography.bodySm,
            fontFamily: fonts.body,
            color: colors.text.muted,
            marginTop: spacing.md,
          }}>
          {Object.entries(memory.context)
            .map(([key, value]) => `${key}: ${value}`)
            .join(' · ')}
        </Text>
      ) : null}
    </SurfaceCard>
  );
}
