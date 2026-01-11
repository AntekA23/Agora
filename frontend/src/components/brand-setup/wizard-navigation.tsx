"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Check, Loader2 } from "lucide-react";

interface WizardNavigationProps {
  currentStep: number;
  totalSteps: number;
  onBack: () => void;
  onNext: () => void;
  onComplete: () => void;
  isLoading?: boolean;
  canGoBack?: boolean;
  canGoNext?: boolean;
  nextLabel?: string;
  completeLabel?: string;
}

export function WizardNavigation({
  currentStep,
  totalSteps,
  onBack,
  onNext,
  onComplete,
  isLoading = false,
  canGoBack = true,
  canGoNext = true,
  nextLabel = "Dalej",
  completeLabel = "Zakoncz",
}: WizardNavigationProps) {
  const isLastStep = currentStep === totalSteps - 1;

  return (
    <div className="flex justify-between items-center">
      <Button
        variant="outline"
        onClick={onBack}
        disabled={!canGoBack || currentStep === 0 || isLoading}
      >
        <ChevronLeft className="h-4 w-4 mr-2" />
        Wstecz
      </Button>

      {isLastStep ? (
        <Button onClick={onComplete} disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Zapisywanie...
            </>
          ) : (
            <>
              <Check className="h-4 w-4 mr-2" />
              {completeLabel}
            </>
          )}
        </Button>
      ) : (
        <Button onClick={onNext} disabled={!canGoNext || isLoading}>
          {nextLabel}
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      )}
    </div>
  );
}
