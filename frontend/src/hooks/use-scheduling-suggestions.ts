"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { type ContentPlatform, type ContentType } from "./use-scheduled-content";

// Types
export interface SchedulePreferences {
  earliest?: string;
  latest?: string;
  avoid_weekends?: boolean;
}

export interface SuggestTimeRequest {
  content_type: ContentType;
  platform: ContentPlatform;
  content?: Record<string, unknown>;
  preferences?: SchedulePreferences;
}

export interface TimeAlternative {
  time: string;
  score: number;
  reasoning: string;
}

export interface SuggestTimeResponse {
  suggested_time: string;
  confidence: number;
  reasoning: string;
  alternatives: TimeAlternative[];
}

// Hook
export function useSchedulingSuggestions() {
  return useMutation({
    mutationFn: (data: SuggestTimeRequest) =>
      api.post<SuggestTimeResponse>("/scheduled-content/suggest-time", data),
  });
}

// Helper function to format confidence as percentage
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

// Helper function to format suggestion time in Polish timezone
export function formatSuggestionTime(isoString: string, locale: string = "pl-PL"): string {
  const date = new Date(isoString);
  return date.toLocaleString(locale, {
    timeZone: "Europe/Warsaw",
    weekday: "long",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
