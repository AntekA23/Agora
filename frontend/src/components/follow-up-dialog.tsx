"use client";

import * as React from "react";
import { Send, Loader2, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { InterpretResponse } from "@/types/assistant";

interface FollowUpDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: InterpretResponse | null;
  originalMessage: string;
  onSubmit: (answers: Record<string, string>) => void;
  isSubmitting?: boolean;
}

export function FollowUpDialog({
  open,
  onOpenChange,
  result,
  originalMessage,
  onSubmit,
  isSubmitting = false,
}: FollowUpDialogProps) {
  const [answers, setAnswers] = React.useState<Record<string, string>>({});
  const [currentIndex, setCurrentIndex] = React.useState(0);

  const questions = result?.follow_up_questions ?? [];
  const missingInfo = result?.missing_info ?? [];

  // Reset state when dialog opens
  React.useEffect(() => {
    if (open) {
      setAnswers({});
      setCurrentIndex(0);
    }
  }, [open]);

  const currentQuestion = questions[currentIndex];
  const currentKey = missingInfo[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  const handleAnswer = (value: string) => {
    if (!currentKey) return;
    setAnswers((prev) => ({ ...prev, [currentKey]: value }));
  };

  const handleNext = () => {
    if (isLastQuestion) {
      onSubmit(answers);
    } else {
      setCurrentIndex((i) => i + 1);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && answers[currentKey]) {
      handleNext();
    }
  };

  if (!result || questions.length === 0) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Potrzebuję więcej informacji</DialogTitle>
          <DialogDescription className="text-sm">
            {originalMessage && (
              <span className="block mt-1 text-foreground/70">
                &quot;{originalMessage}&quot;
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Progress indicator */}
          <div className="flex gap-1">
            {questions.map((_, i) => (
              <div
                key={i}
                className={cn(
                  "h-1 flex-1 rounded-full transition-colors",
                  i < currentIndex
                    ? "bg-primary"
                    : i === currentIndex
                    ? "bg-primary/50"
                    : "bg-muted"
                )}
              />
            ))}
          </div>

          {/* Current question */}
          <div className="space-y-3">
            <p className="text-sm font-medium">{currentQuestion}</p>
            <Input
              value={answers[currentKey] || ""}
              onChange={(e) => handleAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Wpisz odpowiedź..."
              disabled={isSubmitting}
              autoFocus
            />
          </div>
        </div>

        <div className="flex justify-between">
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            <X className="h-4 w-4 mr-1" />
            Anuluj
          </Button>
          <Button
            onClick={handleNext}
            disabled={!answers[currentKey] || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Send className="h-4 w-4 mr-1" />
            )}
            {isLastQuestion ? "Wykonaj" : "Dalej"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
