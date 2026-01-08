"use client";

import * as React from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useInterpretMessage } from "@/hooks/use-assistant";
import type { InterpretResponse } from "@/types/assistant";

interface CommandInputProps {
  onInterpret?: (result: InterpretResponse, message: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function CommandInput({
  onInterpret,
  placeholder = "Opisz czego potrzebujesz...",
  disabled = false,
  className,
}: CommandInputProps) {
  const [message, setMessage] = React.useState("");
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  const { mutate: interpret, isPending } = useInterpretMessage();

  const handleSubmit = React.useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();

      const trimmedMessage = message.trim();
      if (!trimmedMessage || isPending || disabled) return;

      interpret(
        { message: trimmedMessage },
        {
          onSuccess: (result) => {
            onInterpret?.(result, trimmedMessage);
          },
        }
      );
    },
    [message, interpret, isPending, disabled, onInterpret]
  );

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  // Auto-resize textarea
  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "relative flex items-end gap-2 rounded-xl border border-input bg-background p-2 shadow-sm transition-shadow focus-within:shadow-md focus-within:ring-2 focus-within:ring-ring/20",
        className
      )}
    >
      <textarea
        ref={inputRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isPending}
        rows={1}
        className={cn(
          "flex-1 resize-none bg-transparent px-2 py-2 text-sm placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed disabled:opacity-50",
          "min-h-[40px] max-h-[120px]"
        )}
      />
      <Button
        type="submit"
        size="icon"
        disabled={!message.trim() || isPending || disabled}
        className="shrink-0"
      >
        {isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
        <span className="sr-only">Wyslij</span>
      </Button>
    </form>
  );
}

/**
 * Example suggestions shown below the input.
 */
const EXAMPLE_SUGGESTIONS = [
  "Post na Instagram o nowym produkcie",
  "Faktura dla klienta ABC",
  "Analiza cashflow za ostatni miesiac",
  "Ogłoszenie o prace na stanowisko programisty",
];

interface CommandInputWithSuggestionsProps extends CommandInputProps {
  showSuggestions?: boolean;
}

export function CommandInputWithSuggestions({
  showSuggestions = true,
  ...props
}: CommandInputWithSuggestionsProps) {
  const [localMessage, setLocalMessage] = React.useState("");

  return (
    <div className="space-y-3">
      <CommandInput {...props} />

      {showSuggestions && !localMessage && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-muted-foreground">Np.:</span>
          {EXAMPLE_SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setLocalMessage(suggestion)}
              className="rounded-full border border-border bg-muted/50 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
