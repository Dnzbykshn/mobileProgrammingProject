/**
 * Plans Service — Create, view, and complete 7-day plans.
 */

import { api } from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

// --- Types ---
export interface PlanTask {
    id: string;
    day_number: number;
    task_type: 'morning' | 'evening' | 'journal' | 'day0_verse' | 'day0_dua' | 'day0_esma' | 'day0_routine';
    title: string;
    description: string | null;
    duration_minutes: number | null;
    order_index: number;
    is_completed: boolean;
    completed_at: string | null;
    task_metadata: Record<string, any> | null;
}

export interface DayGroup {
    day_number: number;
    tasks: PlanTask[];
    is_complete: boolean;
    is_day0: boolean;
    is_skippable: boolean;
}

export interface Plan {
    id: string;
    journey_title: string;
    journey_type: string;
    total_days: number;
    current_day: number;
    status: 'active' | 'completed' | 'paused';
    started_at: string | null;
    days: DayGroup[];
    topic_summary: string | null;
    day0_skipped: boolean;
}

export interface JourneySummary {
    plan_id: string;
    title: string;
    journey_type: string;
    topic_summary: string | null;
    current_day: number;
    total_days: number;
    status: string;
    today_completed: number;
    today_total: number;
    started_at: string | null;
}

export interface TaskCompleteResponse {
    task_id: string;
    is_completed: boolean;
    completed_at: string | null;
}

export interface DayCompleteResponse {
    plan_id: string;
    current_day: number;
    status: string;
    message: string;
}

// --- API Calls ---

/** Create a new 7-day plan */
export async function createPlan(
    journeyType: string = 'anxiety_management',
    prescriptionId?: string,
    userInput?: string,
): Promise<Plan> {
    return api.post<Plan>('/plans/create', {
        journey_type: journeyType,
        prescription_id: prescriptionId,
        user_input: userInput,
    });
}

/** Get plan with all tasks grouped by day */
export async function getPlan(planId: string): Promise<Plan> {
    return api.get<Plan>(`/plans/${planId}`);
}

/** Toggle task completion */
export async function toggleTask(
    planId: string,
    taskId: string,
): Promise<TaskCompleteResponse> {
    return api.put<TaskCompleteResponse>(
        `/plans/${planId}/tasks/${taskId}/complete`,
    );
}

/** Complete a day and unlock the next */
export async function completeDay(
    planId: string,
    dayNumber: number,
    reflection?: string,
): Promise<DayCompleteResponse> {
    return api.post<DayCompleteResponse>(
        `/plans/${planId}/days/${dayNumber}/complete`,
        { reflection },
    );
}

/** Skip Day 0 and jump to Day 1 */
export async function skipDay0(planId: string): Promise<{ plan_id: string; current_day: number; message: string }> {
    return api.post(`/plans/${planId}/days/0/skip`);
}

/** Get all active journeys for the current user */
export async function getActiveJourneys(): Promise<JourneySummary[]> {
    return api.get<JourneySummary[]>('/plans/active');
}

export const ACTIVE_PLAN_KEY = 'active_plan_id';

/** Save the ID of the most recently created plan */
export async function saveActivePlanId(planId: string): Promise<void> {
    await AsyncStorage.setItem(ACTIVE_PLAN_KEY, planId);
}

/** Get the locally saved active plan ID */
export async function getActivePlanId(): Promise<string | null> {
    return AsyncStorage.getItem(ACTIVE_PLAN_KEY);
}
