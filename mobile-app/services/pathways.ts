import { api } from './api';

export type PathwayTaskType =
  | 'morning'
  | 'evening'
  | 'reflection'
  | 'journal'
  | 'day0_intro'
  | 'day0_reflection'
  | 'day0_verse'
  | 'day0_dua'
  | 'day0_esma'
  | 'day0_routine';

export interface PathwayTask {
  id: string;
  day_number: number;
  task_type: PathwayTaskType;
  title: string;
  description: string | null;
  duration_minutes: number | null;
  order_index: number;
  is_completed: boolean;
  completed_at: string | null;
  task_metadata: Record<string, any> | null;
}

export interface PathwayDay {
  day_number: number;
  tasks: PathwayTask[];
  is_complete: boolean;
  is_day0: boolean;
  is_skippable: boolean;
}

export interface Pathway {
  id: string;
  title: string;
  pathway_type: string;
  total_days: number;
  current_day: number;
  status: 'active' | 'completed' | 'paused';
  started_at: string | null;
  days: PathwayDay[];
  topic_summary: string | null;
  day0_skipped: boolean;
}

export interface PathwaySummary {
  pathway_id: string;
  title: string;
  pathway_type: string;
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
  pathway_id: string;
  current_day: number;
  status: string;
  message: string;
}

export async function createPathway(
  pathwayType: string = 'anxiety_management',
  userInput?: string
): Promise<Pathway> {
  return api.post<Pathway>('/pathways/create', {
    pathway_type: pathwayType,
    user_input: userInput,
  });
}

export async function getPathway(pathwayId: string): Promise<Pathway> {
  return api.get<Pathway>(`/pathways/${pathwayId}`);
}

export async function togglePathwayTask(
  pathwayId: string,
  taskId: string
): Promise<TaskCompleteResponse> {
  return api.put<TaskCompleteResponse>(`/pathways/${pathwayId}/tasks/${taskId}/complete`);
}

export async function completePathwayDay(
  pathwayId: string,
  dayNumber: number
): Promise<DayCompleteResponse> {
  return api.post<DayCompleteResponse>(`/pathways/${pathwayId}/days/${dayNumber}/complete`, {});
}

export async function skipPathwayDay0(
  pathwayId: string
): Promise<{ pathway_id: string; current_day: number; message: string }> {
  return api.post(`/pathways/${pathwayId}/days/0/skip`);
}

export async function getActivePathways(): Promise<PathwaySummary[]> {
  return api.get<PathwaySummary[]>('/pathways/active');
}
