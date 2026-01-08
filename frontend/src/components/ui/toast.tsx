"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Toast as ToastType, ToastVariant } from "@/hooks/use-toast";

interface ToastProps extends Omit<ToastType, "id"> {
  onDismiss?: () => void;
}

const variantStyles: Record<ToastVariant, string> = {
  default: "bg-background border-border",
  destructive: "bg-destructive text-destructive-foreground border-destructive",
};

export function Toast({ title, description, variant = "default", onDismiss }: ToastProps) {
  return (
    <div
      className={cn(
        "pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-4 shadow-lg transition-all",
        variantStyles[variant]
      )}
    >
      <div className="flex-1">
        {title && <div className="text-sm font-semibold">{title}</div>}
        {description && (
          <div className="text-sm opacity-90">{description}</div>
        )}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="rounded-md p-1 opacity-50 hover:opacity-100 transition-opacity"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
