"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useUpdateCompany } from "@/hooks/use-company";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  ArrowRight,
  ArrowLeft,
  Building2,
  Target,
  Sparkles,
  CheckCircle,
  Loader2
} from "lucide-react";

const steps = [
  { id: 1, title: "Twoja firma", icon: Building2 },
  { id: 2, title: "Grupa docelowa", icon: Target },
  { id: 3, title: "Styl komunikacji", icon: Sparkles },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const updateCompany = useUpdateCompany();

  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    industry: "",
    size: "small",
    targetAudience: "",
    brandVoice: "",
  });

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFinish = async () => {
    await updateCompany.mutateAsync({
      industry: formData.industry,
      size: formData.size,
      settings: {
        brand_voice: formData.brandVoice,
        target_audience: formData.targetAudience,
        language: "pl",
      },
    });
    router.push("/dashboard");
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.industry.length > 0;
      case 2:
        return formData.targetAudience.length > 0;
      case 3:
        return formData.brandVoice.length > 0;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                    currentStep >= step.id
                      ? "bg-primary border-primary text-primary-foreground"
                      : "border-muted-foreground text-muted-foreground"
                  }`}
                >
                  {currentStep > step.id ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`w-24 h-0.5 mx-2 transition-colors ${
                      currentStep > step.id ? "bg-primary" : "bg-muted"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2">
            {steps.map((step) => (
              <span
                key={step.id}
                className={`text-xs ${
                  currentStep >= step.id ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {step.title}
              </span>
            ))}
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {currentStep === 1 && `Witaj, ${user?.name?.split(" ")[0] || ""}!`}
              {currentStep === 2 && "Kto jest Twoim klientem?"}
              {currentStep === 3 && "Jak komunikuje sie Twoja marka?"}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 && "Opowiedz nam o swojej firmie, zebysmy mogli lepiej dostosowac agentow AI."}
              {currentStep === 2 && "Zdefiniuj swoja grupe docelowa - to pomoze agentom tworzyc trafniejszy content."}
              {currentStep === 3 && "Okresl ton komunikacji - agenci beda go naladowac w kazdym zadaniu."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Step 1: Company Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="industry">Branza</Label>
                  <Input
                    id="industry"
                    value={formData.industry}
                    onChange={(e) => updateField("industry", e.target.value)}
                    placeholder="np. e-commerce, uslugi IT, gastronomia..."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="size">Wielkosc firmy</Label>
                  <Select
                    id="size"
                    value={formData.size}
                    onChange={(e) => updateField("size", e.target.value)}
                  >
                    <option value="micro">Mikro (1-9 pracownikow)</option>
                    <option value="small">Mala (10-49 pracownikow)</option>
                    <option value="medium">Srednia (50-249 pracownikow)</option>
                  </Select>
                </div>
              </div>
            )}

            {/* Step 2: Target Audience */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="targetAudience">Opis grupy docelowej</Label>
                  <Textarea
                    id="targetAudience"
                    value={formData.targetAudience}
                    onChange={(e) => updateField("targetAudience", e.target.value)}
                    placeholder="Opisz swojego idealnego klienta, np.:
- Wiek: 25-40 lat
- Plec: Kobiety
- Zainteresowania: Zdrowy styl zycia, fitness
- Problem: Brak czasu na gotowanie
- Gdzie szukaja informacji: Instagram, TikTok"
                    rows={6}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Im dokladniej opiszesz, tym lepiej agenci dostosuja komunikacje.
                </p>
              </div>
            )}

            {/* Step 3: Brand Voice */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="brandVoice">Ton komunikacji marki</Label>
                  <Textarea
                    id="brandVoice"
                    value={formData.brandVoice}
                    onChange={(e) => updateField("brandVoice", e.target.value)}
                    placeholder="Opisz jak powinna brzmiec Twoja marka, np.:
- Profesjonalny ale przyjazny
- Unikamy korporacyjnego jezyka
- Uzywamy emoji z umiarem
- Zwracamy sie do klienta per 'Ty'
- Lubimy zartowac, ale nie przesadzamy"
                    rows={6}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Przyklady tonow:</Label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "Profesjonalny",
                      "Przyjazny",
                      "Ekspertowy",
                      "Casualowy",
                      "Inspirujacy",
                      "Humorystyczny",
                    ].map((tone) => (
                      <Button
                        key={tone}
                        variant="outline"
                        size="sm"
                        type="button"
                        onClick={() =>
                          updateField(
                            "brandVoice",
                            formData.brandVoice
                              ? `${formData.brandVoice}, ${tone.toLowerCase()}`
                              : tone
                          )
                        }
                      >
                        {tone}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between pt-4">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 1}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Wstecz
              </Button>

              {currentStep < 3 ? (
                <Button onClick={handleNext} disabled={!canProceed()}>
                  Dalej
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={handleFinish}
                  disabled={!canProceed() || updateCompany.isPending}
                >
                  {updateCompany.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Zapisywanie...
                    </>
                  ) : (
                    <>
                      Rozpocznij prace
                      <Sparkles className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* Skip option */}
            <div className="text-center">
              <Button
                variant="link"
                className="text-muted-foreground"
                onClick={() => router.push("/dashboard")}
              >
                Pomin i skonfiguruj pozniej
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
