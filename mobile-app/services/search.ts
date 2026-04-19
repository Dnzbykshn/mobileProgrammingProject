import { searchContent, type ContentItem } from './content';

export interface QuranSearchResult {
  content_text: string;
  explanation: string;
  metadata: {
    surah_no?: number;
    verse_no?: number;
    surah_name?: string;
    arabic_text?: string;
    [key: string]: unknown;
  };
}

export async function searchQuran(query: string): Promise<QuranSearchResult[]> {
  const results = await searchContent(query, {
    limit: 6,
    sourceTypes: ['quran'],
  });

  return results.map((item: ContentItem) => ({
    content_text: item.content_text,
    explanation: item.explanation,
    metadata: item.metadata,
  }));
}
