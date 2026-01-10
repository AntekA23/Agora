"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Task, TaskListResponse, InstagramTaskInput, CopywriterTaskInput } from "@/types/task";

interface TaskFilters {
  page?: number;
  per_page?: number;
  department?: string;
  agent?: string;
  status?: string;
}

export function useTasks(filters: TaskFilters = {}) {
  const params = new URLSearchParams();

  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.department) params.set("department", filters.department);
  if (filters.agent) params.set("agent", filters.agent);
  if (filters.status) params.set("status", filters.status);

  const queryString = params.toString();
  const endpoint = `/tasks${queryString ? `?${queryString}` : ""}`;

  return useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => api.get<TaskListResponse>(endpoint),
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 3 seconds if there are pending/processing tasks
      if (data?.tasks?.some(t => t.status === "pending" || t.status === "processing")) {
        return 3000;
      }
      return false;
    },
    refetchOnWindowFocus: true,
    staleTime: 0,
  });
}

export function useTask(taskId: string | null) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api.get<Task>(`/tasks/${taskId}`),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === "pending" || data.status === "processing")) {
        return 2000; // Poll every 2 seconds while processing
      }
      return false;
    },
  });
}

export function useCreateInstagramTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InstagramTaskInput) =>
      api.post<Task>("/agents/marketing/instagram", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useCreateCopywriterTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CopywriterTaskInput) =>
      api.post<Task>("/agents/marketing/copywriter", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useRetryTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) =>
      api.post<Task>(`/tasks/${taskId}/retry`),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => api.delete(`/tasks/${taskId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}
