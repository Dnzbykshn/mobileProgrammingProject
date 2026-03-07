import React, { useEffect, useMemo, useState } from 'react';
import {
    View,
    TextInput,
    TouchableOpacity,
    FlatList,
    KeyboardAvoidingView,
    Platform,
    Keyboard,
    KeyboardAvoidingViewProps,
    ActivityIndicator,
    Alert,
    Modal,
} from 'react-native';
import * as Linking from 'expo-linking';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import ScreenWrapper from '@/components/ScreenWrapper';
import {
    Send,
    Sparkles,
    Phone,
    AlertTriangle,
    MapPin,
    History,
    Plus,
    Trash2,
    X,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { saveActivePlanId } from '@/services/plans';
import { useRouter } from 'expo-router';
import {
    sendMessage as sendChatMessage,
    resetMockConversation,
    ChatResponse,
    PrescriptionData,
} from '@/services/chat';
import { colors } from '@/theme';
import { Heading, Body, Caption, Button, HeroCard, InfoCard } from '@/components/ui';

// Types
type PrescriptionItem = { type: string; text: string; count?: number };
type Prescription = {
    id: string; title: string; description: string;
    date: string; items: PrescriptionItem[];
};
type Message = {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    type?: 'text' | 'prescription' | 'gathering_progress' | 'crisis' | 'proposing';
    payload?: Prescription;
    rawPrescription?: PrescriptionData;
    progress?: number;
    isLoading?: boolean;
    crisisLevel?: 'immediate' | 'high' | 'moderate';
    emergencyContacts?: { service: string; number: string }[];
    proposalSummary?: string;
    planId?: string;
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

/** Map English emotional states to Turkish */
const EMOTION_TR: Record<string, string> = {
    'Anxiety': 'Kaygı', 'Depression': 'Hüzün', 'Anger': 'Öfke',
    'Fear': 'Korku', 'Loneliness': 'Yalnızlık', 'Grief': 'Yas',
    'Stress': 'Stres', 'Sadness': 'Üzüntü', 'Hopelessness': 'Umutsuzluk',
    'Guilt': 'Suçluluk', 'Shame': 'Utanç', 'Jealousy': 'Kıskançlık',
    'Confusion': 'Şaşkınlık', 'Overwhelm': 'Bunalmışlık',
};

/** Convert backend PrescriptionData → Prescription card */
function toPrescriptionCard(data: PrescriptionData): Prescription {
    const items: PrescriptionItem[] = [];
    (data.verses || []).forEach(v => {
        items.push({
            type: 'Ayet',
            text: `${v.verse_tr_name || ''} ${v.surah_no || 0}:${v.verse_no || 0} — ${(v.verse_text_tr || '').substring(0, 80)}...`,
        });
    });
    (data.esmas || []).forEach(e => {
        items.push({ type: 'Esma', text: `${e.name_tr} (${e.name_ar}) — ${e.meaning}` });
    });
    (data.duas || []).forEach(d => {
        items.push({ type: 'Dua', text: d.text_tr });
    });
    (data.diagnosis?.spiritual_needs || []).forEach(need => {
        items.push({ type: 'İhtiyaç', text: need });
    });

    const emotionTr = EMOTION_TR[data.diagnosis?.emotional_state] || data.diagnosis?.emotional_state || 'Genel';
    return {
        id: Date.now().toString(),
        date: new Date().toLocaleDateString('tr-TR'),
        title: `${emotionTr} Rutini`,
        description: data.advice || 'Senin için özel hazırlanmış manevi bir rutin.',
        items,
    };
}

function createWelcomeMessage(): Message {
    return {
        id: `welcome-${Date.now()}`,
        text: DEFAULT_GREETING,
        sender: 'bot',
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
        .find((msg) => msg.sender === 'user' && msg.text.trim().length > 0);

    if (!firstUserMessage) return 'Yeni Sohbet';
    return truncate(firstUserMessage.text.trim(), 36);
}

function deriveSessionPreview(sessionMessages: Message[]): string {
    const latest = sessionMessages.find((msg) => msg.text.trim().length > 0);
    if (!latest) return 'Henüz mesaj yok';
    return truncate(latest.text.trim(), 80);
}

function sortSessions(items: ChatSession[]): ChatSession[] {
    return [...items].sort((a, b) => {
        const aTs = new Date(a.updatedAt).getTime();
        const bTs = new Date(b.updatedAt).getTime();
        return bTs - aTs;
    });
}

function formatSessionTime(isoTime: string): string {
    const date = new Date(isoTime);
    if (Number.isNaN(date.getTime())) return 'Az önce';
    return date.toLocaleString('tr-TR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function normalizeStoredSessions(raw: unknown): ChatSession[] {
    if (!Array.isArray(raw)) return [];

    return raw
        .map((item) => {
            if (!item || typeof item !== 'object') return null;
            const asSession = item as Partial<ChatSession> & { messages?: unknown };

            if (typeof asSession.id !== 'string') return null;
            const rawMessages = Array.isArray(asSession.messages) ? asSession.messages : [];
            const normalizedMessages: Message[] = rawMessages
                .filter(
                    (msg): msg is Message =>
                        Boolean(msg) &&
                        typeof msg === 'object' &&
                        typeof (msg as Message).text === 'string' &&
                        ((msg as Message).sender === 'user' || (msg as Message).sender === 'bot')
                )
                .map((msg, index) => ({
                    ...msg,
                    id: typeof msg.id === 'string' ? msg.id : `${asSession.id}-${index}`,
                }));

            if (normalizedMessages.length === 0) {
                normalizedMessages.push(createWelcomeMessage());
            }

            return {
                id: asSession.id,
                title: typeof asSession.title === 'string' ? asSession.title : deriveSessionTitle(normalizedMessages),
                preview: typeof asSession.preview === 'string' ? asSession.preview : deriveSessionPreview(normalizedMessages),
                createdAt: typeof asSession.createdAt === 'string' ? asSession.createdAt : new Date().toISOString(),
                updatedAt: typeof asSession.updatedAt === 'string' ? asSession.updatedAt : new Date().toISOString(),
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

    // Conversation state
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [phase, setPhase] = useState<string>('IDLE');
    const [gatheringProgress, setGatheringProgress] = useState(0);

    // Keyboard behavior
    const defaultBehavior: KeyboardAvoidingViewProps["behavior"] = Platform.OS === "ios" ? "padding" : "height";
    const [behavior, setBehavior] = useState<KeyboardAvoidingViewProps["behavior"]>(defaultBehavior);

    useEffect(() => {
        const showListener = Keyboard.addListener(
            Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
            () => setBehavior(defaultBehavior)
        );
        const hideListener = Keyboard.addListener(
            Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
            () => setBehavior(undefined)
        );
        return () => { showListener.remove(); hideListener.remove(); };
    }, [defaultBehavior]);

    useEffect(() => {
        let cancelled = false;

        const hydrateSessions = async () => {
            try {
                const stored = await AsyncStorage.getItem(CHAT_HISTORY_KEY);
                const parsed = stored ? normalizeStoredSessions(JSON.parse(stored)) : [];
                const hydratedSessions =
                    parsed.length > 0
                        ? sortSessions(parsed).slice(0, MAX_SESSIONS)
                        : [createEmptySession()];

                if (cancelled) return;

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
        if (!isHydrated || !activeSessionId) return;

        const persistableMessages = messages
            .filter((msg) => !msg.isLoading)
            .slice(0, MAX_MESSAGES_PER_SESSION);

        if (persistableMessages.length === 0) return;

        const now = new Date().toISOString();

        setSessions((prev) => {
            const existing = prev.find((session) => session.id === activeSessionId);
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
                ...prev.filter((session) => session.id !== activeSessionId),
            ]).slice(0, MAX_SESSIONS);

            void saveSessionsToStorage(merged);
            return merged;
        });
    }, [activeSessionId, conversationId, gatheringProgress, isHydrated, messages, phase]);

    const activeSession = useMemo(
        () => sessions.find((session) => session.id === activeSessionId) || null,
        [sessions, activeSessionId]
    );

    const switchToSession = (session: ChatSession) => {
        resetMockConversation();
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
        Alert.alert(
            'Sohbet Silinsin mi?',
            'Bu sohbet geçmişi cihazdan kaldırılacak.',
            [
                { text: 'Vazgeç', style: 'cancel' },
                {
                    text: 'Sil',
                    style: 'destructive',
                    onPress: () => {
                        void performDeleteSession(sessionId);
                    },
                },
            ]
        );
    };

    const savePrescriptionToHistory = async (prescription: Prescription) => {
        try {
            const existing = await AsyncStorage.getItem('saved_prescriptions');
            const history = existing ? JSON.parse(existing) : [];
            if (!history.some((p: Prescription) => p.id === prescription.id)) {
                await AsyncStorage.setItem('saved_prescriptions', JSON.stringify([prescription, ...history]));
            }
        } catch (e) {
            console.error('Failed to save prescription', e);
        }
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
        if (!isHydrated || !messageText.trim() || isSending) return;
        const userText = messageText.trim();
        const userMsg: Message = { id: Date.now().toString(), text: userText, sender: 'user' };

        // Add user message + loading
        const loadingId = Date.now().toString() + '_loading';
        setMessages(prev => [
            { id: loadingId, text: 'Düşünüyorum...', sender: 'bot', isLoading: true },
            userMsg,
            ...prev,
        ]);
        setText('');
        setIsSending(true);

        try {
            const response: ChatResponse = await sendChatMessage(userText, conversationId);

            // Update conversation state
            if (response.conversation_id) setConversationId(response.conversation_id);
            if (response.phase) setPhase(response.phase);
            if (response.gathering_progress != null) setGatheringProgress(response.gathering_progress);

            // Remove loading
            setMessages(prev => prev.filter(m => m.id !== loadingId));

            if (response.intent === 'CRISIS' || response.intent === 'CRISIS_MODERATE') {
                // Crisis response — show emergency info
                setMessages(prev => [{
                    id: Date.now().toString() + 'crisis',
                    text: response.response_text || '',
                    sender: 'bot',
                    type: 'crisis',
                    crisisLevel: response.crisis_level || 'moderate',
                    emergencyContacts: response.emergency_contacts || [],
                }, ...prev.filter(m => m.id !== loadingId)]);

            } else if (response.intent === 'PROPOSING') {
                // Proposal card — user must accept to create plan
                setMessages(prev => [{
                    id: Date.now().toString() + 'propose',
                    text: response.response_text || '',
                    sender: 'bot',
                    type: 'proposing',
                    proposalSummary: response.proposal_summary || '',
                    progress: response.gathering_progress || 0,
                }, ...prev.filter(m => m.id !== loadingId)]);

            } else if (response.intent === 'PRESCRIPTION' && response.prescription) {
                // Plan created! Save and show card
                console.log('📦 PRESCRIPTION response received, plan_id:', response.plan_id);
                const card = toPrescriptionCard(response.prescription);
                await savePrescriptionToHistory(card);
                if (response.plan_id) {
                    await saveActivePlanId(response.plan_id);
                    console.log('💾 Plan ID saved:', response.plan_id);
                } else {
                    console.warn('⚠️ No plan_id in response — journey creation may have failed');
                }

                setMessages(prev => [{
                    id: Date.now().toString() + 'rx',
                    text: response.response_text || 'Senin için özel bir manevi yolculuk hazırladım.',
                    sender: 'bot',
                    type: 'prescription',
                    payload: card,
                    rawPrescription: response.prescription || undefined,
                    planId: response.plan_id || undefined,
                }, ...prev.filter(m => m.id !== loadingId)]);

            } else if (response.phase === 'GATHERING' || response.intent === 'GATHERING') {
                // Gathering phase — show progress + question
                setMessages(prev => [{
                    id: Date.now().toString() + 'gather',
                    text: response.response_text || 'Biraz daha anlatır mısın?',
                    sender: 'bot',
                    type: 'gathering_progress',
                    progress: response.gathering_progress || 0,
                }, ...prev.filter(m => m.id !== loadingId)]);

            } else {
                // Normal chat response
                setMessages(prev => [{
                    id: Date.now().toString() + 'bot',
                    text: response.response_text || 'Anladım. Başka nasıl yardımcı olabilirim?',
                    sender: 'bot',
                }, ...prev.filter(m => m.id !== loadingId)]);
            }
        } catch (error: any) {
            console.error('CHAT ERROR:', error);
            setMessages(prev => [{
                id: Date.now().toString() + 'err',
                text: `Hata: ${error?.message || 'Bilinmeyen bir hata oluştu.'}`,
                sender: 'bot',
            }, ...prev.filter(m => m.id !== loadingId)]);
        } finally {
            setIsSending(false);
        }
    };

    const handleSend = () => {
        if (!isHydrated) return;
        sendMessageDirect(text);
    };

    const renderItem = ({ item }: { item: Message }) => {
        // Loading
        if (item.isLoading) {
            return (
                <View style={{
                    alignSelf: 'flex-start',
                    marginBottom: 16,
                    maxWidth: '80%',
                    padding: 16,
                    borderRadius: 24,
                    backgroundColor: colors.teal.accent,
                    flexDirection: 'row',
                    alignItems: 'center'
                }}>
                    <ActivityIndicator size="small" color={colors.gold.primary} />
                    <Body size="md" color={colors.text.secondary} style={{ marginLeft: 12, fontStyle: 'italic' }}>{item.text}</Body>
                </View>
            );
        }

        // PROPOSING card — journey proposal with accept button
        if (item.type === 'proposing') {
            return (
                <HeroCard style={{
                    alignSelf: 'flex-start',
                    marginBottom: 16,
                    maxWidth: '90%',
                    borderWidth: 2,
                    borderColor: `${colors.gold.primary}66`,
                    shadowColor: colors.gold.primary,
                    shadowOpacity: 0.1,
                    shadowRadius: 8
                }}>
                    <View className="flex-row items-center mb-3">
                        <View style={{ backgroundColor: `${colors.gold.primary}33`, padding: 8, borderRadius: 12, marginRight: 12 }}>
                            <MapPin size={20} color={colors.gold.primary} />
                        </View>
                        <Caption size="sm" color={colors.gold.primary} style={{ fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1.5 }}>
                            Yolculuk Önerisi
                        </Caption>
                    </View>
                    <Body size="lg" color={colors.text.white} style={{ marginBottom: 12 }}>{item.text}</Body>
                    {item.proposalSummary ? (
                        <View style={{
                            backgroundColor: colors.teal.dark,
                            padding: 12,
                            borderRadius: 12,
                            marginBottom: 16,
                            borderWidth: 1,
                            borderColor: '#1F5550'
                        }}>
                            <Body size="md" color={colors.text.secondary} style={{ fontStyle: 'italic' }}>{item.proposalSummary}</Body>
                        </View>
                    ) : null}
                    <Button
                        variant="primary"
                        size="lg"
                        onPress={() => sendMessageDirect('Evet, başlayalım!')}
                        style={{ marginBottom: 8 }}
                    >
                        🤲 Yolculuğa Başla
                    </Button>
                    <TouchableOpacity
                        onPress={() => sendMessageDirect('Biraz daha konuşalım')}
                        style={{ paddingVertical: 8, alignItems: 'center' }}
                    >
                        <Body size="md" color={colors.text.muted}>Konuşmaya devam et</Body>
                    </TouchableOpacity>
                </HeroCard>
            );
        }

        // Prescription card — now navigates to plan
        if (item.type === 'prescription' && item.payload) {
            return (
                <InfoCard style={{
                    alignSelf: 'flex-start',
                    marginBottom: 16,
                    maxWidth: '85%',
                    borderColor: colors.gold.primary
                }}>
                    <View className="flex-row items-center mb-2">
                        <Sparkles size={16} color={colors.gold.primary} />
                        <Caption size="md" color={colors.gold.primary} style={{ fontWeight: '700', marginLeft: 8 }}>MANEVİ YOLCULUK</Caption>
                    </View>
                    <Heading size="md" color={colors.text.white} style={{ marginBottom: 4 }}>{item.payload.title}</Heading>
                    <Body size="md" color={colors.text.secondary} style={{ marginBottom: 12 }}>{item.payload.description}</Body>

                    <View style={{ backgroundColor: colors.teal.dark, padding: 12, borderRadius: 12, marginBottom: 16 }}>
                        {item.payload.items.slice(0, 3).map((pi, idx) => (
                            <Body key={idx} size="md" color={colors.text.white} style={{ marginBottom: 4 }}>• {pi.text}</Body>
                        ))}
                        {item.payload.items.length > 3 && (
                            <Caption size="sm" color={colors.text.muted} style={{ marginTop: 4 }}>ve daha fazlası...</Caption>
                        )}
                    </View>

                    <Button
                        variant="primary"
                        size="lg"
                        onPress={() => {
                            if (item.planId) {
                                router.push({
                                    pathname: '/action/plan',
                                    params: { planId: item.planId },
                                });
                            } else {
                                Alert.alert('Yolculuk Hazırlanıyor', 'Plan henüz oluşturulamadı. Lütfen tekrar deneyin.');
                            }
                        }}
                    >
                        Yolculuğa Git 🕌
                    </Button>

                    <Caption size="sm" color={colors.text.white} style={{ marginTop: 8, fontStyle: 'italic' }}>{item.text}</Caption>
                </InfoCard>
            );
        }

        // Gathering progress message
        if (item.type === 'gathering_progress') {
            const progress = item.progress || 0;
            return (
                <View style={{ alignSelf: 'flex-start', marginBottom: 16, maxWidth: '85%' }}>
                    {/* Progress bar */}
                    <View style={{ backgroundColor: colors.teal.dark, borderRadius: 9999, height: 8, marginBottom: 8, overflow: 'hidden' }}>
                        <View
                            style={{ width: `${progress}%`, backgroundColor: colors.gold.primary, height: '100%', borderRadius: 9999 }}
                        />
                    </View>
                    <Caption size="sm" color={colors.text.secondary} style={{ marginBottom: 8 }}>
                        Rutin hazırlığı: %{progress}
                    </Caption>

                    {/* Bot message */}
                    <View style={{ padding: 16, borderRadius: 24, backgroundColor: colors.teal.accent }}>
                        <Body size="md" color={colors.text.white}>{item.text}</Body>
                    </View>
                </View>
            );
        }

        // Crisis message
        if (item.type === 'crisis') {
            const isImmediate = item.crisisLevel === 'immediate';
            return (
                <View style={{
                    alignSelf: 'flex-start',
                    marginBottom: 16,
                    maxWidth: '90%',
                    padding: 16,
                    borderRadius: 24,
                    backgroundColor: isImmediate ? '#4A1C1C' : colors.teal.accent,
                    borderWidth: isImmediate ? 2 : 1,
                    borderColor: isImmediate ? '#FF6B6B' : colors.gold.primary
                }}>
                    <View className="flex-row items-center mb-2">
                        <AlertTriangle size={18} color={isImmediate ? colors.status.error : colors.gold.primary} />
                        <Body size="md" color={isImmediate ? '#FCA5A5' : colors.gold.primary} style={{ fontWeight: '700', marginLeft: 8 }}>
                            {isImmediate ? '⚠️ ACİL YARDIM' : '💚 Destek'}
                        </Body>
                    </View>
                    <Body size="md" color={colors.text.white} style={{ marginBottom: 12 }}>{item.text}</Body>
                    {(item.emergencyContacts || []).map((contact, idx) => (
                        <TouchableOpacity
                            key={idx}
                            onPress={() => Linking.openURL(`tel:${contact.number}`)}
                            style={{
                                backgroundColor: colors.teal.dark,
                                padding: 12,
                                borderRadius: 12,
                                marginBottom: 8,
                                flexDirection: 'row',
                                alignItems: 'center'
                            }}
                        >
                            <Phone size={16} color={colors.gold.primary} />
                            <Body size="md" color={colors.text.white} style={{ marginLeft: 8, fontWeight: '500' }}>{contact.service}</Body>
                            <Body size="md" color={colors.gold.primary} style={{ marginLeft: 'auto', fontWeight: '700' }}>{contact.number}</Body>
                        </TouchableOpacity>
                    ))}
                </View>
            );
        }

        // Normal message
        return (
            <View style={{
                marginBottom: 16,
                maxWidth: '80%',
                padding: 16,
                borderRadius: 24,
                alignSelf: item.sender === 'user' ? 'flex-end' : 'flex-start',
                backgroundColor: item.sender === 'user' ? colors.gold.primary : colors.teal.accent
            }}>
                <Body size="md" color={item.sender === 'user' ? colors.teal.dark : colors.text.white} style={{ fontWeight: item.sender === 'user' ? '700' : '400' }}>
                    {item.text}
                </Body>
            </View>
        );
    };

    // Phase indicator text
    const getPhaseText = () => {
        if (phase === 'GATHERING') return `Seni dinliyorum... %${gatheringProgress}`;
        if (phase === 'PROPOSING') return '🤲 Yolculuk önerisi hazır';
        if (phase === 'GENERATED') return '✨ Yolculuğun hazır';
        if (phase === 'ONGOING') return '💬 Yolculuk aktif, sohbete devam edebilirsin';
        return '';
    };

    if (!isHydrated) {
        return (
            <ScreenWrapper>
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                    <ActivityIndicator size="large" color={colors.gold.primary} />
                    <Caption size="md" color={colors.text.secondary} style={{ marginTop: 12 }}>
                        Sohbet geçmişi yükleniyor...
                    </Caption>
                </View>
            </ScreenWrapper>
        );
    }

    return (
        <ScreenWrapper>
            {/* Header */}
            <View style={{
                padding: 16,
                borderBottomWidth: 1,
                borderBottomColor: `${colors.teal.accent}4D`,
                backgroundColor: `${colors.teal.dark}4D`
            }}>
                <View className="flex-row items-center justify-between">
                    <View style={{ flex: 1, paddingRight: 12 }}>
                        <Heading size="md" color={colors.gold.primary}>Manevi Sohbet</Heading>
                        <Caption size="sm" color={colors.text.secondary} numberOfLines={1} style={{ marginTop: 2 }}>
                            {activeSession?.title || 'Yeni Sohbet'}
                        </Caption>
                    </View>

                    <View className="flex-row items-center">
                        <TouchableOpacity
                            onPress={() => setHistoryVisible(true)}
                            style={{
                                flexDirection: 'row',
                                alignItems: 'center',
                                borderWidth: 1,
                                borderColor: `${colors.teal.accent}99`,
                                paddingHorizontal: 10,
                                paddingVertical: 8,
                                borderRadius: 9999,
                                marginRight: 8,
                                backgroundColor: `${colors.teal.accent}55`,
                            }}
                        >
                            <History size={15} color={colors.text.white} />
                            <Caption size="md" color={colors.text.white} style={{ marginLeft: 6 }}>
                                Geçmiş ({sessions.length})
                            </Caption>
                        </TouchableOpacity>

                        <TouchableOpacity
                            onPress={() => { void handleNewChat(); }}
                            style={{
                                flexDirection: 'row',
                                alignItems: 'center',
                                borderWidth: 1,
                                borderColor: `${colors.gold.primary}99`,
                                paddingHorizontal: 10,
                                paddingVertical: 8,
                                borderRadius: 9999,
                                backgroundColor: `${colors.gold.primary}22`,
                            }}
                        >
                            <Plus size={15} color={colors.gold.primary} />
                            <Caption size="md" color={colors.gold.primary} style={{ marginLeft: 6 }}>
                                Yeni
                            </Caption>
                        </TouchableOpacity>
                    </View>
                </View>
                {phase !== 'IDLE' && (
                    <Caption size="sm" color={colors.text.secondary} style={{ marginTop: 4 }}>{getPhaseText()}</Caption>
                )}
            </View>

            <Modal
                visible={historyVisible}
                transparent
                animationType="fade"
                onRequestClose={() => setHistoryVisible(false)}
            >
                <View style={{ flex: 1, backgroundColor: 'rgba(5, 24, 26, 0.72)' }}>
                    <TouchableOpacity
                        style={{ flex: 1 }}
                        activeOpacity={1}
                        onPress={() => setHistoryVisible(false)}
                    />

                    <View
                        style={{
                            maxHeight: '76%',
                            backgroundColor: colors.teal.dark,
                            borderTopLeftRadius: 24,
                            borderTopRightRadius: 24,
                            borderTopWidth: 1,
                            borderColor: `${colors.teal.accent}AA`,
                            paddingTop: 14,
                        }}
                    >
                        <View
                            style={{
                                flexDirection: 'row',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                paddingHorizontal: 16,
                                paddingBottom: 10,
                                borderBottomWidth: 1,
                                borderBottomColor: `${colors.teal.accent}66`,
                            }}
                        >
                            <Heading size="sm" color={colors.gold.primary}>Sohbet Geçmişi</Heading>
                            <TouchableOpacity onPress={() => setHistoryVisible(false)} style={{ padding: 8 }}>
                                <X size={18} color={colors.text.secondary} />
                            </TouchableOpacity>
                        </View>

                        <FlatList
                            data={sessions}
                            keyExtractor={(item) => item.id}
                            contentContainerStyle={{
                                paddingHorizontal: 12,
                                paddingTop: 12,
                                paddingBottom: insets.bottom + 16,
                            }}
                            ListEmptyComponent={
                                <View style={{ padding: 16, alignItems: 'center' }}>
                                    <Caption size="md" color={colors.text.secondary}>
                                        Henüz kayıtlı sohbet yok.
                                    </Caption>
                                </View>
                            }
                            renderItem={({ item }) => {
                                const isActive = item.id === activeSessionId;
                                return (
                                    <View
                                        style={{
                                            flexDirection: 'row',
                                            alignItems: 'center',
                                            borderWidth: 1,
                                            borderColor: isActive
                                                ? `${colors.gold.primary}88`
                                                : `${colors.teal.accent}88`,
                                            backgroundColor: isActive
                                                ? `${colors.gold.primary}1A`
                                                : `${colors.teal.accent}44`,
                                            borderRadius: 16,
                                            marginBottom: 10,
                                            overflow: 'hidden',
                                        }}
                                    >
                                        <TouchableOpacity
                                            onPress={() => handleOpenSession(item)}
                                            style={{ flex: 1, padding: 12 }}
                                        >
                                            <Body
                                                size="md"
                                                color={isActive ? colors.gold.primary : colors.text.white}
                                                style={{ fontWeight: '700', marginBottom: 2 }}
                                                numberOfLines={1}
                                            >
                                                {item.title}
                                            </Body>
                                            <Caption
                                                size="md"
                                                color={colors.text.secondary}
                                                style={{ marginBottom: 6 }}
                                                numberOfLines={2}
                                            >
                                                {item.preview}
                                            </Caption>
                                            <Caption size="sm" color={colors.text.muted}>
                                                {formatSessionTime(item.updatedAt)}
                                            </Caption>
                                        </TouchableOpacity>

                                        <TouchableOpacity
                                            onPress={() => handleDeleteSession(item.id)}
                                            style={{ paddingHorizontal: 12, paddingVertical: 16 }}
                                        >
                                            <Trash2 size={16} color={colors.status.error} />
                                        </TouchableOpacity>
                                    </View>
                                );
                            }}
                        />
                    </View>
                </View>
            </Modal>

            <KeyboardAvoidingView
                behavior={behavior}
                style={{ flex: 1 }}
                keyboardVerticalOffset={0}
            >
                <FlatList
                    data={messages}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    inverted
                    contentContainerStyle={{ padding: 16 }}
                    keyboardDismissMode="interactive"
                />

                {/* Input */}
                <View style={{
                    backgroundColor: colors.teal.dark,
                    padding: 10,
                    paddingBottom: Platform.OS === 'ios' ? insets.bottom + 40 : 100,
                    borderTopWidth: 1,
                    borderTopColor: colors.teal.accent
                }}>
                    <View className="flex-row items-center">
                        <TextInput
                            style={{
                                flex: 1,
                                backgroundColor: colors.teal.accent,
                                color: colors.text.white,
                                padding: 16,
                                borderRadius: 9999,
                                marginRight: 8,
                                maxHeight: 100
                            }}
                            placeholder="Mesaj yaz..."
                            placeholderTextColor={colors.text.secondary}
                            value={text}
                            onChangeText={setText}
                            onSubmitEditing={handleSend}
                            editable={!isSending && isHydrated}
                        />
                        <TouchableOpacity
                            onPress={handleSend}
                            disabled={isSending || !isHydrated}
                            style={{
                                padding: 16,
                                borderRadius: 9999,
                                backgroundColor: isSending || !isHydrated
                                    ? colors.text.secondary
                                    : colors.gold.primary
                            }}
                        >
                            {isSending
                                ? <ActivityIndicator size="small" color={colors.teal.dark} />
                                : <Send color={colors.teal.dark} size={24} />
                            }
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </ScreenWrapper>
    );
}
