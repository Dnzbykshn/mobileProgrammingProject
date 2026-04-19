import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as Linking from 'expo-linking';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import {
  AlertTriangle,
  ChevronRight,
  History,
  MapPin,
  Phone,
  Plus,
  Send,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react-native';

import ScreenWrapper from '@/components/ScreenWrapper';
import AppButton from '@/components/app/AppButton';
import AppChip from '@/components/app/AppChip';
import { sendMessage as sendChatMessage, ChatResponse } from '@/services/chat';
import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  type?: 'text' | 'gathering_progress' | 'crisis' | 'proposing' | 'pathway_ready';
  progress?: number;
  isLoading?: boolean;
  crisisLevel?: 'immediate' | 'high' | 'moderate';
  emergencyContacts?: { service: string; number: string }[];
  proposalSummary?: string;
  pathwayId?: string;
  sources?: string[];
};

type ChatSession = {
  id: string;
  title: string;
  preview: string;
  createdAt: string;
  updatedAt: string;
  conversationId: string | null;
  phase: string;
  gatheringProgress: number;
  messages: Message[];
};

const CHAT_HISTORY_KEY = 'chat_sessions_v1';
const MAX_SESSIONS = 20;
const MAX_MESSAGES_PER_SESSION = 80;
const DEFAULT_GREETING = 'Selamun Aleyküm, nasıl hissediyorsun bugün?';

const QUICK_SUGGESTIONS = [
  'Bugün zihnim çok dağınık.',
  'İçimi rahatlatacak bir ayet arıyorum.',
  'Uyku öncesi kısa bir rutin önerir misin?',
  'Son günlerde kaygım arttı.',
] as const;

function createWelcomeMessage(): Message {
  return {
    id: `welcome-${Date.now()}`,
    text: DEFAULT_GREETING,
    sender: 'bot',
    type: 'text',
  };
}

