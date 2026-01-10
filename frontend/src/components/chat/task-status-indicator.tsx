"use client";

import { useTask } from "@/hooks/use-tasks";
import { Loader2, CheckCircle, AlertCircle, Clock } from "lucide-react";

interface TaskStatusIndicatorProps {
  taskId: string;
  initialStatus?: string;
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: "Oczekuje w kolejce...",
    className: "text-muted-foreground",
    animate: false,
  },
  processing: {
    icon: Loader2,
    label: "Przetwarzanie...",
    className: "text-blue-500",
    animate: true,
  },
  completed: {
    icon: CheckCircle,
    label: "Zadanie zakonczone",
    className: "text-green-500",
    animate: false,
  },
  failed: {
    icon: AlertCircle,
    label: "Blad zadania",
    className: "text-red-500",
    animate: false,
  },
} as const;

export function TaskStatusIndicator({ taskId, initialStatus }: TaskStatusIndicatorProps) {
  const { data: task } = useTask(taskId);

  // Use live task status if available, otherwise fall back to initial
  const status = (task?.status || initialStatus || "pending") as keyof typeof statusConfig;
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Icon
        className={`h-4 w-4 ${config.className} ${config.animate ? "animate-spin" : ""}`}
      />
      <span>{config.label}</span>
    </div>
  );
}
