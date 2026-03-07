/**
 * Prescriptions Service — Generate, list, get prescription details.
 * Falls back to AsyncStorage when server is unreachable.
 */

import { api, isNetworkError } from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const LOCAL_PRESCRIPTIONS_KEY = 'saved_prescriptions';

// --- Types ---
export interface PrescriptionSummary {
    id: string;
    title: string | null;
    description: string | null;
    emotion_category: string | null;
    prescription_data: any | null;
    created_at: string | null;
    // Local-only fields (from chat screen saves)
    date?: string;
    items?: any[];
}

// --- API Calls ---

/** Generate a new prescription from user message */
export async function generatePrescription(
    message: string,
): Promise<PrescriptionSummary> {
    return api.post<PrescriptionSummary>('/prescriptions/generate', { message });
}

/** Get user's prescription history — API first, local fallback */
export async function getPrescriptionHistory(): Promise<PrescriptionSummary[]> {
    try {
        const apiData = await api.get<PrescriptionSummary[]>('/prescriptions/');
        return apiData;
    } catch (error) {
        if (isNetworkError(error)) {
            console.log('⚡ Server unreachable, loading prescriptions from local storage');
            return getLocalPrescriptions();
        }
        // For auth errors, still try local
        return getLocalPrescriptions();
    }
}

/** Get a single prescription by ID */
export async function getPrescription(
    id: string,
): Promise<PrescriptionSummary> {
    return api.get<PrescriptionSummary>(`/prescriptions/${id}`);
}

/** Get locally saved prescriptions (from chat screen) */
export async function getLocalPrescriptions(): Promise<PrescriptionSummary[]> {
    try {
        const data = await AsyncStorage.getItem(LOCAL_PRESCRIPTIONS_KEY);
        if (!data) return [];
        const items = JSON.parse(data);
        // Map local format to PrescriptionSummary
        return items.map((item: any) => ({
            id: item.id,
            title: item.title,
            description: item.description,
            emotion_category: null,
            prescription_data: null,
            created_at: item.date || null,
            date: item.date,
            items: item.items,
        }));
    } catch {
        return [];
    }
}
