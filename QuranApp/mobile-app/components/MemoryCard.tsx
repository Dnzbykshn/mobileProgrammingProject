/**
 * MemoryCard Component
 * Displays a single memory with swipe-to-delete functionality
 */
import React, { useRef } from 'react';
import { View, Text, Animated, PanResponder, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Memory, MEMORY_TYPE_CONFIG, formatTimeAgo } from '@/services/memory';

interface MemoryCardProps {
  memory: Memory;
  onDelete: (memoryId: string) => void;
}

export default function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  const pan = useRef(new Animated.ValueXY()).current;
  const opacity = useRef(new Animated.Value(1)).current;

  const config = MEMORY_TYPE_CONFIG[memory.memory_type] || MEMORY_TYPE_CONFIG.emotional_state;

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gestureState) => {
        // Only respond to horizontal swipes
        return Math.abs(gestureState.dx) > 10;
      },
      onPanResponderMove: (_, gestureState) => {
        // Only allow left swipes (negative dx)
        if (gestureState.dx < 0) {
          pan.setValue({ x: gestureState.dx, y: 0 });
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dx < -120) {
          // Swipe threshold reached - confirm delete
          Alert.alert(
            'Anıyı Sil',
            'Bu anıyı silmek istediğinizden emin misiniz?',
            [
              {
                text: 'İptal',
                style: 'cancel',
                onPress: () => {
                  // Return to original position
                  Animated.spring(pan, {
                    toValue: { x: 0, y: 0 },
                    useNativeDriver: true,
                  }).start();
                },
              },
              {
                text: 'Sil',
                style: 'destructive',
                onPress: () => {
                  // Fade out animation
                  Animated.parallel([
                    Animated.timing(opacity, {
                      toValue: 0,
                      duration: 300,
                      useNativeDriver: true,
                    }),
                    Animated.timing(pan.x, {
                      toValue: -400,
                      duration: 300,
                      useNativeDriver: true,
                    }),
                  ]).start(() => {
                    onDelete(memory.id);
                  });
                },
              },
            ]
          );
        } else {
          // Return to original position
          Animated.spring(pan, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;

  return (
    <View className="mb-3 relative">
      {/* Delete background (visible when swiped) */}
      <View
        className="absolute right-0 top-0 bottom-0 bg-red-600/20 rounded-xl flex-row items-center justify-end px-6"
        style={{ width: 120 }}
      >
        <Ionicons name="trash-outline" size={24} color="#EF4444" />
      </View>

      {/* Memory card */}
      <Animated.View
        {...panResponder.panHandlers}
        style={{
          transform: [{ translateX: pan.x }],
          opacity,
        }}
        className="rounded-xl p-4"
        style={{
          backgroundColor: config.bgColor,
          borderLeftWidth: 4,
          borderLeftColor: config.color,
        }}
      >
        {/* Header: Type icon + label + time */}
        <View className="flex-row items-center justify-between mb-2">
          <View className="flex-row items-center">
            <Text className="text-2xl mr-2">{config.icon}</Text>
            <Text style={{ color: config.color }} className="font-semibold text-sm">
              {config.label}
            </Text>
          </View>

          <View className="flex-row items-center">
            {memory.is_sensitive && (
              <Ionicons
                name="alert-circle"
                size={16}
                color="#F59E0B"
                style={{ marginRight: 8 }}
              />
            )}
            <Text className="text-white/50 text-xs">
              {formatTimeAgo(memory.created_at)}
            </Text>
          </View>
        </View>

        {/* Content */}
        <Text className="text-white text-base leading-6">
          {memory.content}
        </Text>

        {/* Footer: Importance + Access count */}
        <View className="flex-row items-center justify-between mt-3 pt-3 border-t border-white/10">
          <View className="flex-row items-center">
            <Ionicons name="star" size={14} color="#C0A060" />
            <Text className="text-white/60 text-xs ml-1">
              Önem: {memory.importance_score}/100
            </Text>
          </View>

          <View className="flex-row items-center">
            <Ionicons name="eye-outline" size={14} color="#5A7F82" />
            <Text className="text-white/60 text-xs ml-1">
              {memory.access_count} kez görüntülendi
            </Text>
          </View>
        </View>

        {/* Context (if available) */}
        {memory.context && Object.keys(memory.context).length > 0 && (
          <View className="mt-2 pt-2 border-t border-white/10">
            <Text className="text-white/40 text-xs">
              {Object.entries(memory.context).map(([key, value]) => (
                `${key}: ${value}`
              )).join(' • ')}
            </Text>
          </View>
        )}
      </Animated.View>
    </View>
  );
}
