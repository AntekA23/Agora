"use client";

import { useState } from "react";
import { Loader2, Inbox } from "lucide-react";
import {
  type ScheduledContent,
  type ContentStatus,
  statusLabels,
} from "@/hooks/use-scheduled-content";
import { QueueItem } from "./queue-item";

interface QueueListProps {
  items: ScheduledContent[];
  isLoading?: boolean;
  groupByStatus?: boolean;
  onView?: (item: ScheduledContent) => void;
  onEdit?: (item: ScheduledContent) => void;
  onDelete?: (item: ScheduledContent) => void;
  onApprove?: (item: ScheduledContent) => void;
  onReject?: (item: ScheduledContent) => void;
}

const statusOrder: ContentStatus[] = [
  "pending_approval",
  "scheduled",
  "queued",
  "draft",
  "publishing",
  "published",
  "failed",
];

export function QueueList({
  items,
  isLoading,
  groupByStatus = true,
  onView,
  onEdit,
  onDelete,
  onApprove,
  onReject,
}: QueueListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Inbox className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium">Kolejka jest pusta</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Dodaj treści do kolejki, aby zaplanować publikacje.
        </p>
      </div>
    );
  }

  if (!groupByStatus) {
    return (
      <div className="space-y-3">
        {items.map((item) => (
          <QueueItem
            key={item.id}
            item={item}
            onView={onView}
            onEdit={onEdit}
            onDelete={onDelete}
            onApprove={onApprove}
            onReject={onReject}
          />
        ))}
      </div>
    );
  }

  // Group items by status
  const groupedItems = items.reduce((acc, item) => {
    const status = item.status;
    if (!acc[status]) {
      acc[status] = [];
    }
    acc[status].push(item);
    return acc;
  }, {} as Record<ContentStatus, ScheduledContent[]>);

  // Sort groups by status order
  const sortedStatuses = statusOrder.filter(
    (status) => groupedItems[status]?.length > 0
  );

  return (
    <div className="space-y-6">
      {sortedStatuses.map((status) => (
        <div key={status}>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              {statusLabels[status]}
            </h3>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
              {groupedItems[status].length}
            </span>
          </div>
          <div className="space-y-3">
            {groupedItems[status].map((item) => (
              <QueueItem
                key={item.id}
                item={item}
                onView={onView}
                onEdit={onEdit}
                onDelete={onDelete}
                onApprove={onApprove}
                onReject={onReject}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