function createEmptySession(): ChatSession {
  const now = new Date().toISOString();
  const welcome = createWelcomeMessage();

  return {
    id: `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: 'Yeni Sohbet',
    preview: welcome.text,
    createdAt: now,
    updatedAt: now,
    conversationId: null,
    phase: 'IDLE',
    gatheringProgress: 0,
    messages: [welcome],
  };
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trim()}...`;
}

function deriveSessionTitle(sessionMessages: Message[]): string {
  const firstUserMessage = [...sessionMessages]
    .reverse()
    .find((message) => message.sender === 'user' && message.text.trim().length > 0);

  if (!firstUserMessage) {
    return 'Yeni Sohbet';
  }

  return truncate(firstUserMessage.text.trim(), 36);
}

function deriveSessionPreview(sessionMessages: Message[]): string {
  const latest = sessionMessages.find((message) => message.text.trim().length > 0);
  if (!latest) {
    return 'Henüz mesaj yok';
  }
  return truncate(latest.text.trim(), 80);
}

function sortSessions(items: ChatSession[]): ChatSession[] {
  return [...items].sort((a, b) => {
    const aTimestamp = new Date(a.updatedAt).getTime();
    const bTimestamp = new Date(b.updatedAt).getTime();
    return bTimestamp - aTimestamp;
  });
}

function formatSessionTime(isoTime: string): string {
  const date = new Date(isoTime);
  if (Number.isNaN(date.getTime())) {
    return 'Az önce';
  }

  return date.toLocaleString('tr-TR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

type ChatHistorySheetProps = {
  visible: boolean;
  sessions: ChatSession[];
  activeSessionId: string | null;
  bottomInset: number;
  onClose: () => void;
  onCreateChat: () => void;
  onOpenSession: (session: ChatSession) => void;
  onDeleteSession: (sessionId: string) => void;
};

function ChatHistorySheet({
  visible,
  sessions,
  activeSessionId,
  bottomInset,
  onClose,
  onCreateChat,
  onOpenSession,
  onDeleteSession,
}: ChatHistorySheetProps) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={{ flex: 1, backgroundColor: colors.overlay.scrim }}>
        <TouchableOpacity style={{ flex: 1 }} activeOpacity={1} onPress={onClose} />

        <View
          style={{
            maxHeight: '80%',
            backgroundColor: colors.surface.nightSoft,
            borderTopLeftRadius: radius.xxl,
            borderTopRightRadius: radius.xxl,
            borderTopWidth: 1,
            borderColor: colors.border.strong,
            paddingTop: spacing.sm,
            ...shadows.lg,
          }}>
          <View style={{ alignItems: 'center', paddingBottom: spacing.sm }}>
            <View
              style={{
                width: 42,
                height: 5,
                borderRadius: radius.full,
                backgroundColor: colors.surface.nightRaised,
              }}
            />
          </View>

          <View
            style={{
              flexDirection: 'row',
              alignItems: 'flex-start',
              paddingHorizontal: spacing.lg,
              paddingBottom: spacing.md,
            }}>
            <View style={{ flex: 1, paddingRight: spacing.md }}>
              <Text
                style={{
                  ...typography.h2,
                  fontFamily: fonts.heading,
                  color: colors.text.primary,
                }}>
                Sohbet geçmişi
              </Text>

              <Text
                style={{
                  ...typography.bodySm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                  marginTop: spacing.xs + 2,
                }}>
                {sessions.length === 1
                  ? '1 sohbet bu cihazda saklanıyor.'
                  : `${sessions.length} sohbet bu cihazda saklanıyor.`}
              </Text>
            </View>

            <TouchableOpacity
              onPress={onClose}
              activeOpacity={0.85}
              style={{
                width: 36,
                height: 36,
                borderRadius: radius.full,
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: colors.surface.raised,
                borderWidth: 1,
                borderColor: colors.border.soft,
              }}>
              <X size={17} color={colors.text.primary} />
            </TouchableOpacity>
          </View>

          <View style={{ paddingHorizontal: spacing.lg, paddingBottom: spacing.md }}>
            <TouchableOpacity
              onPress={onCreateChat}
              activeOpacity={0.9}
              style={{
                minHeight: 50,
                borderRadius: radius.xl,
                borderWidth: 1,
                borderColor: colors.border.gold,
                backgroundColor: colors.surface.goldSoft,
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <Plus size={17} color={colors.text.primary} />
              <Text
                style={{
                  ...typography.labelLg,
                  fontFamily: fonts.bodyMd,
                  color: colors.text.primary,
                  marginLeft: spacing.sm,
                }}>
                Yeni sohbet
              </Text>
            </TouchableOpacity>
          </View>

          <FlatList
            data={sessions}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{
              paddingHorizontal: spacing.lg,
              paddingBottom: bottomInset + spacing.lg,
            }}
            ListEmptyComponent={
              <View
                style={{
                  paddingVertical: spacing.lg,
                  paddingHorizontal: spacing.lg,
                  borderRadius: radius.xl,
                  backgroundColor: colors.surface.raised,
                  borderWidth: 1,
                  borderColor: colors.border.soft,
                }}>
                <Text
                  style={{
                    ...typography.bodyMd,
                    fontFamily: fonts.body,
                    color: colors.text.secondary,
                  }}>
                  Henüz kayıtlı sohbet yok.
                </Text>
              </View>
            }
            renderItem={({ item }) => {
              const isActive = item.id === activeSessionId;

              return (
                <View
                  style={{
                    flexDirection: 'row',
                    alignItems: 'stretch',
                    marginBottom: spacing.md,
                  }}>
                  <TouchableOpacity
                    onPress={() => onOpenSession(item)}
                    activeOpacity={0.9}
                    style={{ flex: 1, marginRight: spacing.sm + 2 }}>
                    <View
                      style={{
                        borderRadius: radius.xl,
                        paddingHorizontal: spacing.lg,
                        paddingVertical: spacing.md + 3,
                        backgroundColor: isActive
                          ? colors.surface.goldSoft
                          : colors.surface.raised,
                        borderWidth: 1,
                        borderColor: isActive ? colors.border.gold : colors.border.soft,
                      }}>
                      <View
                        style={{
                          flexDirection: 'row',
                          alignItems: 'center',
                          marginBottom: spacing.sm,
                        }}>
                        <View
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: radius.full,
                            marginRight: spacing.sm,
                            backgroundColor: isActive ? colors.gold : colors.surface.nightRaised,
                          }}
                        />

                        <Text
                          numberOfLines={1}
                          style={{
                            flex: 1,
                            ...typography.labelLg,
                            fontFamily: fonts.bodyMd,
                            color: colors.text.primary,
                          }}>
                          {item.title}
                        </Text>

                        <Text
                          style={{
                            ...typography.labelMd,
                            fontFamily: fonts.body,
                            color: colors.text.secondary,
                            marginLeft: spacing.sm,
                          }}>
                          {formatSessionTime(item.updatedAt)}
                        </Text>
                      </View>

                      <Text
                        numberOfLines={2}
                        style={{
                          ...typography.bodySm,
                          fontFamily: fonts.body,
                          color: colors.text.secondary,
                        }}>
                        {item.preview}
                      </Text>

                      <View
                        style={{
                          flexDirection: 'row',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginTop: spacing.md,
                        }}>
                        <View
                          style={{
                            paddingHorizontal: spacing.sm + 2,
                            paddingVertical: spacing.xs + 1,
                            borderRadius: radius.full,
                            backgroundColor: isActive
                              ? colors.surface.goldMuted
                              : colors.surface.nightSoft,
                          }}>
                          <Text
                            style={{
                              ...typography.labelMd,
                              fontFamily: fonts.bodyMd,
                              color: colors.text.primary,
                            }}>
                            {isActive ? 'Açık sohbet' : 'Aç'}
                          </Text>
                        </View>

                        <ChevronRight size={16} color={colors.text.secondary} />
                      </View>
                    </View>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => onDeleteSession(item.id)}
                    activeOpacity={0.85}
                    style={{
                      width: 48,
                      borderRadius: radius.lg,
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: colors.surface.dangerSoft,
                      borderWidth: 1,
                      borderColor: colors.border.danger,
                    }}>
                    <Trash2 size={16} color={colors.status.error} />
                  </TouchableOpacity>
                </View>
              );
            }}
          />
        </View>
      </View>
    </Modal>
  );
}

