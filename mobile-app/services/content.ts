import { api } from './api';

export interface ContentItem {
  id: number;
  source_type: string;
  content_text: string;
  explanation: string;
  metadata: Record<string, unknown>;
  score_hint: string;
}

export async function getContentSources(): Promise<string[]> {
  const response = await api.get<{ sources: string[] }>('/content/sources');
  return response.sources;
}

export async function searchContent(
  query: string,
  options?: {
    limit?: number;
    sourceTypes?: string[];
  }
): Promise<ContentItem[]> {
  const response = await api.post<{ results: ContentItem[] }>('/content/search', {
    query,
    limit: options?.limit ?? 6,
    source_types: options?.sourceTypes ?? ['quran'],
  });

  return response.results;
}
