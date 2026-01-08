"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  useConversations,
  useCreateConversation,
} from "@/hooks/use-conversations";
import { ChatInterface, ConversationList } from "@/components/chat";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Menu,
  MessageSquare,
  Loader2,
} from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedId, setSelectedId] = React.useState<string | null>(
    searchParams.get("id")
  );
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const { data: conversations, isLoading } = useConversations();
  const createConversation = useCreateConversation();

  // Auto-create or select conversation on mount
  React.useEffect(() => {
    const initConversation = async () => {
      if (selectedId) return;

      if (!isLoading) {
        if (conversations?.conversations.length === 0) {
          // Create new conversation
          const result = await createConversation.mutateAsync();
          setSelectedId(result.id);
          router.replace(`/chat?id=${result.id}`);
        } else if (conversations?.conversations[0]) {
          // Select most recent
          setSelectedId(conversations.conversations[0].id);
          router.replace(`/chat?id=${conversations.conversations[0].id}`);
        }
      }
    };

    initConversation();
  }, [isLoading, conversations, selectedId]);

  const handleSelectConversation = (id: string) => {
    setSelectedId(id);
    router.replace(`/chat?id=${id}`);
    setSidebarOpen(false);
  };

  if (isLoading && !selectedId) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-120px)] -mx-6 -mt-6">
      {/* Desktop sidebar */}
      <div className="hidden md:flex w-64 border-r bg-muted/30 flex-col">
        <ConversationList
          selectedId={selectedId}
          onSelect={handleSelectConversation}
        />
      </div>

      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="p-0 w-72">
          <ConversationList
            selectedId={selectedId}
            onSelect={handleSelectConversation}
          />
        </SheetContent>
      </Sheet>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <div className="md:hidden flex items-center gap-2 p-3 border-b">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <span className="font-medium">Rozmowy</span>
          </div>
        </div>

        {/* Chat interface */}
        {selectedId ? (
          <ChatInterface conversationId={selectedId} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Wybierz rozmowę lub utwórz nową</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