function normalizeStoredSessions(raw: unknown): ChatSession[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null;
      }

      const asSession = item as Partial<ChatSession> & { messages?: unknown };
      if (typeof asSession.id !== 'string') {
        return null;
      }

      const rawMessages = Array.isArray(asSession.messages) ? asSession.messages : [];
      const normalizedMessages: Message[] = rawMessages
        .filter(
          (message): message is Message =>
            Boolean(message) &&
            typeof message === 'object' &&
            typeof (message as Message).text === 'string' &&
            ((message as Message).sender === 'user' || (message as Message).sender === 'bot')
        )
        .map((message, index) => ({
          ...message,
          id: typeof message.id === 'string' ? message.id : `${asSession.id}-${index}`,
        }));

      if (normalizedMessages.length === 0) {
        normalizedMessages.push(createWelcomeMessage());
      }

      return {
        id: asSession.id,
        title:
          typeof asSession.title === 'string'
            ? asSession.title
            : deriveSessionTitle(normalizedMessages),
        preview:
          typeof asSession.preview === 'string'
            ? asSession.preview
            : deriveSessionPreview(normalizedMessages),
        createdAt:
          typeof asSession.createdAt === 'string' ? asSession.createdAt : new Date().toISOString(),
        updatedAt:
          typeof asSession.updatedAt === 'string' ? asSession.updatedAt : new Date().toISOString(),
        conversationId:
          typeof asSession.conversationId === 'string' ? asSession.conversationId : null,
        phase: typeof asSession.phase === 'string' ? asSession.phase : 'IDLE',
        gatheringProgress:
          typeof asSession.gatheringProgress === 'number' ? asSession.gatheringProgress : 0,
        messages: normalizedMessages.slice(0, MAX_MESSAGES_PER_SESSION),
      } as ChatSession;
    })
    .filter((session): session is ChatSession => session !== null)
    .slice(0, MAX_SESSIONS);
}

async function saveSessionsToStorage(nextSessions: ChatSession[]): Promise<void> {
  try {
    await AsyncStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(nextSessions));
  } catch (error) {
    console.error('Failed to persist chat sessions:', error);
  }
}

