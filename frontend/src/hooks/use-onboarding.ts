"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface AnalyzeWebsiteRequest {
  url?: string;
  company_name?: string;
  description?: string;
}

export interface ExtractedInfo {
  company_name: string;
  industry: string;
  description: string;
  target_audience: string;
  brand_voice: string;
  products_services: string[];
  unique_selling_points: string[];
  suggested_hashtags: string[];
  confidence_score: number;
  source: "website" | "ai_suggestion" | "empty";
}

export interface SmartSetupRequest {
  company_name: string;
  description?: string;
  website_url?: string;
  industry?: string;
  target_audience?: string;
  brand_voice?: string;
  skip_analysis?: boolean;
}

export interface SmartSetupResponse {
  success: boolean;
  message: string;
  extracted_info?: ExtractedInfo;
  company_updated: boolean;
}

export interface OnboardingStatus {
  completed: boolean;
  reason?: string;
  has_industry?: boolean;
  has_brand_settings?: boolean;
  company_name?: string;
}

// Hooks
export function useOnboardingStatus() {
  return useQuery({
    queryKey: ["onboarding", "status"],
    queryFn: () => api.get<OnboardingStatus>("/onboarding/status"),
  });
}

export function useAnalyzeWebsite() {
  return useMutation({
    mutationFn: (data: AnalyzeWebsiteRequest) =>
      api.post<ExtractedInfo>("/onboarding/analyze", data),
  });
}

export function useCompleteSmartSetup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SmartSetupRequest) =>
      api.post<SmartSetupResponse>("/onboarding/complete", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding"] });
      queryClient.invalidateQueries({ queryKey: ["company"] });
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}
