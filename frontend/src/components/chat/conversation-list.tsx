"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
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

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) {
      return date.toLocaleTimeString("pl-PL", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffDays === 1) {
      return "Wczoraj";
    } else if (diffDays < 7) {
      return `${diffDays} dni temu`;
    } else {
      return date.toLocaleDateString("pl-PL", {
        day: "numeric",
        month: "short",
      });
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
      <ScrollArea className="flex-1">
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
                  "group flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors",
                  selectedId === conv.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-muted"
                )}
                onClick={() => onSelect(conv.id)}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{conv.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(conv.last_message_at || conv.created_at)}
                    {conv.message_count > 0 && ` • ${conv.message_count} wiad.`}
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={(e) => handleDelete(conv.id, e as unknown as React.MouseEvent)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Usuń
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