export default function ChatScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([createWelcomeMessage()]);
  const [text, setText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [phase, setPhase] = useState<string>('IDLE');
  const [gatheringProgress, setGatheringProgress] = useState(0);

  const canSend = useMemo(
    () => isHydrated && !isSending && text.trim().length > 0,
    [isHydrated, isSending, text]
  );

  useEffect(() => {
    const showListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      () => {
        setIsKeyboardVisible(true);
      }
    );

    const hideListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setIsKeyboardVisible(false);
      }
    );

    return () => {
      showListener.remove();
      hideListener.remove();
    };
  }, []);

  const tabBarOffset = Math.max(insets.bottom, spacing.sm) + 68;

  useEffect(() => {
    let cancelled = false;

    const hydrateSessions = async () => {
      try {
        const stored = await AsyncStorage.getItem(CHAT_HISTORY_KEY);
        const parsed = stored ? normalizeStoredSessions(JSON.parse(stored)) : [];
        const hydratedSessions =
          parsed.length > 0 ? sortSessions(parsed).slice(0, MAX_SESSIONS) : [createEmptySession()];

        if (cancelled) {
          return;
        }

        const initial = hydratedSessions[0];
        setSessions(hydratedSessions);
        setActiveSessionId(initial.id);
        setMessages(initial.messages.length > 0 ? initial.messages : [createWelcomeMessage()]);
        setConversationId(initial.conversationId);
        setPhase(initial.phase || 'IDLE');
        setGatheringProgress(initial.gatheringProgress || 0);

        if (!stored || parsed.length === 0) {
          await saveSessionsToStorage(hydratedSessions);
        }
      } catch (error) {
        console.error('Failed to hydrate chat sessions:', error);
        if (!cancelled) {
          const fallback = createEmptySession();
          setSessions([fallback]);
          setActiveSessionId(fallback.id);
          setMessages(fallback.messages);
          setConversationId(null);
          setPhase('IDLE');
          setGatheringProgress(0);
          await saveSessionsToStorage([fallback]);
        }
      } finally {
        if (!cancelled) {
          setIsHydrated(true);
        }
      }
    };

    void hydrateSessions();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isHydrated || !activeSessionId) {
      return;
    }

    const persistableMessages = messages
      .filter((message) => !message.isLoading)
      .slice(0, MAX_MESSAGES_PER_SESSION);

    if (persistableMessages.length === 0) {
      return;
    }

    const now = new Date().toISOString();

    setSessions((previous) => {
      const existing = previous.find((session) => session.id === activeSessionId);
      const updatedSession: ChatSession = {
        id: activeSessionId,
        title: deriveSessionTitle(persistableMessages),
        preview: deriveSessionPreview(persistableMessages),
        createdAt: existing?.createdAt || now,
        updatedAt: now,
        conversationId,
        phase,
        gatheringProgress,
        messages: persistableMessages,
      };

      const merged = sortSessions([
        updatedSession,
        ...previous.filter((session) => session.id !== activeSessionId),
      ]).slice(0, MAX_SESSIONS);

      void saveSessionsToStorage(merged);
      return merged;
    });
  }, [activeSessionId, conversationId, gatheringProgress, isHydrated, messages, phase]);

  const switchToSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    setMessages(session.messages.length > 0 ? session.messages : [createWelcomeMessage()]);
    setConversationId(session.conversationId || null);
    setPhase(session.phase || 'IDLE');
    setGatheringProgress(session.gatheringProgress || 0);
  };

  const handleOpenSession = (session: ChatSession) => {
    switchToSession(session);
    setHistoryVisible(false);
  };

  const performDeleteSession = async (sessionId: string) => {
    const remaining = sessions.filter((session) => session.id !== sessionId);

    if (remaining.length === 0) {
      const fallback = createEmptySession();
      setSessions([fallback]);
      switchToSession(fallback);
      await saveSessionsToStorage([fallback]);
      return;
    }

    const next = sortSessions(remaining).slice(0, MAX_SESSIONS);
    setSessions(next);
    await saveSessionsToStorage(next);

    if (activeSessionId === sessionId) {
      switchToSession(next[0]);
    }
  };

  const handleDeleteSession = (sessionId: string) => {
    Alert.alert('Sohbet silinsin mi?', 'Bu sohbet geçmişi cihazdan kaldırılacak.', [
      { text: 'Vazgeç', style: 'cancel' },
      {
        text: 'Sil',
        style: 'destructive',
        onPress: () => {
          void performDeleteSession(sessionId);
        },
      },
    ]);
  };

  const handleNewChat = async () => {
    const nextSession = createEmptySession();
    const nextSessions = sortSessions([nextSession, ...sessions]).slice(0, MAX_SESSIONS);
    setSessions(nextSessions);
    switchToSession(nextSession);
    setHistoryVisible(false);
    await saveSessionsToStorage(nextSessions);
  };

  const sendMessageDirect = async (messageText: string) => {
    if (!isHydrated || !messageText.trim() || isSending) {
      return;
    }

    const userText = messageText.trim();
    const userMessage: Message = {
      id: Date.now().toString(),
      text: userText,
      sender: 'user',
      type: 'text',
    };

    const loadingId = `${Date.now()}_loading`;

    setMessages((previous) => [
      { id: loadingId, text: 'Düşünüyorum...', sender: 'bot', isLoading: true },
      userMessage,
      ...previous,
    ]);

    setText('');
    setIsSending(true);

    const buildBotMessage = (overrides: Partial<Message>, sources: string[] = []): Message => ({
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      sender: 'bot',
      type: 'text',
      text: 'Anladım. Başka nasıl yardımcı olabilirim?',
      sources,
      ...overrides,
    });

    try {
      const response: ChatResponse = await sendChatMessage(userText, conversationId);

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }
      if (response.phase) {
        setPhase(response.phase);
      }
      if (response.gathering_progress != null) {
        setGatheringProgress(response.gathering_progress);
      }

      const responseSources = Array.isArray((response as { sources?: unknown }).sources)
        ? ((response as { sources?: unknown }).sources as unknown[])
            .filter((source): source is string => typeof source === 'string')
            .slice(0, 4)
        : [];

      setMessages((previous) => {
        const withoutLoading = previous.filter((message) => message.id !== loadingId);

        if (response.intent === 'CRISIS' || response.intent === 'CRISIS_MODERATE') {
          return [
            buildBotMessage(
              {
                text: response.response_text || '',
                type: 'crisis',
                crisisLevel: response.crisis_level || 'moderate',
                emergencyContacts: response.emergency_contacts || [],
              },
              responseSources
            ),
            ...withoutLoading,
          ];
        }

        if (response.intent === 'PROPOSING') {
          return [
            buildBotMessage(
              {
                text: response.response_text || '',
                type: 'proposing',
                proposalSummary: response.proposal_summary || '',
                progress: response.gathering_progress || 0,
              },
              responseSources
            ),
            ...withoutLoading,
          ];
        }

        if (response.pathway_action === 'created' || response.pathway_action === 'updated') {
          return [
            buildBotMessage(
              {
                text: response.response_text || 'Yolun hazır.',
                type: 'pathway_ready',
                pathwayId: response.pathway_id || undefined,
              },
              responseSources
            ),
            ...withoutLoading,
          ];
        }

        if (response.phase === 'GATHERING' || response.intent === 'GATHERING') {
          return [
            buildBotMessage(
              {
                text: response.response_text || 'Biraz daha anlatır mısın?',
                type: 'gathering_progress',
                progress: response.gathering_progress || 0,
              },
              responseSources
            ),
            ...withoutLoading,
          ];
        }

        return [
          buildBotMessage(
            {
              text: response.response_text || 'Anladım. Başka nasıl yardımcı olabilirim?',
              type: 'text',
            },
            responseSources
          ),
          ...withoutLoading,
        ];
      });
    } catch (error) {
      const fallbackMessage =
        error &&
        typeof error === 'object' &&
        'message' in error &&
        typeof error.message === 'string'
          ? error.message
          : 'Bilinmeyen bir hata oluştu.';

      setMessages((previous) => [
        {
          id: `${Date.now()}_error`,
          text: `Hata: ${fallbackMessage}`,
          sender: 'bot',
          type: 'text',
        },
        ...previous.filter((message) => message.id !== loadingId),
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSend = () => {
    if (!canSend) {
      return;
    }
    void sendMessageDirect(text);
  };

  const getPhaseText = () => {
    if (phase === 'GATHERING') return `Seni dinliyorum · %${gatheringProgress}`;
    if (phase === 'PROPOSING') return 'Yol önerisi hazır';
    if (phase === 'GENERATED') return 'Yolun hazır';
    if (phase === 'ONGOING') return 'Yol aktif';
    return '';
  };

  const renderSources = (sources?: string[]) => {
    if (!sources || sources.length === 0) {
      return null;
    }

    return (
      <View
        style={{
          marginTop: spacing.md,
          paddingLeft: spacing.sm + 2,
          borderLeftWidth: 3,
          borderLeftColor: colors.gold,
          gap: spacing.xs,
        }}>
        <Text
          style={{
            ...typography.labelSm,
            fontFamily: fonts.bodySm,
            color: colors.gold,
            textTransform: 'uppercase',
            letterSpacing: 0.8,
          }}>
          Kaynaklar
        </Text>

        {sources.map((source) => (
          <Text
            key={source}
            style={{
              ...typography.bodySm,
              fontFamily: fonts.body,
              color: colors.text.muted,
            }}>
            {source}
          </Text>
        ))}
      </View>
    );
  };

  const renderItem = ({ item }: { item: Message }) => {
    if (item.isLoading) {
      return (
        <View
          style={{
            alignSelf: 'flex-start',
            marginBottom: spacing.md,
            maxWidth: '86%',
            paddingHorizontal: spacing.lg,
            paddingVertical: spacing.md,
            borderRadius: radius.xl,
            backgroundColor: colors.surface.raised,
            borderWidth: 1,
            borderColor: colors.border.soft,
            flexDirection: 'row',
            alignItems: 'center',
            ...shadows.sm,
          }}>
          <ActivityIndicator size="small" color={colors.gold} />
          <Text
            style={{
              marginLeft: spacing.sm + 2,
              ...typography.bodyMd,
              fontFamily: fonts.body,
              color: colors.text.secondary,
            }}>
            {item.text}
          </Text>
        </View>
      );
    }

    if (item.type === 'proposing') {
      return (
        <View
          style={{
            alignSelf: 'flex-start',
            marginBottom: spacing.md,
            maxWidth: '92%',
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.gold,
            backgroundColor: colors.surface.raised,
            padding: spacing.lg,
          }}>
          <View
            style={{ marginBottom: spacing.sm + 2, flexDirection: 'row', alignItems: 'center' }}>
            <View
              style={{
                backgroundColor: colors.surface.goldSoft,
                padding: spacing.sm,
                borderRadius: radius.md,
                marginRight: spacing.sm + 2,
              }}>
              <MapPin size={18} color={colors.text.primary} />
            </View>

            <Text
              style={{
                ...typography.labelMd,
                fontFamily: fonts.bodySm,
                color: colors.gold,
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}>
              Yol önerisi
            </Text>
          </View>

          <Text
            style={{
              ...typography.bodyLg,
              fontFamily: fonts.body,
              color: colors.text.primary,
              marginBottom: spacing.sm + 2,
            }}>
            {item.text}
          </Text>

          {item.proposalSummary ? (
            <View
              style={{
                backgroundColor: colors.surface.nightSoft,
                padding: spacing.md,
                borderRadius: radius.md,
                marginBottom: spacing.lg,
                borderWidth: 1,
                borderColor: colors.border.soft,
              }}>
              <Text
                style={{
                  ...typography.bodyMd,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                }}>
                {item.proposalSummary}
              </Text>
            </View>
          ) : null}

          {renderSources(item.sources)}

          <AppButton
            label="Yolu başlat"
            onPress={() => {
              void sendMessageDirect('Evet, başlayalım!');
            }}
            style={{ marginTop: spacing.lg, marginBottom: spacing.sm }}
          />

          <TouchableOpacity
            onPress={() => {
              void sendMessageDirect('Biraz daha konuşalım.');
            }}
            style={{ paddingVertical: spacing.sm, alignItems: 'center' }}>
            <Text
              style={{
                ...typography.bodyMd,
                fontFamily: fonts.body,
                color: colors.text.secondary,
              }}>
              Konuşmaya devam et
            </Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (item.type === 'pathway_ready') {
      return (
        <View
          style={{
            alignSelf: 'flex-start',
            marginBottom: spacing.md,
            maxWidth: '90%',
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.gold,
            backgroundColor: colors.surface.raised,
            padding: spacing.lg,
          }}>
          <View style={{ marginBottom: spacing.sm, flexDirection: 'row', alignItems: 'center' }}>
            <Sparkles size={16} color={colors.gold} />
            <Text
              style={{
                ...typography.labelMd,
                fontFamily: fonts.bodySm,
                color: colors.gold,
                marginLeft: spacing.sm,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}>
              Manevi yol
            </Text>
          </View>

          <Text
            style={{
              ...typography.bodyLg,
              fontFamily: fonts.body,
              color: colors.text.primary,
              marginBottom: spacing.lg,
            }}>
            {item.text}
          </Text>

          {renderSources(item.sources)}

          {item.pathwayId ? (
            <AppButton
              label="Yolu aç"
              onPress={() =>
                router.push({
                  pathname: '/action/pathway',
                  params: { pathwayId: item.pathwayId },
                })
              }
              style={{ marginTop: spacing.lg }}
            />
          ) : null}
        </View>
      );
    }

    if (item.type === 'gathering_progress') {
      const progress = item.progress || 0;

      return (
        <View style={{ alignSelf: 'flex-start', marginBottom: spacing.md, maxWidth: '90%' }}>
          <View
            style={{
              backgroundColor: colors.surface.nightSoft,
              borderRadius: radius.full,
              height: 8,
              marginBottom: spacing.sm,
              overflow: 'hidden',
              borderWidth: 1,
              borderColor: colors.border.soft,
            }}>
            <View
              style={{
                width: `${progress}%`,
                backgroundColor: colors.gold,
                height: '100%',
                borderRadius: radius.full,
              }}
            />
          </View>

          <Text
            style={{
              ...typography.labelMd,
              fontFamily: fonts.body,
              color: colors.text.secondary,
              marginBottom: spacing.sm,
            }}>
            Rutin hazırlığı · %{progress}
          </Text>

          <View
            style={{
              padding: spacing.lg,
              borderRadius: radius.xl,
              backgroundColor: colors.surface.raised,
              borderWidth: 1,
              borderColor: colors.border.soft,
            }}>
            <Text style={{ ...typography.bodyMd, fontFamily: fonts.body, color: colors.text.primary }}>
              {item.text}
            </Text>
            {renderSources(item.sources)}
          </View>
        </View>
      );
    }

    if (item.type === 'crisis') {
      const isImmediate = item.crisisLevel === 'immediate';

      return (
        <View
          style={{
            alignSelf: 'flex-start',
            marginBottom: spacing.md,
            maxWidth: '92%',
            padding: spacing.lg,
            borderRadius: radius.xl,
            backgroundColor: isImmediate ? colors.surface.dangerSoft : colors.surface.raised,
            borderWidth: 1,
            borderColor: isImmediate ? colors.border.danger : colors.border.gold,
          }}>
          <View style={{ marginBottom: spacing.sm, flexDirection: 'row', alignItems: 'center' }}>
            <AlertTriangle size={18} color={isImmediate ? colors.status.error : colors.gold} />
            <Text
              style={{
                ...typography.labelLg,
                fontFamily: fonts.bodyMd,
                color: isImmediate ? colors.text.danger : colors.gold,
                marginLeft: spacing.sm,
              }}>
              {isImmediate ? 'Acil yardım' : 'Destek'}
            </Text>
          </View>

          <Text
            style={{
              ...typography.bodyMd,
              fontFamily: fonts.body,
              color: colors.text.primary,
              marginBottom: spacing.md,
            }}>
            {item.text}
          </Text>

          {(item.emergencyContacts || []).map((contact) => (
            <TouchableOpacity
              key={`${contact.service}-${contact.number}`}
              onPress={() => {
                void Linking.openURL(`tel:${contact.number}`);
              }}
              style={{
                backgroundColor: colors.surface.nightSoft,
                padding: spacing.md,
                borderRadius: radius.md,
                marginBottom: spacing.sm,
                flexDirection: 'row',
                alignItems: 'center',
                borderWidth: 1,
                borderColor: colors.border.soft,
              }}>
              <Phone size={16} color={colors.gold} />
              <Text
                style={{
                  marginLeft: spacing.sm,
                  ...typography.bodyMd,
                  fontFamily: fonts.bodyMd,
                  color: colors.text.primary,
                }}>
                {contact.service}
              </Text>
              <Text
                style={{
                  marginLeft: 'auto',
                  ...typography.labelLg,
                  fontFamily: fonts.bodySm,
                  color: colors.gold,
                }}>
                {contact.number}
              </Text>
            </TouchableOpacity>
          ))}

          {renderSources(item.sources)}
        </View>
      );
    }

    const isUser = item.sender === 'user';

    return (
      <View
        style={{
          marginBottom: spacing.md,
          maxWidth: '86%',
          paddingHorizontal: spacing.lg,
          paddingVertical: spacing.md,
          borderRadius: radius.xl,
          alignSelf: isUser ? 'flex-end' : 'flex-start',
          backgroundColor: isUser ? colors.night : colors.surface.raised,
          borderWidth: 1,
          borderColor: isUser ? colors.border.night : colors.border.soft,
          ...(isUser ? shadows.md : shadows.sm),
        }}>
        <Text
          style={{
            ...typography.bodyMd,
            fontFamily: fonts.body,
            color: colors.text.primary,
          }}>
          {item.text}
        </Text>

        {!isUser ? renderSources(item.sources) : null}
      </View>
    );
  };

  if (!isHydrated) {
    return (
      <ScreenWrapper withDecoration={false}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={colors.gold} />
          <Text
            style={{
              ...typography.bodyMd,
              fontFamily: fonts.body,
              color: colors.text.secondary,
              marginTop: spacing.sm + 2,
            }}>
            Sohbet geçmişi yükleniyor...
          </Text>
        </View>
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper withDecoration={false}>
      <View style={{ flex: 1, paddingHorizontal: spacing.md, paddingTop: spacing.xs }}>
        <View
          style={{
            paddingBottom: spacing.xs,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
          <TouchableOpacity
            onPress={() => setHistoryVisible(true)}
            activeOpacity={0.85}
            style={{
              width: 34,
              height: 34,
              borderRadius: radius.full,
              alignItems: 'center',
              justifyContent: 'center',
              borderWidth: 1,
              borderColor: colors.border.soft,
              backgroundColor: colors.surface.raised,
            }}>
            <History size={15} color={colors.text.secondary} />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => {
              void handleNewChat();
            }}
            activeOpacity={0.85}
            style={{
              width: 34,
              height: 34,
              borderRadius: radius.full,
              alignItems: 'center',
              justifyContent: 'center',
              borderWidth: 1,
              borderColor: colors.border.gold,
              backgroundColor: colors.surface.goldSoft,
            }}>
            <Plus size={15} color={colors.text.primary} />
          </TouchableOpacity>
        </View>

        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={{ flex: 1 }}
          keyboardVerticalOffset={0}>
          <FlatList
            data={messages}
            renderItem={renderItem}
            keyExtractor={(item) => item.id}
            inverted
            contentContainerStyle={{
              paddingTop: spacing.md,
              paddingBottom: spacing.md,
            }}
            keyboardDismissMode="none"
            keyboardShouldPersistTaps="always"
          />

          {phase !== 'IDLE' ? (
            <View
              style={{
                marginBottom: spacing.xs,
                paddingHorizontal: spacing.sm + 2,
                paddingVertical: spacing.xs + 1,
                borderRadius: radius.md,
                borderWidth: 1,
                borderColor: colors.border.soft,
                backgroundColor: colors.surface.raised,
                flexDirection: 'row',
                alignItems: 'center',
              }}>
              <MapPin size={12} color={colors.gold} />
              <Text
                numberOfLines={1}
                style={{
                  flex: 1,
                  ...typography.labelSm,
                  fontFamily: fonts.body,
                  color: colors.text.secondary,
                  marginLeft: spacing.xs + 2,
                }}>
                {getPhaseText()}
              </Text>
            </View>
          ) : null}

          <View
            style={{
              borderTopWidth: 1,
              borderTopColor: colors.border.soft,
              paddingTop: spacing.xs,
              paddingBottom: Math.max(insets.bottom, spacing.xs),
              marginBottom: isKeyboardVisible ? 0 : tabBarOffset,
              backgroundColor: colors.surface.base,
            }}>
            {!isKeyboardVisible && text.trim().length === 0 ? (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                keyboardShouldPersistTaps="always"
                contentContainerStyle={{
                  gap: spacing.xs,
                  paddingBottom: spacing.xs,
                  paddingRight: spacing.xs,
                }}>
                {QUICK_SUGGESTIONS.map((suggestion) => (
                  <AppChip
                    key={suggestion}
                    label={suggestion}
                    onPress={() => {
                      void sendMessageDirect(suggestion);
                    }}
                  />
                ))}
              </ScrollView>
            ) : null}

            <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: spacing.xs }}>
              <View
                style={{
                  flex: 1,
                  minHeight: 44,
                  borderRadius: radius.md,
                  borderWidth: 1,
                  borderColor: colors.border.soft,
                  backgroundColor: colors.surface.nightSoft,
                  paddingHorizontal: spacing.md,
                  alignItems: 'flex-start',
                }}>
                <TextInput
                  value={text}
                  onChangeText={setText}
                  placeholder="Mesajını yaz..."
                  placeholderTextColor={colors.text.muted}
                  multiline
                  editable={isHydrated}
                  selectionColor={colors.gold}
                  cursorColor={colors.gold}
                  keyboardAppearance="dark"
                  underlineColorAndroid="transparent"
                  textAlignVertical="top"
                  style={{
                    width: '100%',
                    minHeight: 52,
                    maxHeight: 110,
                    ...typography.bodyMd,
                    fontFamily: fonts.body,
                    color: colors.text.primary,
                    paddingVertical: spacing.sm,
                  }}
                />
              </View>

              <TouchableOpacity
                onPress={handleSend}
                disabled={!canSend}
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: radius.full,
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: canSend ? colors.gold : colors.surface.nightRaised,
                  borderWidth: 1,
                  borderColor: canSend ? colors.border.gold : colors.border.soft,
                  marginBottom: 2,
                }}>
                {isSending ? (
                  <ActivityIndicator size="small" color={colors.text.onGold} />
                ) : (
                  <Send color={canSend ? colors.text.onGold : colors.text.muted} size={18} />
                )}
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>

      <ChatHistorySheet
        visible={historyVisible}
        sessions={sessions}
        activeSessionId={activeSessionId}
        bottomInset={insets.bottom}
        onClose={() => setHistoryVisible(false)}
        onCreateChat={() => {
          void handleNewChat();
        }}
        onOpenSession={handleOpenSession}
        onDeleteSession={handleDeleteSession}
      />
    </ScreenWrapper>
  );
}
