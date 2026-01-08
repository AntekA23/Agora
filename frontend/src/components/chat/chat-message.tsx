"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  User,
  Bot,
  CheckCircle,
  Loader2,
  AlertCircle,
  Copy,
  Check,
} from "lucide-react";
import type { Message } from "@/hooks/use-conversations";

interface ChatMessageProps {
  message: Message;
  onAction?: (actionId: string) => void;
}

export function ChatMessage({ message, onAction }: ChatMessageProps) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTaskStatusIcon = () => {
    switch (message.task_status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />;
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 p-4 rounded-lg",
        isUser
          ? "bg-primary/5 ml-12"
          : "bg-muted/50 mr-12"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 space-y-2 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">
            {isUser ? "Ty" : "Agora"}
          </span>
          <span className="text-xs text-muted-foreground">
            {new Date(message.created_at).toLocaleTimeString("pl-PL", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {/* Message content with line breaks preserved */}
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>

        {/* Task status indicator */}
        {message.task_id && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {getTaskStatusIcon()}
            <span>
              {message.task_status === "completed"
                ? "Zadanie zakończone"
                : message.task_status === "failed"
                ? "Błąd zadania"
                : "Przetwarzanie..."}
            </span>
          </div>
        )}

        {/* Action buttons */}
        {isAssistant && message.actions && message.actions.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {message.actions.map((action) => (
              <Button
                key={action.id}
                size="sm"
                variant={action.type === "primary" ? "default" : "outline"}
                onClick={() => onAction?.(action.id)}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* Copy button for assistant messages */}
        {isAssistant && message.content.length > 50 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-muted-foreground"
            onClick={handleCopy}
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 mr-1" />
                Skopiowano
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Kopiuj
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
