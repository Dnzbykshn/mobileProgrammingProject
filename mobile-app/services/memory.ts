/**
 * Memory API Service
 * Handles all memory-related API calls including CRUD operations,
 * semantic search, and privacy management.
 */
import { api } from './api';

export interface Memory {
  id: string;
  user_id: string;
  memory_type:
    | 'emotional_state'
    | 'life_event'
    | 'spiritual_preference'
    | 'goal'
    | 'progress_milestone'
    | 'behavioral_pattern';
  content: string;
  context: Record<string, any>;
  importance_score: number;
  access_count: number;
  created_at: string;
  expires_at: string | null;
  is_sensitive: boolean;
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
}

export interface MemorySearchRequest {
  search_query: string;
  limit?: number;
}

export interface PrivacyReport {
  total_memories: number;
  by_type: Record<string, number>;
  oldest_memory: string | null;
  storage_size_kb: number;
}

export interface MemoryCreateRequest {
  memory_type: string;
  content: string;
  context?: Record<string, any>;
  importance_score?: number;
  conversation_id?: string;
}

/**
 * Get all memories for the current user
 * @param memoryType - Optional filter by memory type
 * @param limit - Max results to return
 * @param offset - Number of results to skip (pagination)
 */
export async function getMemories(
  memoryType?: string,
  limit: number = 20,
  offset: number = 0
): Promise<MemoryListResponse> {
  const params = new URLSearchParams();
  if (memoryType) params.append('memory_type', memoryType);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return await api.get<MemoryListResponse>(`/memories/memories?${params.toString()}`);
}

/**
 * Semantic search across user's memories
 * @param searchQuery - Natural language search query
 * @param limit - Max results to return
 */
export async function searchMemories(
  searchQuery: string,
  limit: number = 5
): Promise<MemoryListResponse> {
  return await api.post<MemoryListResponse>('/memories/memories/search', {
    search_query: searchQuery,
    limit,
  });
}

/**
 * Create a new memory (manual creation)
 * Note: Memories are also auto-extracted from conversations
 */
export async function createMemory(data: MemoryCreateRequest): Promise<Memory> {
  return await api.post<Memory>('/memories/memories', data);
}

/**
 * Delete a memory (soft delete)
 * @param memoryId - UUID of the memory to delete
 */
export async function deleteMemory(memoryId: string): Promise<void> {
  await api.delete(`/memories/memories/${memoryId}`);
}

/**
 * Get privacy report showing memory statistics
 */
export async function getPrivacyReport(): Promise<PrivacyReport> {
  return await api.get<PrivacyReport>('/memories/memories/privacy-report');
}

/**
 * Memory type display configurations
 */
export const MEMORY_TYPE_CONFIG = {
  emotional_state: {
    icon: '💭' as const,
    label: 'Duygusal Durum',
  },
  life_event: {
    icon: '📍' as const,
    label: 'Yaşam Olayı',
  },
  spiritual_preference: {
    icon: '✨' as const,
    label: 'Manevi Tercih',
  },
  goal: {
    icon: '🎯' as const,
    label: 'Hedef',
  },
  progress_milestone: {
    icon: '🏆' as const,
    label: 'Başarı',
  },
  behavioral_pattern: {
    icon: '⏰' as const,
    label: 'Alışkanlık',
  },
} as const;

/**
 * Format time ago (e.g., "2 gün önce", "3 hafta önce")
 */
export function formatTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Bugün';
  if (diffDays === 1) return 'Dün';
  if (diffDays < 7) return `${diffDays} gün önce`;
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} hafta önce`;
  }
  const months = Math.floor(diffDays / 30);
  return `${months} ay önce`;
}
