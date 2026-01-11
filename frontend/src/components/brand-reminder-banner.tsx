"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { X, Sparkles, Clock, ChevronRight } from "lucide-react";

interface WizardStatus {
  wizard_completed: boolean;
  has_description: boolean;
  has_products: boolean;
  has_target_audience: boolean;
  show_reminder: boolean;
  reminder_dismissed: boolean;
  snooze_until: string | null;
}

export function BrandReminderBanner() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ["wizard-status"],
    queryFn: () => api.get<WizardStatus>("/companies/me/wizard/status"),
  });

  const updateReminder = useMutation({
    mutationFn: (action: "dismiss" | "snooze") =>
      api.post("/companies/me/wizard/reminder", {
        action,
        snooze_days: 7,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wizard-status"] });
    },
  });

  // Don't show if loading, completed, or reminder is hidden
  if (isLoading || !status || !status.show_reminder) {
    return null;
  }

  const handleComplete = () => {
    router.push("/brand-setup");
  };

  const handleSnooze = () => {
    updateReminder.mutate("snooze");
  };

  const handleDismiss = () => {
    updateReminder.mutate("dismiss");
  };

  // Calculate completion percentage
  const completedItems = [
    status.has_description,
    status.has_products,
    status.has_target_audience,
  ].filter(Boolean).length;
  const totalItems = 3;
  const percentage = Math.round((completedItems / totalItems) * 100);

  return (
    <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">
              Uzupelnij dane firmy
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Pomoz AI lepiej zrozumiec Twoja firme, zeby generowac trafniejsze tresci.
              {percentage > 0 && (
                <span className="ml-1">
                  Uzupelniono: {percentage}%
                </span>
              )}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" onClick={handleComplete}>
                Uzupelnij teraz
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSnooze}
                disabled={updateReminder.isPending}
              >
                <Clock className="w-4 h-4 mr-1" />
                Przypomnij za tydzien
              </Button>
            </div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDismiss}
          disabled={updateReminder.isPending}
          className="flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
