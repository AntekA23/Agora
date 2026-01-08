"use client";

import * as React from "react";
import {
  Instagram,
  PenLine,
  FileText,
  TrendingUp,
  Rocket,
  Briefcase,
  MoreHorizontal,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuickActions, useInterpretQuickAction } from "@/hooks/use-assistant";
import type { InterpretResponse, QuickAction } from "@/types/assistant";

// Icon mapping for quick actions
const ICON_MAP: Record<string, LucideIcon> = {
  instagram: Instagram,
  pen: PenLine,
  "file-text": FileText,
  "trending-up": TrendingUp,
  rocket: Rocket,
  briefcase: Briefcase,
};

interface QuickActionsProps {
  onSelect?: (result: InterpretResponse, action: QuickAction) => void;
  className?: string;
  maxVisible?: number;
}

export function QuickActions({
  onSelect,
  className,
  maxVisible = 6,
}: QuickActionsProps) {
  const { data, isLoading } = useQuickActions();
  const { mutate: interpretAction, isPending } = useInterpretQuickAction();

  const actions = data?.actions ?? [];
  const visibleActions = actions.slice(0, maxVisible);
  const hasMore = actions.length > maxVisible;

  const handleClick = React.useCallback(
    (action: QuickAction) => {
      if (isPending) return;

      interpretAction(
        { action_id: action.id },
        {
          onSuccess: (result) => {
            onSelect?.(result, action);
          },
        }
      );
    },
    [interpretAction, isPending, onSelect]
  );

  if (isLoading) {
    return (
      <div className={cn("flex flex-wrap gap-3", className)}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-24 w-32 animate-pulse rounded-xl bg-muted"
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("flex flex-wrap gap-3", className)}>
      {visibleActions.map((action) => {
        const Icon = ICON_MAP[action.icon] || FileText;

        return (
          <button
            key={action.id}
            type="button"
            onClick={() => handleClick(action)}
            disabled={isPending}
            className={cn(
              "group flex flex-col items-center justify-center gap-2 rounded-xl border border-border bg-card p-4 text-center transition-all",
              "hover:border-primary/50 hover:bg-accent hover:shadow-md",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "min-w-[120px] max-w-[150px]"
            )}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
              <Icon className="h-5 w-5" />
            </div>
            <span className="text-sm font-medium text-foreground">
              {action.label}
            </span>
          </button>
        );
      })}

      {hasMore && (
        <button
          type="button"
          onClick={() => {
            // Could open a dialog with all actions
          }}
          className={cn(
            "group flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card/50 p-4 text-center transition-all",
            "hover:border-primary/50 hover:bg-accent",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            "min-w-[120px] max-w-[150px]"
          )}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <MoreHorizontal className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-muted-foreground">
            Wiecej
          </span>
        </button>
      )}
    </div>
  );
}

/**
 * Compact version of quick actions as a horizontal list.
 */
export function QuickActionsCompact({
  onSelect,
  className,
}: QuickActionsProps) {
  const { data, isLoading } = useQuickActions();
  const { mutate: interpretAction, isPending } = useInterpretQuickAction();

  const actions = data?.actions ?? [];

  const handleClick = React.useCallback(
    (action: QuickAction) => {
      if (isPending) return;

      interpretAction(
        { action_id: action.id },
        {
          onSuccess: (result) => {
            onSelect?.(result, action);
          },
        }
      );
    },
    [interpretAction, isPending, onSelect]
  );

  if (isLoading) {
    return (
      <div className={cn("flex gap-2 overflow-x-auto", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-9 w-24 animate-pulse rounded-full bg-muted"
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("flex gap-2 overflow-x-auto pb-1", className)}>
      {actions.map((action) => {
        const Icon = ICON_MAP[action.icon] || FileText;

        return (
          <button
            key={action.id}
            type="button"
            onClick={() => handleClick(action)}
            disabled={isPending}
            className={cn(
              "inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-sm transition-all",
              "hover:border-primary/50 hover:bg-accent",
              "focus:outline-none focus:ring-2 focus:ring-ring",
              "disabled:cursor-not-allowed disabled:opacity-50"
            )}
          >
            <Icon className="h-3.5 w-3.5 text-primary" />
            <span className="text-foreground">{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
