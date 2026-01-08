"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface SuggestionSummary {
  total_suggestions: number;
  high_priority: number;
  upcoming_events: number;
}

export interface ContentIdea {
  suggestion_type: string;
  title: string;
  event_name?: string;
  event_date?: string;
  days_until?: number;
  marketing_tip?: string;
  priority: "high" | "medium" | "low";
  suggested_actions: string[];
  industry_angle?: string;
}

export interface CalendarEvent {
  date: string;
  date_full: string;
  name: string;
  type: "holiday" | "commercial" | "seasonal";
  marketing_tip: string;
  days_until: number;
  suggestion_type: string;
}

export interface TrendSuggestion {
  suggestion_type: string;
  title: string;
  content: string;
  action: string;
  priority: string;
}

export interface SuggestionsResponse {
  generated_at: string;
  company_id: string;
  summary: SuggestionSummary;
  urgent: ContentIdea[];
  upcoming: ContentIdea[];
  planned: ContentIdea[];
  trends: TrendSuggestion[];
  calendar_events: CalendarEvent[];
}

// Hooks
export function useSuggestions(daysAhead: number = 14, includeTrends: boolean = true) {
  return useQuery({
    queryKey: ["suggestions", daysAhead, includeTrends],
    queryFn: () =>
      api.get<SuggestionsResponse>(
        `/suggestions?days_ahead=${daysAhead}&include_trends=${includeTrends}`
      ),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });
}

export function useCalendarEvents(daysAhead: number = 30) {
  return useQuery({
    queryKey: ["calendar-events", daysAhead],
    queryFn: () =>
      api.get<CalendarEvent[]>(`/suggestions/calendar?days_ahead=${daysAhead}`),
    staleTime: 1000 * 60 * 60, // Cache for 1 hour - calendar doesn't change often
  });
}

export function useTrendSuggestions(industry?: string) {
  return useQuery({
    queryKey: ["trend-suggestions", industry],
    queryFn: () =>
      api.get<TrendSuggestion[]>(
        `/suggestions/trends${industry ? `?industry=${encodeURIComponent(industry)}` : ""}`
      ),
    enabled: !!industry,
    staleTime: 1000 * 60 * 30, // Cache for 30 minutes
  });
}

export function useDismissSuggestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (suggestionId: string) =>
      api.post(`/suggestions/dismiss/${suggestionId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
    },
  });
}

// Helper to get priority color
export function getPriorityColor(priority: string): string {
  switch (priority) {
    case "high":
      return "text-red-500";
    case "medium":
      return "text-yellow-500";
    case "low":
      return "text-green-500";
    default:
      return "text-muted-foreground";
  }
}

// Helper to get event type color
export function getEventTypeColor(type: string): string {
  switch (type) {
    case "holiday":
      return "bg-red-500/10 text-red-600";
    case "commercial":
      return "bg-green-500/10 text-green-600";
    case "seasonal":
      return "bg-blue-500/10 text-blue-600";
    default:
      return "bg-muted text-muted-foreground";
  }
}
