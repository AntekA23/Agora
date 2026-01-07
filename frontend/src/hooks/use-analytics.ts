"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface DashboardAnalytics {
  summary: {
    total_tasks: number;
    tasks_today: number;
    tasks_week: number;
    completion_rate: number;
  };
  tasks_by_status: Record<string, number>;
  tasks_by_department: Record<string, number>;
  tasks_by_agent: Record<string, number>;
  daily_activity: Array<{ date: string; count: number }>;
}

export function useDashboardAnalytics() {
  return useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: () => api.get<DashboardAnalytics>("/analytics/dashboard"),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}
