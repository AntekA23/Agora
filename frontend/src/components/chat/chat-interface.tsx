"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  useConversation,
  useSendMessage,
  useExecuteTasks,
} from "@/hooks/use-conversations";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatMessage } from "./chat-message";
import {
  Send,
  Loader2,
  Bot,
  Sparkles,
} from "lucide-react";

interface ChatInterfaceProps {
  conversationId: string;
}

export function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const router = useRouter();
  const [input, setInput] = React.useState("");
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const { data: conversation, isLoading } = useConversation(conversationId);
  const sendMessage = useSendMessage(conversationId);
  const executeTasks = useExecuteTasks(conversationId);

  // Auto-scroll to bottom on new messages
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages]);

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || sendMessage.isPending) return;

    const message = input.trim();
    setInput("");
    await sendMessage.mutateAsync(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAction = async (actionId: string) => {
    if (actionId === "execute" || actionId === "confirm") {
      await executeTasks.mutateAsync();
    } else if (actionId === "view_tasks") {
      router.push("/tasks");
    } else if (actionId === "modify") {
      // Focus input for modification
      textareaRef.current?.focus();
    } else if (actionId === "cancel") {
      // User wants to cancel
      await sendMessage.mutateAsync("[Anuluj]");
    } else if (actionId === "undo") {
      // User wants to undo last action
      await sendMessage.mutateAsync("[Cofnij]");
    } else if (actionId === "use_defaults") {
      // User wants to skip recommended questions - use defaults
      await sendMessage.mutateAsync("[Użyj domyślnych]");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const messages = conversation?.messages ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="p-4 rounded-full bg-primary/10">
              <Bot className="h-12 w-12 text-primary" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Cześć! Jestem Agora</h3>
              <p className="text-muted-foreground max-w-md">
                Powiedz mi czego potrzebujesz, a przygotuję to dla Ciebie.
                Mogę tworzyć posty, teksty reklamowe, faktury i wiele więcej.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              <SuggestionChip
                onClick={() => setInput("Stwórz post na Instagram o nowym produkcie")}
              >
                <Sparkles className="h-3 w-3" />
                Post na Instagram
              </SuggestionChip>
              <SuggestionChip
                onClick={() => setInput("Napisz tekst reklamowy na promocję -20%")}
              >
                <Sparkles className="h-3 w-3" />
                Tekst reklamowy
              </SuggestionChip>
              <SuggestionChip
                onClick={() => setInput("Przygotuj kampanię na nowy produkt")}
              >
                <Sparkles className="h-3 w-3" />
                Kampania marketingowa
              </SuggestionChip>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onAction={handleAction}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t p-4 bg-background">
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Napisz wiadomość..."
              className="min-h-[56px] max-h-[200px] pr-14 resize-none"
              rows={1}
              disabled={sendMessage.isPending}
            />
            <Button
              size="icon"
              className="absolute right-2 bottom-2"
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending}
            >
              {sendMessage.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            Naciśnij Enter aby wysłać, Shift+Enter dla nowej linii
          </p>
        </div>
      </div>
    </div>
  );
}

interface SuggestionChipProps {
  children: React.ReactNode;
  onClick: () => void;
}

function SuggestionChip({ children, onClick }: SuggestionChipProps) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-muted hover:bg-muted/80 transition-colors"
    >
      {children}
    </button>
  );
}
