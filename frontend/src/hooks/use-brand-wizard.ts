"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BrandWizardComplete, WebsiteAnalyzeResponse } from "@/types";

interface WizardStatus {
  wizard_completed: boolean;
  has_knowledge: boolean;
}

interface KnowledgeResponse {
  knowledge: Record<string, unknown>;
}

export function useWizardStatus() {
  return useQuery({
    queryKey: ["wizard-status"],
    queryFn: () => api.get<WizardStatus>("/companies/me/wizard/status"),
  });
}

export function useAnalyzeWebsite() {
  return useMutation({
    mutationFn: (url: string) =>
      api.post<WebsiteAnalyzeResponse>("/companies/me/wizard/analyze-website", {
        url,
      }),
  });
}

export function useCompleteWizard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BrandWizardComplete) =>
      api.post<KnowledgeResponse>("/companies/me/wizard/complete", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company"] });
      queryClient.invalidateQueries({ queryKey: ["wizard-status"] });
    },
  });
}
