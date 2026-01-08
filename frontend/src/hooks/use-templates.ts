"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface TemplateField {
  name: string;
  label: string;
  type: "text" | "textarea" | "select" | "date" | "checkbox";
  required: boolean;
  options?: string[];
  showIf?: Record<string, string>;
}

export interface Template {
  id: string;
  name: string;
  icon: string;
  description: string;
  fields: TemplateField[];
  default_prompt: string;
}

export interface TemplateCategory {
  id: string;
  name: string;
  icon: string;
  templates: Template[];
}

export interface TemplatesResponse {
  categories: TemplateCategory[];
}

export interface TemplateHistoryEntry {
  template_id: string;
  category_id: string;
  params: Record<string, unknown>;
  used_at: string;
  task_id?: string;
}

export interface TemplateHistoryResponse {
  template_id: string;
  category_id: string;
  last_used: Record<string, unknown> | null;
  usage_count: number;
}

export interface SaveTemplateHistoryRequest {
  template_id: string;
  category_id: string;
  params: Record<string, unknown>;
  task_id?: string;
}

// Hooks
export function useTemplates() {
  return useQuery({
    queryKey: ["templates"],
    queryFn: () => api.get<TemplatesResponse>("/templates"),
    staleTime: 1000 * 60 * 60, // Cache for 1 hour - templates don't change often
  });
}

export function useTemplateHistory(categoryId: string, templateId: string) {
  return useQuery({
    queryKey: ["template-history", categoryId, templateId],
    queryFn: () =>
      api.get<TemplateHistoryResponse>(
        `/templates/history/${categoryId}/${templateId}`
      ),
    enabled: !!categoryId && !!templateId,
  });
}

export function useRecentTemplates(limit: number = 5) {
  return useQuery({
    queryKey: ["recent-templates", limit],
    queryFn: () =>
      api.get<TemplateHistoryEntry[]>(`/templates/recent?limit=${limit}`),
  });
}

export function useSaveTemplateHistory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SaveTemplateHistoryRequest) =>
      api.post("/templates/history", data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["template-history", variables.category_id, variables.template_id],
      });
      queryClient.invalidateQueries({ queryKey: ["recent-templates"] });
    },
  });
}

// Helper to get template by ID
export function findTemplate(
  categories: TemplateCategory[],
  categoryId: string,
  templateId: string
): Template | undefined {
  const category = categories.find((c) => c.id === categoryId);
  return category?.templates.find((t) => t.id === templateId);
}

// Helper to get category by ID
export function findCategory(
  categories: TemplateCategory[],
  categoryId: string
): TemplateCategory | undefined {
  return categories.find((c) => c.id === categoryId);
}
