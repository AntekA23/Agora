"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { type ContentPlatform, type ContentType } from "./use-scheduled-content";

// Types
export type VarietyLevel = "low" | "medium" | "high";

export interface DateRange {
  start: string;
  end: string;
}

export interface BatchGenerationRequest {
  content_type: ContentType;
  platform: ContentPlatform;
  count: number;
  theme: string;
  variety: VarietyLevel;
  date_range?: DateRange;
  auto_schedule: boolean;
  require_approval: boolean;
}

export interface GeneratedItemContent {
  text?: string;
  caption?: string;
  hashtags?: string[];
  error?: string;
}

export interface GeneratedItem {
  index: number;
  prompt: string;
  content: GeneratedItemContent | null;
  status: "success" | "failed";
  error?: string;
}

export interface ScheduledItem {
  id: string;
  title: string;
  scheduled_for: string | null;
  status: string;
}

export interface BatchGenerationResponse {
  total_requested: number;
  total_generated: number;
  total_failed: number;
  total_scheduled: number;
  generated_items: GeneratedItem[];
  scheduled_items: ScheduledItem[];
}

export interface BatchStats {
  total_batches: number;
  total_items_generated: number;
  total_items_scheduled: number;
  total_items_published: number;
  average_batch_size: number;
  most_used_platform: ContentPlatform | null;
}

// Hooks
export function useBatchGeneration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchGenerationRequest) =>
      api.post<BatchGenerationResponse>("/batch/generate", data),
    onSuccess: () => {
      // Invalidate scheduled content queries to reflect new items
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
    },
  });
}

export function useBatchStats() {
  return useQuery({
    queryKey: ["batch-stats"],
    queryFn: () => api.get<BatchStats>("/batch/stats"),
  });
}

export function useRemoveFromBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (contentId: string) =>
      api.delete(`/batch/scheduled/${contentId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-content"] });
      queryClient.invalidateQueries({ queryKey: ["batch-stats"] });
    },
  });
}

// Helper labels
export const varietyLabels: Record<VarietyLevel, string> = {
  low: "Podobne",
  medium: "Zróżnicowane",
  high: "Bardzo różnorodne",
};

export const varietyDescriptions: Record<VarietyLevel, string> = {
  low: "Treści będą spójne stylistycznie",
  medium: "Treści będą zróżnicowane pod względem stylu i podejścia",
  high: "Maksymalna różnorodność - każdy post będzie unikalny",
};

export const countOptions = [3, 5, 7, 14, 21, 30];
