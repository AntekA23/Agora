"use client";

import * as React from "react";
import { cn, formatRelativeDatePL } from "@/lib/utils";
import {
  useConversations,
  useCreateConversation,
  useDeleteConversation,
} from "@/hooks/use-conversations";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Plus,
  MessageSquare,
  MoreVertical,
  Trash2,
  Loader2,
} from "lucide-react";

interface ConversationListProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ConversationList({ selectedId, onSelect }: ConversationListProps) {
  const { data, isLoading } = useConversations();
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();

  const handleNewConversation = async () => {
    const result = await createConversation.mutateAsync();
    onSelect(result.id);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteConversation.mutateAsync(id);
    if (selectedId === id) {
      // Select another conversation or create new
      const remaining = data?.conversations.filter((c) => c.id !== id);
      if (remaining && remaining.length > 0) {
        onSelect(remaining[0].id);
      } else {
        handleNewConversation();
      }
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* New conversation button */}
      <div className="p-3 border-b">
        <Button
          onClick={handleNewConversation}
          className="w-full justify-start gap-2"
          disabled={createConversation.isPending}
        >
          {createConversation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Nowa rozmowa
        </Button>
      </div>

      {/* Conversations list */}
      <ScrollArea className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : data?.conversations.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            Brak rozmów
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {data?.conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  "group flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors overflow-hidden",
                  selectedId === conv.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-muted"
                )}
                onClick={() => onSelect(conv.id)}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0 overflow-hidden">
                  <p className="text-sm font-medium truncate">{conv.title}</p>
                  <p className="text-xs text-muted-foreground truncate">
                    {formatRelativeDatePL(conv.last_message_at || conv.created_at)}
                    {conv.message_count > 0 && ` • ${conv.message_count}`}
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 shrink-0 text-muted-foreground hover:text-foreground hover:bg-muted"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreVertical className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" side="right">
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={(e) => handleDelete(conv.id, e as unknown as React.MouseEvent)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Usuń rozmowę
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
