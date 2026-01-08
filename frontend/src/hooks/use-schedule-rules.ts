"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { type ContentPlatform, type ContentType } from "./use-scheduled-content";

// Types
export type RuleFrequency = "daily" | "weekly" | "monthly";

export type ContentCategory =
  | "motivational"
  | "industry_news"
  | "educational"
  | "promotional"
  | "behind_scenes"
  | "seasonal"
  | "custom";

export type ApprovalMode = "auto_publish" | "require_approval" | "draft_only";

export interface ScheduleConfig {
  frequency: RuleFrequency;
  days_of_week: number[];
  day_of_month: number | null;
  time: string;
  timezone: string;
}

export interface ContentTemplate {
  category: ContentCategory;
  prompt_template: string;
  style: string;
  include_hashtags: boolean;
  include_emoji: boolean;
  generate_image: boolean;
  additional_instructions: string;
}

export interface ScheduleRule {
  id: string;
  company_id: string;
  created_by: string;
  name: string;
  description: string | null;
  content_type: ContentType;
  platform: ContentPlatform;
  content_template: ContentTemplate;
  schedule: ScheduleConfig;
  approval_mode: ApprovalMode;
  notify_before_publish: boolean;
  notification_minutes: number;
  fallback_on_no_response: string;
  is_active: boolean;
  last_executed: string | null;
  next_execution: string | null;
  last_error: string | null;
  max_queue_size: number;
  total_generated: number;
  total_published: number;
  queue_count: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduleRuleListResponse {
  items: ScheduleRule[];
  total: number;
  active_count: number;
  paused_count: number;
}

export interface ScheduleRuleStats {
  total_rules: number;
  active_rules: number;
  paused_rules: number;
  total_generated: number;
  total_published: number;
  next_executions: {
    rule_id: string;
    rule_name: string;
    next_execution: string | null;
  }[];
}

export interface ScheduleRuleCreate {
  name: string;
  description?: string;
  content_type: ContentType;
  platform: ContentPlatform;
  content_template: Partial<ContentTemplate>;
  schedule: Partial<ScheduleConfig>;
  approval_mode: ApprovalMode;
  notify_before_publish?: boolean;
  notification_minutes?: number;
  fallback_on_no_response?: string;
  max_queue_size?: number;
}

export interface ScheduleRuleUpdate {
  name?: string;
  description?: string;
  content_template?: Partial<ContentTemplate>;
  schedule?: Partial<ScheduleConfig>;
  approval_mode?: ApprovalMode;
  notify_before_publish?: boolean;
  notification_minutes?: number;
  fallback_on_no_response?: string;
  max_queue_size?: number;
}

export interface GenerateNowResponse {
  success: boolean;
  scheduled_content_id?: string;
  error?: string;
}

// Hooks
export function useScheduleRules(isActive?: boolean) {
  const params = new URLSearchParams();
  if (isActive !== undefined) {
    params.set("is_active", String(isActive));
  }
  const queryString = params.toString();
  const endpoint = `/schedule-rules${queryString ? `?${queryString}` : ""}`;

  return useQuery({
    queryKey: ["schedule-rules", isActive],
    queryFn: () => api.get<ScheduleRuleListResponse>(endpoint),
  });
}

export function useScheduleRule(ruleId: string | null) {
  return useQuery({
    queryKey: ["schedule-rules", ruleId],
    queryFn: () => api.get<ScheduleRule>(`/schedule-rules/${ruleId}`),
    enabled: !!ruleId,
  });
}

export function useScheduleRuleStats() {
  return useQuery({
    queryKey: ["schedule-rules-stats"],
    queryFn: () => api.get<ScheduleRuleStats>("/schedule-rules/stats"),
  });
}

export function useCreateScheduleRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduleRuleCreate) =>
      api.post<ScheduleRule>("/schedule-rules", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-rules"] });
    },
  });
}

export function useUpdateScheduleRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScheduleRuleUpdate }) =>
      api.patch<ScheduleRule>(`/schedule-rules/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["schedule-rules"] });
      queryClient.invalidateQueries({ queryKey: ["schedule-rules", id] });
    },
  });
}

export function useDeleteScheduleRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/schedule-rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-rules"] });
    },
  });
}

export function useToggleScheduleRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<ScheduleRule>(`/schedule-rules/${id}/toggle`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["schedule-rules"] });
      queryClient.invalidateQueries({ queryKey: ["schedule-rules", id] });
    },
  });
}

export function useGenerateNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      schedule_for,
    }: {
      id: string;
      schedule_for?: string;
    }) =>
      api.post<GenerateNowResponse>(`/schedule-rules/${id}/generate-now`, {
        schedule_for,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-rules"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
    },
  });
}

// Helper labels
export const frequencyLabels: Record<RuleFrequency, string> = {
  daily: "Codziennie",
  weekly: "Co tydzień",
  monthly: "Co miesiąc",
};

export const categoryLabels: Record<ContentCategory, string> = {
  motivational: "Motywacyjne",
  industry_news: "Branżowe newsy",
  educational: "Edukacyjne",
  promotional: "Promocyjne",
  behind_scenes: "Za kulisami",
  seasonal: "Okolicznościowe",
  custom: "Własny szablon",
};

export const approvalModeLabels: Record<ApprovalMode, string> = {
  auto_publish: "Pełna autonomia",
  require_approval: "Wymaga zatwierdzenia",
  draft_only: "Tylko generuj do kolejki",
};

export const dayLabels: Record<number, string> = {
  0: "Pon",
  1: "Wto",
  2: "Śro",
  3: "Czw",
  4: "Pią",
  5: "Sob",
  6: "Nie",
};

export const dayFullLabels: Record<number, string> = {
  0: "Poniedziałek",
  1: "Wtorek",
  2: "Środa",
  3: "Czwartek",
  4: "Piątek",
  5: "Sobota",
  6: "Niedziela",
};
