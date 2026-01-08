"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export type ContentStatus =
  | "draft"
  | "queued"
  | "scheduled"
  | "pending_approval"
  | "publishing"
  | "published"
  | "failed";

export type ContentPlatform =
  | "instagram"
  | "facebook"
  | "linkedin"
  | "twitter"
  | "email"
  | "other";

export type ContentType =
  | "instagram_post"
  | "instagram_story"
  | "instagram_reel"
  | "facebook_post"
  | "linkedin_post"
  | "twitter_post"
  | "email_newsletter"
  | "ad_copy"
  | "other";

export interface ScheduledContent {
  id: string;
  company_id: string;
  created_by: string;
  title: string;
  content_type: ContentType;
  platform: ContentPlatform;
  content: Record<string, unknown>;
  media_urls: string[];
  status: ContentStatus;
  scheduled_for: string | null;
  timezone: string;
  published_at: string | null;
  source_task_id: string | null;
  source_conversation_id: string | null;
  source_rule_id: string | null;
  platform_post_id: string | null;
  platform_post_url: string | null;
  engagement_stats: Record<string, number> | null;
  error_message: string | null;
  retry_count: number;
  requires_approval: boolean;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledContentListResponse {
  items: ScheduledContent[];
  total: number;
  page: number;
  per_page: number;
}

export interface ScheduledContentStats {
  total: number;
  by_status: Record<string, number>;
  by_platform: Record<string, number>;
  scheduled_this_week: number;
  published_this_week: number;
}

export interface ScheduledContentCreate {
  title: string;
  content_type: ContentType;
  platform: ContentPlatform;
  content?: Record<string, unknown>;
  media_urls?: string[];
  scheduled_for?: string;
  timezone?: string;
  source_task_id?: string;
  source_conversation_id?: string;
  requires_approval?: boolean;
}

export interface ScheduledContentUpdate {
  title?: string;
  content?: Record<string, unknown>;
  media_urls?: string[];
  scheduled_for?: string;
  timezone?: string;
  status?: ContentStatus;
  requires_approval?: boolean;
}

export interface BulkActionRequest {
  ids: string[];
  action: "approve" | "reject" | "delete" | "reschedule";
  new_scheduled_for?: string;
}

export interface BulkActionResponse {
  success_count: number;
  failed_count: number;
  failed_ids: string[];
  errors: Record<string, string>;
}

// Filters
interface ScheduledContentFilters {
  page?: number;
  per_page?: number;
  status?: ContentStatus[];
  platform?: ContentPlatform[];
  content_type?: ContentType[];
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Hooks
export function useScheduledContent(filters: ScheduledContentFilters = {}) {
  const params = new URLSearchParams();

  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.status?.length) {
    filters.status.forEach((s) => params.append("status", s));
  }
  if (filters.platform?.length) {
    filters.platform.forEach((p) => params.append("platform", p));
  }
  if (filters.content_type?.length) {
    filters.content_type.forEach((ct) => params.append("content_type", ct));
  }
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.search) params.set("search", filters.search);

  const queryString = params.toString();
  const endpoint = `/scheduled-content${queryString ? `?${queryString}` : ""}`;

  return useQuery({
    queryKey: ["scheduled-content", filters],
    queryFn: () => api.get<ScheduledContentListResponse>(endpoint),
  });
}

export function useScheduledContentItem(contentId: string | null) {
  return useQuery({
    queryKey: ["scheduled-content", contentId],
    queryFn: () => api.get<ScheduledContent>(`/scheduled-content/${contentId}`),
    enabled: !!contentId,
  });
}

export function useScheduledContentStats() {
  return useQuery({
    queryKey: ["scheduled-content-stats"],
    queryFn: () => api.get<ScheduledContentStats>("/scheduled-content/stats"),
  });
}

export function useCreateScheduledContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduledContentCreate) =>
      api.post<ScheduledContent>("/scheduled-content", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function useUpdateScheduledContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: ScheduledContentUpdate;
    }) => api.patch<ScheduledContent>(`/scheduled-content/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content", id] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function useDeleteScheduledContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/scheduled-content/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function useApproveContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      scheduled_for,
    }: {
      id: string;
      scheduled_for?: string;
    }) =>
      api.post<ScheduledContent>(`/scheduled-content/${id}/approve`, {
        scheduled_for,
      }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content", id] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function useRejectContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<ScheduledContent>(`/scheduled-content/${id}/reject`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content", id] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function usePublishContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<ScheduledContent>(`/scheduled-content/${id}/publish`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content", id] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

export function useBulkAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkActionRequest) =>
      api.post<BulkActionResponse>("/scheduled-content/bulk-action", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["scheduled-content-stats"] });
    },
  });
}

// Helper functions
export const statusLabels: Record<ContentStatus, string> = {
  draft: "Szkic",
  queued: "W kolejce",
  scheduled: "Zaplanowane",
  pending_approval: "Do zatwierdzenia",
  publishing: "Publikowanie",
  published: "Opublikowane",
  failed: "Błąd",
};

export const statusColors: Record<ContentStatus, string> = {
  draft: "text-muted-foreground",
  queued: "text-blue-500",
  scheduled: "text-primary",
  pending_approval: "text-yellow-500",
  publishing: "text-blue-500",
  published: "text-green-500",
  failed: "text-red-500",
};

export const platformLabels: Record<ContentPlatform, string> = {
  instagram: "Instagram",
  facebook: "Facebook",
  linkedin: "LinkedIn",
  twitter: "Twitter/X",
  email: "Email",
  other: "Inne",
};

export const contentTypeLabels: Record<ContentType, string> = {
  instagram_post: "Post Instagram",
  instagram_story: "Story Instagram",
  instagram_reel: "Reel Instagram",
  facebook_post: "Post Facebook",
  linkedin_post: "Post LinkedIn",
  twitter_post: "Post Twitter",
  email_newsletter: "Newsletter",
  ad_copy: "Tekst reklamowy",
  other: "Inne",
};
