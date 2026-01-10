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
    refetchOnMount: "always", // ALWAYS fetch when component mounts or page is visited
    refetchOnWindowFocus: true,
    staleTime: 0,
    // Always poll - faster when there are active tasks, slower otherwise
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasActiveTasks = data?.tasks?.some(
        (t) => t.status === "pending" || t.status === "processing"
      );
      // 2 seconds for active tasks, 5 seconds idle (to catch new tasks)
      return hasActiveTasks ? 2000 : 5000;
    },
  });
}

export function useTask(taskId: string | null) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api.get<Task>(`/tasks/${taskId}`),
    enabled: !!taskId,
    staleTime: 0,
    // Always poll for non-terminal statuses, stop when completed/failed
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === "completed" || data.status === "failed")) {
        return false; // Stop polling when terminal
      }
      return 2000; // Poll every 2 seconds until terminal
    },
  });
}

export function useCreateInstagramTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InstagramTaskInput) =>
      api.post<Task>("/agents/marketing/instagram", data),
    onSuccess: async () => {
      // Force immediate refetch of tasks list
      await queryClient.refetchQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useCreateCopywriterTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CopywriterTaskInput) =>
      api.post<Task>("/agents/marketing/copywriter", data),
    onSuccess: async () => {
      // Force immediate refetch of tasks list
      await queryClient.refetchQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useRetryTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) =>
      api.post<Task>(`/tasks/${taskId}/retry`),
    onSuccess: async (_, taskId) => {
      // Force immediate refetch
      await queryClient.refetchQueries({ queryKey: ["tasks"] });
      await queryClient.refetchQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => api.delete(`/tasks/${taskId}`),
    onSuccess: async () => {
      // Force immediate refetch of tasks list
      await queryClient.refetchQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}
