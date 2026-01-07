"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Task } from "@/types/task";
import type { InvoiceTaskInput, CashflowTaskInput } from "@/types/finance";

export function useCreateInvoiceTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InvoiceTaskInput) =>
      api.post<Task>("/agents/finance/invoice", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useCreateCashflowTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CashflowTaskInput) =>
      api.post<Task>("/agents/finance/cashflow", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
