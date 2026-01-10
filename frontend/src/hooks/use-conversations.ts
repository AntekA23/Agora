"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_type: string;
  actions: Array<{ id: string; label: string; type: string }>;
  task_id?: string;
  task_status?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  messages: Message[];
  task_ids: string[];
  created_at: string;
  last_message_at: string | null;
}

export interface ConversationListItem {
  id: string;
  title: string;
  status: string;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationListItem[];
  total: number;
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
  tasks_created: string[];
}

// Hooks
export function useConversations(limit: number = 20) {
  return useQuery({
    queryKey: ["conversations", limit],
    queryFn: () =>
      api.get<ConversationListResponse>(`/conversations?limit=${limit}`),
    staleTime: 1000 * 60, // 1 minute
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => api.get<Conversation>(`/conversations/${conversationId}`),
    enabled: !!conversationId,
    staleTime: 0, // Always fetch fresh
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.post<Conversation>("/conversations", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (content: string) =>
      api.post<SendMessageResponse>(`/conversations/${conversationId}/messages`, {
        content,
      }),
    onSuccess: (data) => {
      // Update conversation cache with new messages
      queryClient.setQueryData<Conversation>(
        ["conversation", conversationId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            messages: [...old.messages, data.user_message, data.assistant_message],
            last_message_at: data.assistant_message.created_at,
          };
        }
      );
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useExecuteTasks(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post<SendMessageResponse>(`/conversations/${conversationId}/execute`, {}),
    onSuccess: async (data) => {
      // Update conversation cache
      queryClient.setQueryData<Conversation>(
        ["conversation", conversationId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            messages: [...old.messages, data.user_message, data.assistant_message],
            task_ids: [...old.task_ids, ...data.tasks_created],
            last_message_at: data.assistant_message.created_at,
          };
        }
      );
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      // Force immediate refetch of tasks list
      await queryClient.refetchQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) =>
      api.delete(`/conversations/${conversationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
