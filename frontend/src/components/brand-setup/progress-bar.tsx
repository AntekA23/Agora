"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface Step {
  id: number;
  title: string;
  description: string;
}

interface ProgressBarProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (step: number) => void;
}

export function ProgressBar({ steps, currentStep, onStepClick }: ProgressBarProps) {
  return (
    <div className="w-full">
      {/* Desktop view */}
      <div className="hidden md:flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center flex-1">
            {/* Step indicator */}
            <button
              type="button"
              onClick={() => onStepClick?.(step.id)}
              disabled={!onStepClick || step.id > currentStep}
              className={cn(
                "flex flex-col items-center gap-2 transition-colors",
                step.id <= currentStep && onStepClick && "cursor-pointer",
                step.id > currentStep && "cursor-not-allowed"
              )}
            >
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                  step.id < currentStep && "bg-primary text-primary-foreground",
                  step.id === currentStep && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                  step.id > currentStep && "bg-muted text-muted-foreground"
                )}
              >
                {step.id < currentStep ? (
                  <Check className="w-5 h-5" />
                ) : (
                  step.id + 1
                )}
              </div>
              <div className="text-center">
                <p
                  className={cn(
                    "text-sm font-medium",
                    step.id <= currentStep ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground hidden lg:block">
                  {step.description}
                </p>
              </div>
            </button>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-4",
                  step.id < currentStep ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* Mobile view - simplified */}
      <div className="md:hidden">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-foreground">
            Krok {currentStep + 1} z {steps.length}
          </span>
          <span className="text-sm text-muted-foreground">
            {steps[currentStep]?.title}
          </span>
        </div>
        <div className="flex gap-1">
          {steps.map((step) => (
            <div
              key={step.id}
              className={cn(
                "h-1.5 flex-1 rounded-full transition-colors",
                step.id <= currentStep ? "bg-primary" : "bg-muted"
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
