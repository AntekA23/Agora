"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/brand-setup/progress-bar";
import { WizardNavigation } from "@/components/brand-setup/wizard-navigation";
import { StepQuickStart } from "@/components/brand-setup/step-quick-start";
import { StepCompanyInfo, type CompanyInfoData } from "@/components/brand-setup/step-company-info";
import { StepMarket, type MarketData, type ProductItem } from "@/components/brand-setup/step-market";
import { StepCommunication, type CommunicationData } from "@/components/brand-setup/step-communication";
import { StepSummary } from "@/components/brand-setup/step-summary";
import { X, Sparkles } from "lucide-react";

const STEPS = [
  { id: 0, title: "Quick Start", description: "Analiza strony" },
  { id: 1, title: "Firma", description: "Podstawowe informacje" },
  { id: 2, title: "Rynek", description: "Klienci i oferta" },
  { id: 3, title: "Komunikacja", description: "Styl i ton" },
  { id: 4, title: "Podsumowanie", description: "Przegląd danych" },
];

const initialCompanyInfo: CompanyInfoData = {
  name: "",
  industry: "",
  description: "",
  website: "",
  founded_year: null,
  location: "",
  mission: "",
  vision: "",
  values: [],
};

const initialMarket: MarketData = {
  target_audience: "",
  audience_age_from: null,
  audience_age_to: null,
  audience_locations: [],
  audience_interests: [],
  products: [],
  services: [],
  unique_selling_points: [],
};

const initialCommunication: CommunicationData = {
  tone: "",
  voice_description: "",
  formality_level: 3,
  emoji_usage: "moderate",
  brand_values: [],
  words_to_use: [],
  words_to_avoid: [],
  preferred_formats: [],
  content_themes: [],
};

interface WebsiteAnalyzeResponse {
  success: boolean;
  data: {
    name?: string;
    description?: string;
    industry?: string;
    products?: { name: string; description: string }[];
    services?: { name: string; description: string }[];
  };
}

