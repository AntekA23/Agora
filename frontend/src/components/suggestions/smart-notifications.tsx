"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  useSuggestions,
  useDismissSuggestion,
  ContentIdea,
  TrendSuggestion,
  getEventTypeColor,
} from "@/hooks/use-suggestions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Lightbulb,
  Calendar,
  TrendingUp,
  Clock,
  X,
  ChevronRight,
  Sparkles,
  AlertCircle,
  Loader2,
  Bell,
  Gift,
  Sun,
  Snowflake,
  Leaf,
  Flower2,
} from "lucide-react";

// Season icons
const seasonIcons: Record<string, typeof Sun> = {
  holiday: Gift,
  commercial: TrendingUp,
  seasonal: Sun,
};

interface SmartNotificationsProps {
  maxItems?: number;
  showTrends?: boolean;
  compact?: boolean;
}

export function SmartNotifications({
  maxItems = 5,
  showTrends = true,
  compact = false,
}: SmartNotificationsProps) {
  const router = useRouter();
  const { data, isLoading, error } = useSuggestions(14, showTrends);
  const dismissMutation = useDismissSuggestion();

  const [dismissedIds, setDismissedIds] = React.useState<Set<string>>(new Set());

  const handleDismiss = (id: string) => {
    setDismissedIds((prev) => {
      const newSet = new Set(prev);
      newSet.add(id);
      return newSet;
    });
    dismissMutation.mutate(id);
  };

  const handleAction = (suggestion: ContentIdea) => {
    // Navigate to marketing with pre-filled data
    const params = new URLSearchParams();
    if (suggestion.event_name) {
      params.set("brief", `Post z okazji ${suggestion.event_name}`);
    }
    router.push(`/marketing?${params.toString()}`);
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "high":
        return (
          <Badge variant="destructive" className="text-xs">
            Pilne
          </Badge>
        );
      case "medium":
        return (
          <Badge variant="secondary" className="text-xs bg-yellow-500/10 text-yellow-600">
            Wkrotce
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-xs">
            Zaplanuj
          </Badge>
        );
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8 text-muted-foreground">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>Nie mozna zaladowac sugestii</span>
        </CardContent>
      </Card>
    );
  }

  // Combine and filter suggestions
  const allSuggestions = [
    ...data.urgent,
    ...data.upcoming,
    ...data.planned.slice(0, 2),
  ].filter((s) => !dismissedIds.has(s.event_name || s.title));

  const visibleSuggestions = allSuggestions.slice(0, maxItems);
  const trends = data.trends.filter((t) => !dismissedIds.has(t.title));

  if (visibleSuggestions.length === 0 && trends.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-8 text-muted-foreground">
          <Sparkles className="h-8 w-8 mb-2" />
          <p className="font-medium">Wszystko zaplanowane!</p>
          <p className="text-sm">Brak nowych sugestii na teraz.</p>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {visibleSuggestions.slice(0, 3).map((suggestion, idx) => {
          const EventIcon = seasonIcons[suggestion.suggestion_type] || Calendar;
          return (
            <button
              key={idx}
              onClick={() => handleAction(suggestion)}
              className="w-full flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors text-left"
            >
              <div className={`p-2 rounded-lg ${suggestion.priority === "high" ? "bg-red-500/10" : "bg-primary/10"}`}>
                <EventIcon className={`h-4 w-4 ${suggestion.priority === "high" ? "text-red-500" : "text-primary"}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{suggestion.event_name || suggestion.title}</p>
                <p className="text-xs text-muted-foreground">
                  {suggestion.days_until === 0
                    ? "Dzisiaj!"
                    : suggestion.days_until === 1
                    ? "Jutro"
                    : `Za ${suggestion.days_until} dni`}
                </p>
              </div>
              {getPriorityBadge(suggestion.priority)}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            Sugestie dla Ciebie
          </CardTitle>
          <Badge variant="secondary" className="text-xs">
            {data.summary.total_suggestions} pomyslow
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Urgent items */}
        {data.urgent.length > 0 && (
          <div className="space-y-2">
            {data.urgent
              .filter((s) => !dismissedIds.has(s.event_name || s.title))
              .map((suggestion, idx) => (
                <SuggestionItem
                  key={`urgent-${idx}`}
                  suggestion={suggestion}
                  onAction={() => handleAction(suggestion)}
                  onDismiss={() => handleDismiss(suggestion.event_name || suggestion.title)}
                />
              ))}
          </div>
        )}

        {/* Upcoming items */}
        {data.upcoming.length > 0 && (
          <div className="space-y-2">
            {data.upcoming
              .filter((s) => !dismissedIds.has(s.event_name || s.title))
              .slice(0, 3)
              .map((suggestion, idx) => (
                <SuggestionItem
                  key={`upcoming-${idx}`}
                  suggestion={suggestion}
                  onAction={() => handleAction(suggestion)}
                  onDismiss={() => handleDismiss(suggestion.event_name || suggestion.title)}
                />
              ))}
          </div>
        )}

        {/* Trends */}
        {showTrends && trends.length > 0 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              Trendy w Twojej branzy
            </p>
            {trends.map((trend, idx) => (
              <div
                key={`trend-${idx}`}
                className="p-3 rounded-lg bg-muted/50 text-sm"
              >
                <p className="font-medium">{trend.title}</p>
                <p className="text-muted-foreground text-xs mt-1 line-clamp-2">
                  {trend.content}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* View all link */}
        {allSuggestions.length > maxItems && (
          <Button
            variant="ghost"
            className="w-full text-muted-foreground"
            onClick={() => router.push("/suggestions")}
          >
            Zobacz wszystkie ({data.summary.total_suggestions})
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

interface SuggestionItemProps {
  suggestion: ContentIdea;
  onAction: () => void;
  onDismiss: () => void;
}

function SuggestionItem({ suggestion, onAction, onDismiss }: SuggestionItemProps) {
  const EventIcon = seasonIcons[suggestion.suggestion_type] || Calendar;
  const isUrgent = suggestion.priority === "high";

  return (
    <div
      className={`relative group flex items-start gap-3 p-3 rounded-lg border transition-colors ${
        isUrgent
          ? "border-red-500/30 bg-red-500/5 hover:bg-red-500/10"
          : "bg-card hover:bg-muted/50"
      }`}
    >
      {/* Icon */}
      <div
        className={`shrink-0 p-2 rounded-lg ${
          isUrgent ? "bg-red-500/10" : "bg-primary/10"
        }`}
      >
        <EventIcon
          className={`h-5 w-5 ${isUrgent ? "text-red-500" : "text-primary"}`}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-medium text-sm">
              {suggestion.event_name || suggestion.title}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {suggestion.days_until === 0
                  ? "Dzisiaj!"
                  : suggestion.days_until === 1
                  ? "Jutro"
                  : `Za ${suggestion.days_until} dni`}
              </span>
              {isUrgent && (
                <Badge variant="destructive" className="text-xs h-5">
                  Pilne
                </Badge>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
          >
            <X className="h-3 w-3" />
          </Button>
        </div>

        {suggestion.marketing_tip && (
          <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
            {suggestion.marketing_tip}
          </p>
        )}

        <Button
          variant="link"
          size="sm"
          className="h-auto p-0 mt-2 text-xs"
          onClick={onAction}
        >
          Stworz post
          <ChevronRight className="h-3 w-3 ml-1" />
        </Button>
      </div>
    </div>
  );
}
