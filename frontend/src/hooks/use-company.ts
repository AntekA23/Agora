"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Company } from "@/types";

interface CompanyUpdate {
  name?: string;
  industry?: string;
  size?: string;
  settings?: {
    brand_voice?: string;
    target_audience?: string;
    language?: string;
  };
  enabled_agents?: string[];
}

export function useCompany() {
  return useQuery({
    queryKey: ["company"],
    queryFn: () => api.get<Company>("/companies/me"),
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CompanyUpdate) =>
      api.patch<Company>("/companies/me", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company"] });
    },
  });
}
