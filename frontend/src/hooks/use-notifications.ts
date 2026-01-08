"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export type NotificationType =
  | "pending_approval"
  | "content_approved"
  | "content_rejected"
  | "content_published"
  | "content_failed"
  | "rule_generated"
  | "rule_error"
  | "batch_completed"
  | "batch_failed"
  | "system_info"
  | "system_warning";

export type NotificationPriority = "low" | "normal" | "high" | "urgent";

export interface NotificationAction {
  label: string;
  action_type: "navigate" | "approve" | "reject" | "dismiss";
  action_url?: string;
  action_data?: Record<string, unknown>;
}

export interface Notification {
  id: string;
  type: NotificationType;
  priority: NotificationPriority;
  title: string;
  message: string;
  icon?: string;
  related_type?: string;
  related_id?: string;
  action_url?: string;
  actions: NotificationAction[];
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationCountResponse {
  unread_count: number;
}

// Hooks
export function useNotifications(options?: {
  includeRead?: boolean;
  includeDismissed?: boolean;
  limit?: number;
}) {
  const params = new URLSearchParams();
  if (options?.includeRead) params.set("include_read", "true");
  if (options?.includeDismissed) params.set("include_dismissed", "true");
  if (options?.limit) params.set("limit", String(options.limit));

  const queryString = params.toString();
  const endpoint = `/notifications${queryString ? `?${queryString}` : ""}`;

  return useQuery({
    queryKey: ["notifications", options],
    queryFn: () => api.get<NotificationListResponse>(endpoint),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useNotificationCount() {
  return useQuery({
    queryKey: ["notifications", "count"],
    queryFn: () => api.get<NotificationCountResponse>("/notifications/count"),
    refetchInterval: 15000, // Refetch every 15 seconds
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      api.post(`/notifications/${notificationId}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post("/notifications/mark-read", { notification_ids: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useDismissNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      api.delete(`/notifications/${notificationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useDismissAllNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post("/notifications/dismiss", { notification_ids: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

// Helper functions
export const notificationIcons: Record<NotificationType, string> = {
  pending_approval: "AlertCircle",
  content_approved: "CheckCircle",
  content_rejected: "XCircle",
  content_published: "CheckCircle",
  content_failed: "AlertTriangle",
  rule_generated: "Sparkles",
  rule_error: "AlertTriangle",
  batch_completed: "Rocket",
  batch_failed: "AlertTriangle",
  system_info: "Info",
  system_warning: "AlertTriangle",
};

export const notificationColors: Record<NotificationPriority, string> = {
  low: "text-muted-foreground",
  normal: "text-foreground",
  high: "text-orange-500",
  urgent: "text-destructive",
};
