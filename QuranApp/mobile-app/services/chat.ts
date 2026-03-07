/**
 * Chat Service — Multi-turn conversational therapy flow.
 * Supports conversation_id for state tracking.
 * Falls back to mock data when server is unreachable.
 */

import { api } from './api';

// --- Types ---
export interface ChatResponse {
    intent: 'CHAT' | 'PRESCRIPTION' | 'GATHERING' | 'GUARDRAIL' | 'READY' | 'PROPOSING' | 'CRISIS' | 'CRISIS_MODERATE' | 'UNKNOWN';
    response_text: string | null;
    prescription: PrescriptionData | null;
    conversation_id: string | null;
    phase: 'IDLE' | 'GATHERING' | 'PROPOSING' | 'READY' | 'GENERATED' | 'ONGOING' | null;
    gathering_progress: number | null;  // 0-100
    crisis_level?: 'immediate' | 'high' | 'moderate' | null;
    emergency_contacts?: Array<{ service: string; number: string }> | null;
    plan_id?: string | null;
    proposal_summary?: string | null;
}

export interface PrescriptionData {
    diagnosis: {
        emotional_state: string;
        root_cause: string;
        spiritual_needs: string[];
        search_keywords: string[];
    };
    esmas: Array<{
        name_tr: string;
        name_ar: string;
        meaning: string;
        reason: string;
    }>;
    duas: Array<{
        source: string;
        text_tr: string;
        context: string;
        tags: string[];
    }>;
    verses: Array<{
        verse_text_ar: string;
        verse_text_tr: string;
        explanation: string;
        surah_no: number;
        verse_no: number;
        verse_tr_name: string;
        source_type: string;
    }>;
    advice: string;
}

// --- Mock Data (Türkçe, konuşmalı akış) ---
const MOCK_GATHERING_RESPONSES = [
    'Seni duyuyorum. Bu durumun ne zamandır devam ettiğini merak ediyorum, biraz anlatır mısın?',
    'Anlıyorum, zor bir süreçten geçiyorsun. Peki bu durum günlük hayatını nasıl etkiliyor?',
    'Seni anlıyorum. Son olarak, manevi açıdan neler hissediyorsun? Dualarında ne istiyorsun?',
];

let mockTurnCount = 0;

const MOCK_PRESCRIPTION_RESPONSE: ChatResponse = {
    intent: 'PRESCRIPTION',
    response_text: 'Seninle konuşmamız ışığında, sana özel bir manevi rutin hazırladım.',
    prescription: {
        diagnosis: {
            emotional_state: 'Kaygı',
            root_cause: 'Belirsizlik ve kontrol kaybı hissi nedeniyle ortaya çıkan kaygı durumu.',
            spiritual_needs: ['Tevekkül', 'Sabır', 'Huzur'],
            search_keywords: ['kaygı', 'huzur', 'tevekkül'],
        },
        esmas: [],
        duas: [],
        verses: [
            {
                verse_text_ar: 'أَلَا بِذِكْرِ ٱللَّهِ تَطْمَئِنُّ ٱلْقُلُوبُ',
                verse_text_tr: 'Biliniz ki, kalpler ancak Allah\'ı anmakla huzur bulur.',
                explanation: 'Kalbin gerçek huzuru, maddi güvencelerde değil, ilahi bağlantıda aranmalıdır.',
                surah_no: 13,
                verse_no: 28,
                verse_tr_name: "Ra'd Suresi",
                source_type: 'MOCK',
            },
            {
                verse_text_ar: 'فَإِنَّ مَعَ ٱلْعُسْرِ يُسْرًا',
                verse_text_tr: 'Muhakkak ki zorlukla beraber bir kolaylık vardır.',
                explanation: 'Her sıkıntının ardından mutlaka bir ferahlık gelecektir.',
                surah_no: 94,
                verse_no: 5,
                verse_tr_name: 'İnşirah Suresi',
                source_type: 'MOCK',
            },
        ],
        advice: 'Bu rutin senin manevi durumuna özel hazırlanmıştır. Günde en az bir kere okumanı tavsiye ederiz.',
    },
    conversation_id: '00000000-0000-0000-0000-000000000001',
    phase: 'GENERATED',
    gathering_progress: 100,
};

/** Determine if message likely indicates emotional distress */
function isTherapyIntent(message: string): boolean {
    const keywords = [
        'daraldım', 'sıkıntı', 'kaygı', 'huzur', 'stres', 'üzgün', 'korku',
        'kötü', 'aram bozuk', 'bunaldım', 'ağlıyorum', 'mutsuz', 'yalnız',
        'umutsuz', 'kızgın', 'öfke', 'hüzün', 'dert', 'sorun',
    ];
    const lower = message.toLowerCase();
    return keywords.some(k => lower.includes(k));
}

// --- API Calls ---

/** Send a message with conversation tracking */
export async function sendMessage(
    message: string,
    conversationId?: string | null,
): Promise<ChatResponse> {
    try {
        const body: any = { message };
        if (conversationId) {
            body.conversation_id = conversationId;
        }
        return await api.post<ChatResponse>('/chat/send', body);
    } catch (error: any) {
        // Fallback to mock data
        const reason = error?.message || error?.status || 'unknown';
        console.log(`⚡ API failed (${reason}), using mock data`);
        return getMockResponse(message);
    }
}

/** Mock conversational flow — simulates gathering before prescription */
function getMockResponse(message: string): ChatResponse {
    if (!isTherapyIntent(message)) {
        // Normal chat
        mockTurnCount = 0;
        return {
            intent: 'CHAT',
            response_text: 'Seni dinliyorum. Nasıl hissediyorsun bugün?',
            prescription: null,
            conversation_id: '00000000-0000-0000-0000-000000000001',
            phase: 'IDLE',
            gathering_progress: 0,
        };
    }

    // Therapy needed — simulate gathering
    if (mockTurnCount < MOCK_GATHERING_RESPONSES.length) {
        const response = MOCK_GATHERING_RESPONSES[mockTurnCount];
        const progress = Math.min(((mockTurnCount + 1) / 3) * 100, 90);
        mockTurnCount++;
        return {
            intent: 'GATHERING',
            response_text: response,
            prescription: null,
            conversation_id: '00000000-0000-0000-0000-000000000001',
            phase: 'GATHERING',
            gathering_progress: Math.round(progress),
        };
    }

    // Enough turns — generate prescription
    mockTurnCount = 0;
    return { ...MOCK_PRESCRIPTION_RESPONSE };
}

/** Reset mock conversation state (for new chat) */
export function resetMockConversation() {
    mockTurnCount = 0;
}
