"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import {
  useAnalyzeWebsite,
  useCompleteSmartSetup,
  ExtractedInfo,
} from "@/hooks/use-onboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  ArrowLeft,
  Building2,
  Sparkles,
  CheckCircle,
  Loader2,
  Globe,
  Wand2,
  AlertCircle,
  Edit2,
} from "lucide-react";

const steps = [
  { id: 1, title: "Podstawy", icon: Building2 },
  { id: 2, title: "Weryfikacja", icon: Sparkles },
];

export default function SmartSetupPage() {
  const router = useRouter();
  const { user } = useAuth();
  const analyzeWebsite = useAnalyzeWebsite();
  const completeSetup = useCompleteSmartSetup();

  const [currentStep, setCurrentStep] = useState(1);
  const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Step 1 data
  const [formData, setFormData] = useState({
    companyName: "",
    description: "",
    websiteUrl: "",
  });

  // Step 2 data (editable extracted info)
  const [editableData, setEditableData] = useState({
    industry: "",
    targetAudience: "",
    brandVoice: "",
    productsServices: [] as string[],
    suggestedHashtags: [] as string[],
  });

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const updateEditableField = (field: string, value: string | string[]) => {
    setEditableData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAnalyze = async () => {
    try {
      const result = await analyzeWebsite.mutateAsync({
        url: formData.websiteUrl || undefined,
        company_name: formData.companyName,
        description: formData.description || undefined,
      });

      setExtractedInfo(result);
      setEditableData({
        industry: result.industry,
        targetAudience: result.target_audience,
        brandVoice: result.brand_voice,
        productsServices: result.products_services,
        suggestedHashtags: result.suggested_hashtags,
      });
      setCurrentStep(2);
    } catch {
      // Even on error, move to step 2 with empty data
      setCurrentStep(2);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setIsEditing(false);
    }
  };

  const handleFinish = async () => {
    await completeSetup.mutateAsync({
      company_name: formData.companyName,
      description: formData.description,
      website_url: formData.websiteUrl || undefined,
      industry: editableData.industry,
      target_audience: editableData.targetAudience,
      brand_voice: editableData.brandVoice,
      skip_analysis: true, // We already have the data
    });
    router.push("/dashboard");
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.companyName.length >= 2;
      case 2:
        return true; // Can always finish, data is optional
      default:
        return false;
    }
  };

  const getSourceBadge = () => {
    if (!extractedInfo) return null;

    switch (extractedInfo.source) {
      case "website":
        return (
          <Badge variant="default" className="gap-1">
            <Globe className="h-3 w-3" />
            Ze strony www
          </Badge>
        );
      case "ai_suggestion":
        return (
          <Badge variant="secondary" className="gap-1">
            <Wand2 className="h-3 w-3" />
            Sugestia AI
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Uzupelnij recznie
          </Badge>
        );
    }
  };

  const isLoading = analyzeWebsite.isPending || completeSetup.isPending;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-center items-center gap-4">
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
          <div className="flex justify-center gap-24 mt-2">
            {steps.map((step) => (
              <span
                key={step.id}
                className={`text-xs ${
                  currentStep >= step.id
                    ? "text-foreground"
                    : "text-muted-foreground"
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
              {currentStep === 1 &&
                `Witaj, ${user?.name?.split(" ")[0] || ""}!`}
              {currentStep === 2 && "Sprawdz dane Twojej firmy"}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 &&
                "Podaj podstawowe informacje - reszte wyciagniemy automatycznie."}
              {currentStep === 2 && (
                <span className="flex items-center gap-2">
                  {getSourceBadge()}
                  <span>Mozesz edytowac jesli cos sie nie zgadza.</span>
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Step 1: Basic Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="companyName">Nazwa firmy *</Label>
                  <Input
                    id="companyName"
                    value={formData.companyName}
                    onChange={(e) => updateField("companyName", e.target.value)}
                    placeholder="np. ABC Kosmetyki Sp. z o.o."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">
                    Czym sie zajmujecie? (opcjonalne)
                  </Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => updateField("description", e.target.value)}
                    placeholder="Krotki opis firmy w 1-2 zdaniach..."
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="websiteUrl">
                    Strona internetowa (opcjonalne)
                  </Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="websiteUrl"
                      value={formData.websiteUrl}
                      onChange={(e) => updateField("websiteUrl", e.target.value)}
                      placeholder="www.twoja-firma.pl"
                      className="pl-10"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Jesli podasz strone, automatycznie wyciagniemy wiecej
                    informacji o Twojej marce.
                  </p>
                </div>
              </div>
            )}

            {/* Step 2: Verification / Auto-fill */}
            {currentStep === 2 && (
              <div className="space-y-4">
                {extractedInfo && extractedInfo.confidence_score > 0.2 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-2 text-sm">
                      <Sparkles className="h-4 w-4 text-primary" />
                      <span>
                        Pewnosc analizy:{" "}
                        {Math.round(extractedInfo.confidence_score * 100)}%
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      <Edit2 className="h-4 w-4 mr-1" />
                      {isEditing ? "Gotowe" : "Edytuj"}
                    </Button>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="industry">Branza</Label>
                  {isEditing || !editableData.industry ? (
                    <Input
                      id="industry"
                      value={editableData.industry}
                      onChange={(e) =>
                        updateEditableField("industry", e.target.value)
                      }
                      placeholder="np. e-commerce, uslugi IT, gastronomia..."
                    />
                  ) : (
                    <div className="p-3 rounded-lg bg-muted/50 text-sm">
                      {editableData.industry}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="targetAudience">Grupa docelowa</Label>
                  {isEditing || !editableData.targetAudience ? (
                    <Textarea
                      id="targetAudience"
                      value={editableData.targetAudience}
                      onChange={(e) =>
                        updateEditableField("targetAudience", e.target.value)
                      }
                      placeholder="Opisz swojego idealnego klienta..."
                      rows={3}
                    />
                  ) : (
                    <div className="p-3 rounded-lg bg-muted/50 text-sm whitespace-pre-wrap">
                      {editableData.targetAudience}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="brandVoice">Ton komunikacji</Label>
                  {isEditing || !editableData.brandVoice ? (
                    <>
                      <Input
                        id="brandVoice"
                        value={editableData.brandVoice}
                        onChange={(e) =>
                          updateEditableField("brandVoice", e.target.value)
                        }
                        placeholder="np. profesjonalny, przyjazny..."
                      />
                      <div className="flex flex-wrap gap-2 mt-2">
                        {[
                          "profesjonalny",
                          "przyjazny",
                          "ekspertowy",
                          "casualowy",
                        ].map((tone) => (
                          <Button
                            key={tone}
                            variant="outline"
                            size="sm"
                            type="button"
                            onClick={() =>
                              updateEditableField(
                                "brandVoice",
                                editableData.brandVoice
                                  ? `${editableData.brandVoice}, ${tone}`
                                  : tone
                              )
                            }
                          >
                            {tone}
                          </Button>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="p-3 rounded-lg bg-muted/50 text-sm">
                      {editableData.brandVoice}
                    </div>
                  )}
                </div>

                {editableData.suggestedHashtags.length > 0 && (
                  <div className="space-y-2">
                    <Label>Sugerowane hashtagi</Label>
                    <div className="flex flex-wrap gap-2">
                      {editableData.suggestedHashtags.map((tag, i) => (
                        <Badge key={i} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {editableData.productsServices.length > 0 && (
                  <div className="space-y-2">
                    <Label>Wykryte produkty/uslugi</Label>
                    <div className="flex flex-wrap gap-2">
                      {editableData.productsServices.map((item, i) => (
                        <Badge key={i} variant="outline">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between pt-4">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 1 || isLoading}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Wstecz
              </Button>

              {currentStep === 1 ? (
                <Button
                  onClick={handleAnalyze}
                  disabled={!canProceed() || isLoading}
                >
                  {analyzeWebsite.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Analizuje...
                    </>
                  ) : (
                    <>
                      {formData.websiteUrl ? "Analizuj strone" : "Dalej"}
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  onClick={handleFinish}
                  disabled={!canProceed() || isLoading}
                >
                  {completeSetup.isPending ? (
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
                disabled={isLoading}
              >
                Pomin i skonfiguruj pozniej
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info about Brand Wizard */}
        <p className="text-center text-xs text-muted-foreground mt-4">
          Potrzebujesz wiecej opcji? Uzyj{" "}
          <span className="font-medium">Kreatora Marki</span> w Ustawieniach.
        </p>
      </div>
    </div>
  );
}
