"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface DepartmentSummary {
  total_tasks: number;
  tasks_this_week: number;
  completed: number;
  pending: number;
  success_rate: number;
}

export interface AgentStats {
  agent: string;
  count: number;
}

export interface RecentTask {
  id: string;
  agent: string;
  type: string;
  status: string;
  created_at: string;
  title: string;
}

export interface WeeklyTrend {
  date: string;
  count: number;
}

export interface DepartmentStats {
  department: string;
  summary: DepartmentSummary;
  tasks_by_agent: AgentStats[];
  recent_tasks: RecentTask[];
  weekly_trend: WeeklyTrend[];
  content_types: Record<string, number>;
}

// Hook
export function useDepartmentStats(department: string) {
  return useQuery({
    queryKey: ["department-stats", department],
    queryFn: () => api.get<DepartmentStats>(`/analytics/department/${department}`),
    staleTime: 1000 * 60 * 2, // 2 minutes cache
  });
}

// Agent labels for display
export const agentLabels: Record<string, string> = {
  instagram_specialist: "Instagram",
  copywriter: "Copywriter",
  image_generator: "Grafiki",
  invoice_specialist: "Faktury",
  cashflow_analyst: "Cashflow",
  hr_recruiter: "Rekrutacja",
  campaign_service: "Kampanie",
};

// Task type labels
export const taskTypeLabels: Record<string, string> = {
  create_post: "Posty",
  create_copy: "Teksty",
  create_invoice: "Faktury",
  analyze_cashflow: "Analizy",
};
