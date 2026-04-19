/**
 * Chat Service — Multi-turn conversational therapy flow.
 * Uses backend conversation state only.
 */

import { api } from './api';

export interface ChatResponse {
  intent:
    | 'CHAT'
    | 'GATHERING'
    | 'GUARDRAIL'
    | 'READY'
    | 'PROPOSING'
    | 'CRISIS'
    | 'CRISIS_MODERATE'
    | 'UNKNOWN';
  response_text: string | null;
  conversation_id: string | null;
  phase: 'IDLE' | 'GATHERING' | 'PROPOSING' | 'READY' | 'GENERATED' | 'ONGOING' | null;
  gathering_progress: number | null;
  crisis_level?: 'immediate' | 'high' | 'moderate' | null;
  emergency_contacts?: { service: string; number: string }[] | null;
  pathway_id?: string | null;
  pathway_action?: 'created' | 'updated' | 'failed' | 'authentication_required' | null;
  proposal_summary?: string | null;
}

export async function sendMessage(
  message: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  const body: { message: string; conversation_id?: string } = { message };
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  return api.post<ChatResponse>('/chat/send', body);
}