export default function BrandSetupPage() {
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [currentStep, setCurrentStep] = useState(0);
  const [companyInfo, setCompanyInfo] = useState<CompanyInfoData>(initialCompanyInfo);
  const [market, setMarket] = useState<MarketData>(initialMarket);
  const [communication, setCommunication] = useState<CommunicationData>(initialCommunication);

  // Analyze website mutation
  const analyzeWebsite = useMutation({
    mutationFn: (url: string) =>
      api.post<WebsiteAnalyzeResponse>("/companies/me/wizard/analyze-website", { url }),
    onSuccess: (response) => {
      if (response.success && response.data) {
        const data = response.data;
        // Pre-fill company info
        setCompanyInfo((prev) => ({
          ...prev,
          name: data.name || prev.name,
          description: data.description || prev.description,
          industry: data.industry || prev.industry,
          website: prev.website,
        }));
        // Pre-fill products and services if available
        if (data.products && data.products.length > 0) {
          setMarket((prev) => ({
            ...prev,
            products: data.products as ProductItem[],
          }));
        }
        if (data.services && data.services.length > 0) {
          setMarket((prev) => ({
            ...prev,
            services: data.services as ProductItem[],
          }));
        }
        toast({
          title: "Analiza zakonczona",
          description: "Dane z strony zostaly załadowane do formularza",
        });
      }
      setCurrentStep(1);
    },
    onError: () => {
      toast({
        title: "Blad analizy",
        description: "Nie udalo sie przeanalizowac strony. Wypelnij dane recznie.",
        variant: "destructive",
      });
      setCurrentStep(1);
    },
  });

  // Complete wizard mutation
  const completeWizard = useMutation({
    mutationFn: async () => {
      // Transform data to match backend schema
      const payload = {
        step1: {
          company_description: companyInfo.description,
          founded_year: companyInfo.founded_year,
          location: companyInfo.location,
          website: companyInfo.website,
        },
        step2: {
          mission: companyInfo.mission,
          vision: companyInfo.vision,
          values: companyInfo.values,
          personality_traits: communication.brand_values,
          unique_value_proposition: market.unique_selling_points.join(", "),
        },
        step3: {
          description: market.target_audience,
          age_from: market.audience_age_from,
          age_to: market.audience_age_to,
          gender: "all",
          locations: market.audience_locations,
          interests: market.audience_interests,
          pain_points: [],
          goals: [],
          where_they_are: [],
        },
        step4: {
          products: market.products.map((p) => ({
            name: p.name,
            description: p.description,
            price: null,
            category: "",
            features: [],
            unique_selling_points: [],
          })),
          services: market.services.map((s) => ({
            name: s.name,
            description: s.description,
            price_from: null,
            price_to: null,
            duration: "",
            benefits: [],
          })),
          price_positioning: "mid_range",
        },
        step5: {
          competitors: [],
          market_position: "",
          key_differentiators: market.unique_selling_points,
        },
        step6: {
          formality_level: communication.formality_level,
          emoji_usage: communication.emoji_usage,
          words_to_use: communication.words_to_use,
          words_to_avoid: communication.words_to_avoid,
          example_phrases: [],
        },
        step7: {
          themes: communication.content_themes,
          hashtag_style: "mixed",
          branded_hashtags: [],
          post_frequency: "",
          preferred_formats: communication.preferred_formats,
          content_goals: [],
        },
        // Also update company name and industry
        company_name: companyInfo.name,
        company_industry: companyInfo.industry,
      };
      return api.post("/companies/me/wizard/complete", payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company"] });
      queryClient.invalidateQueries({ queryKey: ["wizard-status"] });
      toast({
        title: "Kreator zakonczony!",
        description: "Dane firmy zostaly zapisane. Mozesz teraz korzystac z Agora.",
      });
      router.push("/");
    },
    onError: (error) => {
      toast({
        title: "Blad zapisu",
        description: "Nie udalo sie zapisac danych. Sprobuj ponownie.",
        variant: "destructive",
      });
      console.error("Wizard complete error:", error);
    },
  });

  const handleAnalyzeWebsite = async (url: string) => {
    setCompanyInfo((prev) => ({ ...prev, website: url }));
    await analyzeWebsite.mutateAsync(url);
  };

  const handleSkipQuickStart = () => {
    setCurrentStep(1);
  };

  const goNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const goBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step: number) => {
    if (step <= currentStep || step === currentStep + 1) {
      setCurrentStep(step);
    }
  };

  const handleComplete = () => {
    completeWizard.mutate();
  };

  const handleSkipWizard = () => {
    router.push("/");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            <span className="font-bold text-xl text-foreground">Agora</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkipWizard}
            className="text-muted-foreground"
          >
            <X className="w-4 h-4 mr-1" />
            Pomin
          </Button>
        </div>
      </header>

      {/* Progress bar - hide on step 0 */}
      {currentStep > 0 && (
        <div className="border-b border-border bg-background py-4">
          <div className="max-w-4xl mx-auto px-4">
            <ProgressBar
              steps={STEPS.slice(1)} // Skip Quick Start in progress
              currentStep={currentStep - 1}
              onStepClick={(step) => goToStep(step + 1)}
            />
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 py-8 px-4 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {currentStep === 0 && (
            <StepQuickStart
              onAnalyze={handleAnalyzeWebsite}
              onSkip={handleSkipQuickStart}
              isAnalyzing={analyzeWebsite.isPending}
            />
          )}
          {currentStep === 1 && (
            <StepCompanyInfo data={companyInfo} onChange={setCompanyInfo} />
          )}
          {currentStep === 2 && (
            <StepMarket data={market} onChange={setMarket} />
          )}
          {currentStep === 3 && (
            <StepCommunication data={communication} onChange={setCommunication} />
          )}
          {currentStep === 4 && (
            <StepSummary
              companyInfo={companyInfo}
              market={market}
              communication={communication}
              onEditStep={goToStep}
            />
          )}
        </div>
      </main>

      {/* Footer navigation - hide on step 0 */}
      {currentStep > 0 && (
        <footer className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky bottom-0">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <WizardNavigation
              currentStep={currentStep - 1}
              totalSteps={STEPS.length - 1}
              onBack={goBack}
              onNext={goNext}
              onComplete={handleComplete}
              isLoading={completeWizard.isPending}
              completeLabel="Zapisz i rozpocznij"
            />
          </div>
        </footer>
      )}
    </div>
  );
}
