"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  InterpretRequest,
  InterpretResponse,
  QuickActionsResponse,
  QuickActionRequest,
} from "@/types/assistant";

/**
 * Hook to interpret natural language messages.
 */
export function useInterpretMessage() {
  return useMutation({
    mutationFn: (data: InterpretRequest) =>
      api.post<InterpretResponse>("/assistant/interpret", data),
  });
}

/**
 * Hook to interpret quick action selections.
 */
export function useInterpretQuickAction() {
  return useMutation({
    mutationFn: (data: QuickActionRequest) =>
      api.post<InterpretResponse>("/assistant/quick-action", data),
  });
}

/**
 * Hook to fetch available quick actions.
 */
export function useQuickActions() {
  return useQuery({
    queryKey: ["quick-actions"],
    queryFn: () => api.get<QuickActionsResponse>("/assistant/quick-actions"),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
