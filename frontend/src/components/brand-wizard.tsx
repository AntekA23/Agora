"use client";

import { useState } from "react";
import { useAnalyzeWebsite, useCompleteWizard } from "@/hooks/use-brand-wizard";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Globe,
  Building2,
  Target,
  Users,
  Package,
  Trophy,
  MessageSquare,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";
import type {
  BrandWizardStep1,
  BrandWizardStep2,
  BrandWizardStep3,
  BrandWizardStep4,
  BrandWizardStep5,
  BrandWizardStep6,
  BrandWizardStep7,
  ProductInput,
  ServiceInput,
  CompetitorInput,
} from "@/types";

interface BrandWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

const STEPS = [
  { id: 0, title: "Analiza strony", icon: Globe, optional: true },
  { id: 1, title: "Podstawowe informacje", icon: Building2 },
  { id: 2, title: "Tozsamosc marki", icon: Target },
  { id: 3, title: "Grupa docelowa", icon: Users },
  { id: 4, title: "Produkty i uslugi", icon: Package },
  { id: 5, title: "Konkurencja", icon: Trophy },
  { id: 6, title: "Styl komunikacji", icon: MessageSquare },
  { id: 7, title: "Preferencje tresci", icon: Sparkles },
];

const initialStep1: BrandWizardStep1 = {
  company_description: "",
  founded_year: null,
  location: "",
  website: "",
};

const initialStep2: BrandWizardStep2 = {
  mission: "",
  vision: "",
  values: [],
  personality_traits: [],
  unique_value_proposition: "",
};

const initialStep3: BrandWizardStep3 = {
  description: "",
  age_from: null,
  age_to: null,
  gender: "all",
  locations: [],
  interests: [],
  pain_points: [],
  goals: [],
  where_they_are: [],
};

const initialStep4: BrandWizardStep4 = {
  products: [],
  services: [],
  price_positioning: "mid_range",
};

const initialStep5: BrandWizardStep5 = {
  competitors: [],
  market_position: "",
  key_differentiators: [],
};

const initialStep6: BrandWizardStep6 = {
  formality_level: 3,
  emoji_usage: "moderate",
  words_to_use: [],
  words_to_avoid: [],
  example_phrases: [],
};

const initialStep7: BrandWizardStep7 = {
  themes: [],
  hashtag_style: "mixed",
  branded_hashtags: [],
  post_frequency: "",
  preferred_formats: [],
  content_goals: [],
};

export function BrandWizard({ open, onOpenChange, onComplete }: BrandWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [step1, setStep1] = useState<BrandWizardStep1>(initialStep1);
  const [step2, setStep2] = useState<BrandWizardStep2>(initialStep2);
  const [step3, setStep3] = useState<BrandWizardStep3>(initialStep3);
  const [step4, setStep4] = useState<BrandWizardStep4>(initialStep4);
  const [step5, setStep5] = useState<BrandWizardStep5>(initialStep5);
  const [step6, setStep6] = useState<BrandWizardStep6>(initialStep6);
  const [step7, setStep7] = useState<BrandWizardStep7>(initialStep7);

  const analyzeWebsite = useAnalyzeWebsite();
  const completeWizard = useCompleteWizard();

  const handleAnalyzeWebsite = async () => {
    if (!websiteUrl) return;

    try {
      const result = await analyzeWebsite.mutateAsync(websiteUrl);
      if (result.success && result.data) {
        const data = result.data as Record<string, string>;
        // Pre-fill data from website analysis
        setStep1((prev) => ({
          ...prev,
          website: websiteUrl,
          company_description: data.description || prev.company_description,
        }));
        if (data.mission) {
          setStep2((prev) => ({ ...prev, mission: data.mission || prev.mission }));
        }
        if (data.products) {
          // Handle products if returned
        }
      }
      setCurrentStep(1);
    } catch {
      // Continue to step 1 even if analysis fails
      setCurrentStep(1);
    }
  };

  const handleComplete = async () => {
    try {
      await completeWizard.mutateAsync({
        step1,
        step2,
        step3,
        step4,
        step5,
        step6,
        step7,
      });
      onComplete();
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  };

  const goNext = () => {
    if (currentStep < 7) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const goBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipWebsiteAnalysis = () => {
    setCurrentStep(1);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl w-[90vw] max-h-[85vh] overflow-hidden flex flex-col" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {(() => {
              const StepIcon = STEPS[currentStep].icon;
              return <StepIcon className="h-5 w-5" />;
            })()}
            {STEPS[currentStep].title}
            {STEPS[currentStep].optional && (
              <Badge variant="secondary" className="ml-2">Opcjonalne</Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            Krok {currentStep + 1} z {STEPS.length}
          </DialogDescription>
        </DialogHeader>

        {/* Progress bar */}
        <div className="flex gap-1 mb-4">
          {STEPS.map((step, idx) => (
            <div
              key={step.id}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                idx <= currentStep ? "bg-primary" : "bg-muted"
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="flex-1 overflow-y-auto pr-2 -mr-2">
          {currentStep === 0 && (
            <Step0WebsiteAnalysis
              url={websiteUrl}
              setUrl={setWebsiteUrl}
              isLoading={analyzeWebsite.isPending}
              onAnalyze={handleAnalyzeWebsite}
              onSkip={skipWebsiteAnalysis}
            />
          )}
          {currentStep === 1 && (
            <Step1BasicInfo data={step1} onChange={setStep1} />
          )}
          {currentStep === 2 && (
            <Step2BrandIdentity data={step2} onChange={setStep2} />
          )}
          {currentStep === 3 && (
            <Step3TargetAudience data={step3} onChange={setStep3} />
          )}
          {currentStep === 4 && (
            <Step4ProductsServices data={step4} onChange={setStep4} />
          )}
          {currentStep === 5 && (
            <Step5Competition data={step5} onChange={setStep5} />
          )}
          {currentStep === 6 && (
            <Step6CommunicationStyle data={step6} onChange={setStep6} />
          )}
          {currentStep === 7 && (
            <Step7ContentPreferences data={step7} onChange={setStep7} />
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-4 border-t border-border mt-4">
          <Button
            variant="outline"
            onClick={goBack}
            disabled={currentStep === 0}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Wstecz
          </Button>
          {currentStep < 7 ? (
            <Button onClick={goNext} disabled={currentStep === 0}>
              Dalej
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleComplete} disabled={completeWizard.isPending}>
              {completeWizard.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Zapisywanie...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Zakoncz
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// STEP 0: Website Analysis
// ============================================================================

function Step0WebsiteAnalysis({
  url,
  setUrl,
  isLoading,
  onAnalyze,
  onSkip,
}: {
  url: string;
  setUrl: (url: string) => void;
  isLoading: boolean;
  onAnalyze: () => void;
  onSkip: () => void;
}) {
  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Podaj adres strony internetowej swojej firmy, a automatycznie
        sprobujemy wyciagnac podstawowe informacje. Ten krok jest opcjonalny.
      </p>

      <div className="space-y-2">
        <Label htmlFor="website-url">Adres strony WWW</Label>
        <div className="flex gap-2">
          <Input
            id="website-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://twoja-firma.pl"
            type="url"
          />
          <Button onClick={onAnalyze} disabled={!url || isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Analizuj"
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Wykorzystamy Tavily AI do analizy zawartosci strony
        </p>
      </div>

      <div className="flex justify-center">
        <Button variant="ghost" onClick={onSkip}>
          Pomin ten krok
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// STEP 1: Basic Info
// ============================================================================

function Step1BasicInfo({
  data,
  onChange,
}: {
  data: BrandWizardStep1;
  onChange: (data: BrandWizardStep1) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="company-description">Opis firmy</Label>
        <Textarea
          id="company-description"
          value={data.company_description}
          onChange={(e) =>
            onChange({ ...data, company_description: e.target.value })
          }
          placeholder="Krotki opis tego, czym zajmuje sie Twoja firma..."
          rows={4}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="founded-year">Rok zalozenia</Label>
          <Input
            id="founded-year"
            type="number"
            value={data.founded_year || ""}
            onChange={(e) =>
              onChange({
                ...data,
                founded_year: e.target.value ? parseInt(e.target.value) : null,
              })
            }
            placeholder="2020"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="location">Lokalizacja</Label>
          <Input
            id="location"
            value={data.location}
            onChange={(e) => onChange({ ...data, location: e.target.value })}
            placeholder="Warszawa"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="website">Strona internetowa</Label>
        <Input
          id="website"
          value={data.website}
          onChange={(e) => onChange({ ...data, website: e.target.value })}
          placeholder="https://twoja-firma.pl"
        />
      </div>
    </div>
  );
}

// ============================================================================
// STEP 2: Brand Identity
// ============================================================================

function Step2BrandIdentity({
  data,
  onChange,
}: {
  data: BrandWizardStep2;
  onChange: (data: BrandWizardStep2) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="mission">Misja</Label>
        <Textarea
          id="mission"
          value={data.mission}
          onChange={(e) => onChange({ ...data, mission: e.target.value })}
          placeholder="Po co istniejemy? Jaki problem rozwiazujemy?"
          rows={2}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="vision">Wizja</Label>
        <Textarea
          id="vision"
          value={data.vision}
          onChange={(e) => onChange({ ...data, vision: e.target.value })}
          placeholder="Dokad zmierzamy? Jak widzimy przyszlosc?"
          rows={2}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="uvp">Unikalna propozycja wartosci (UVP)</Label>
        <Textarea
          id="uvp"
          value={data.unique_value_proposition}
          onChange={(e) =>
            onChange({ ...data, unique_value_proposition: e.target.value })
          }
          placeholder="Co wyroznia nas na tle konkurencji?"
          rows={2}
        />
      </div>

      <TagInput
        label="Wartosci firmy"
        placeholder="Dodaj wartosc, np. jakosc, innowacyjnosc..."
        tags={data.values}
        onChange={(values) => onChange({ ...data, values })}
      />

      <TagInput
        label="Cechy osobowosci marki"
        placeholder="Dodaj ceche, np. profesjonalna, przyjazna..."
        tags={data.personality_traits}
        onChange={(personality_traits) =>
          onChange({ ...data, personality_traits })
        }
      />
    </div>
  );
}

// ============================================================================
// STEP 3: Target Audience
// ============================================================================

function Step3TargetAudience({
  data,
  onChange,
}: {
  data: BrandWizardStep3;
  onChange: (data: BrandWizardStep3) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="audience-description">Opis grupy docelowej</Label>
        <Textarea
          id="audience-description"
          value={data.description}
          onChange={(e) => onChange({ ...data, description: e.target.value })}
          placeholder="Opisz swojego idealnego klienta..."
          rows={3}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="age-from">Wiek od</Label>
          <Input
            id="age-from"
            type="number"
            value={data.age_from || ""}
            onChange={(e) =>
              onChange({
                ...data,
                age_from: e.target.value ? parseInt(e.target.value) : null,
              })
            }
            placeholder="18"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="age-to">Wiek do</Label>
          <Input
            id="age-to"
            type="number"
            value={data.age_to || ""}
            onChange={(e) =>
              onChange({
                ...data,
                age_to: e.target.value ? parseInt(e.target.value) : null,
              })
            }
            placeholder="45"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="gender">Plec</Label>
          <Select value={data.gender} onValueChange={(v) => onChange({ ...data, gender: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Wybierz" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Wszyscy</SelectItem>
              <SelectItem value="female">Kobiety</SelectItem>
              <SelectItem value="male">Mezczyzni</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <TagInput
        label="Lokalizacje"
        placeholder="Dodaj lokalizacje, np. Warszawa..."
        tags={data.locations}
        onChange={(locations) => onChange({ ...data, locations })}
      />

      <TagInput
        label="Zainteresowania"
        placeholder="Dodaj zainteresowanie, np. fitness..."
        tags={data.interests}
        onChange={(interests) => onChange({ ...data, interests })}
      />

      <TagInput
        label="Problemy/Bolaczki"
        placeholder="Jakie problemy maja Twoi klienci?"
        tags={data.pain_points}
        onChange={(pain_points) => onChange({ ...data, pain_points })}
      />

      <TagInput
        label="Cele klientow"
        placeholder="Co chca osiagnac?"
        tags={data.goals}
        onChange={(goals) => onChange({ ...data, goals })}
      />

      <TagInput
        label="Gdzie sie znajduja"
        placeholder="Instagram, LinkedIn, Facebook..."
        tags={data.where_they_are}
        onChange={(where_they_are) => onChange({ ...data, where_they_are })}
      />
    </div>
  );
}

// ============================================================================
// STEP 4: Products & Services
// ============================================================================

function Step4ProductsServices({
  data,
  onChange,
}: {
  data: BrandWizardStep4;
  onChange: (data: BrandWizardStep4) => void;
}) {
  const addProduct = () => {
    const newProduct: ProductInput = {
      name: "",
      description: "",
      price: null,
      category: "",
      features: [],
      unique_selling_points: [],
      visual_description: "",
    };
    onChange({ ...data, products: [...data.products, newProduct] });
  };

  const updateProduct = (index: number, product: ProductInput) => {
    const products = [...data.products];
    products[index] = product;
    onChange({ ...data, products });
  };

  const removeProduct = (index: number) => {
    onChange({ ...data, products: data.products.filter((_, i) => i !== index) });
  };

  const addService = () => {
    const newService: ServiceInput = {
      name: "",
      description: "",
      price_from: null,
      price_to: null,
      duration: "",
      benefits: [],
      visual_description: "",
    };
    onChange({ ...data, services: [...data.services, newService] });
  };

  const updateService = (index: number, service: ServiceInput) => {
    const services = [...data.services];
    services[index] = service;
    onChange({ ...data, services });
  };

  const removeService = (index: number) => {
    onChange({ ...data, services: data.services.filter((_, i) => i !== index) });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="price-positioning">Pozycjonowanie cenowe</Label>
        <Select value={data.price_positioning} onValueChange={(v) => onChange({ ...data, price_positioning: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Wybierz" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="budget">Budzetowy</SelectItem>
            <SelectItem value="mid_range">Srednia polka</SelectItem>
            <SelectItem value="premium">Premium</SelectItem>
            <SelectItem value="luxury">Luksusowy</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Products */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Produkty</Label>
          <Button variant="outline" size="sm" onClick={addProduct}>
            <Plus className="h-4 w-4 mr-1" />
            Dodaj produkt
          </Button>
        </div>
        {data.products.map((product, index) => (
          <ProductForm
            key={index}
            product={product}
            onChange={(p) => updateProduct(index, p)}
            onRemove={() => removeProduct(index)}
          />
        ))}
        {data.products.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
            Brak produktow. Kliknij &quot;Dodaj produkt&quot; aby dodac.
          </p>
        )}
      </div>

      {/* Services */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Uslugi</Label>
          <Button variant="outline" size="sm" onClick={addService}>
            <Plus className="h-4 w-4 mr-1" />
            Dodaj usluge
          </Button>
        </div>
        {data.services.map((service, index) => (
          <ServiceForm
            key={index}
            service={service}
            onChange={(s) => updateService(index, s)}
            onRemove={() => removeService(index)}
          />
        ))}
        {data.services.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
            Brak uslug. Kliknij &quot;Dodaj usluge&quot; aby dodac.
          </p>
        )}
      </div>
    </div>
  );
}

function ProductForm({
  product,
  onChange,
  onRemove,
}: {
  product: ProductInput;
  onChange: (p: ProductInput) => void;
  onRemove: () => void;
}) {
  return (
    <div className="p-4 border border-border rounded-lg space-y-3 bg-muted/30">
      <div className="flex items-center justify-between">
        <Input
          value={product.name}
          onChange={(e) => onChange({ ...product, name: e.target.value })}
          placeholder="Nazwa produktu"
          className="font-medium"
        />
        <Button variant="ghost" size="sm" onClick={onRemove} className="ml-2">
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
      <Textarea
        value={product.description}
        onChange={(e) => onChange({ ...product, description: e.target.value })}
        placeholder="Opis produktu"
        rows={2}
      />
      <div className="grid grid-cols-2 gap-2">
        <Input
          type="number"
          value={product.price || ""}
          onChange={(e) =>
            onChange({
              ...product,
              price: e.target.value ? parseFloat(e.target.value) : null,
            })
          }
          placeholder="Cena (PLN)"
        />
        <Input
          value={product.category}
          onChange={(e) => onChange({ ...product, category: e.target.value })}
          placeholder="Kategoria"
        />
      </div>
      <div className="space-y-1">
        <Textarea
          value={product.visual_description}
          onChange={(e) => onChange({ ...product, visual_description: e.target.value })}
          placeholder="Opis wizualny dla AI (po angielsku), np. 'colorful educational toy for children, cartoon owl mascot, bright colors'"
          rows={2}
          className="text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Opisz jak wyglada produkt - AI uzyje tego do generowania grafik
        </p>
      </div>
    </div>
  );
}

function ServiceForm({
  service,
  onChange,
  onRemove,
}: {
  service: ServiceInput;
  onChange: (s: ServiceInput) => void;
  onRemove: () => void;
}) {
  return (
    <div className="p-4 border border-border rounded-lg space-y-3 bg-muted/30">
      <div className="flex items-center justify-between">
        <Input
          value={service.name}
          onChange={(e) => onChange({ ...service, name: e.target.value })}
          placeholder="Nazwa uslugi"
          className="font-medium"
        />
        <Button variant="ghost" size="sm" onClick={onRemove} className="ml-2">
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
      <Textarea
        value={service.description}
        onChange={(e) => onChange({ ...service, description: e.target.value })}
        placeholder="Opis uslugi"
        rows={2}
      />
      <div className="grid grid-cols-3 gap-2">
        <Input
          type="number"
          value={service.price_from || ""}
          onChange={(e) =>
            onChange({
              ...service,
              price_from: e.target.value ? parseFloat(e.target.value) : null,
            })
          }
          placeholder="Cena od (PLN)"
        />
        <Input
          type="number"
          value={service.price_to || ""}
          onChange={(e) =>
            onChange({
              ...service,
              price_to: e.target.value ? parseFloat(e.target.value) : null,
            })
          }
          placeholder="Cena do (PLN)"
        />
        <Input
          value={service.duration}
          onChange={(e) => onChange({ ...service, duration: e.target.value })}
          placeholder="Czas trwania"
        />
      </div>
      <div className="space-y-1">
        <Textarea
          value={service.visual_description}
          onChange={(e) => onChange({ ...service, visual_description: e.target.value })}
          placeholder="Opis wizualny dla AI (po angielsku), np. 'professional business consultation, modern office, two people discussing'"
          rows={2}
          className="text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Opisz jak wyglada usluga - AI uzyje tego do generowania grafik
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// STEP 5: Competition
// ============================================================================

function Step5Competition({
  data,
  onChange,
}: {
  data: BrandWizardStep5;
  onChange: (data: BrandWizardStep5) => void;
}) {
  const addCompetitor = () => {
    const newCompetitor: CompetitorInput = {
      name: "",
      website: "",
      strengths: [],
      weaknesses: [],
      notes: "",
    };
    onChange({ ...data, competitors: [...data.competitors, newCompetitor] });
  };

  const updateCompetitor = (index: number, competitor: CompetitorInput) => {
    const competitors = [...data.competitors];
    competitors[index] = competitor;
    onChange({ ...data, competitors });
  };

  const removeCompetitor = (index: number) => {
    onChange({
      ...data,
      competitors: data.competitors.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="market-position">Pozycja na rynku</Label>
        <Textarea
          id="market-position"
          value={data.market_position}
          onChange={(e) =>
            onChange({ ...data, market_position: e.target.value })
          }
          placeholder="Opisz swoja pozycje na rynku wzgledem konkurencji..."
          rows={2}
        />
      </div>

      <TagInput
        label="Kluczowe wyrozniki"
        placeholder="Co wyroznia Cie na tle konkurencji?"
        tags={data.key_differentiators}
        onChange={(key_differentiators) =>
          onChange({ ...data, key_differentiators })
        }
      />

      {/* Competitors */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Konkurenci</Label>
          <Button variant="outline" size="sm" onClick={addCompetitor}>
            <Plus className="h-4 w-4 mr-1" />
            Dodaj konkurenta
          </Button>
        </div>
        {data.competitors.map((competitor, index) => (
          <CompetitorForm
            key={index}
            competitor={competitor}
            onChange={(c) => updateCompetitor(index, c)}
            onRemove={() => removeCompetitor(index)}
          />
        ))}
        {data.competitors.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
            Brak konkurentow. Kliknij &quot;Dodaj konkurenta&quot; aby dodac.
          </p>
        )}
      </div>
    </div>
  );
}

function CompetitorForm({
  competitor,
  onChange,
  onRemove,
}: {
  competitor: CompetitorInput;
  onChange: (c: CompetitorInput) => void;
  onRemove: () => void;
}) {
  return (
    <div className="p-4 border border-border rounded-lg space-y-3 bg-muted/30">
      <div className="flex items-center justify-between">
        <Input
          value={competitor.name}
          onChange={(e) => onChange({ ...competitor, name: e.target.value })}
          placeholder="Nazwa konkurenta"
          className="font-medium"
        />
        <Button variant="ghost" size="sm" onClick={onRemove} className="ml-2">
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
      <Input
        value={competitor.website}
        onChange={(e) => onChange({ ...competitor, website: e.target.value })}
        placeholder="Strona www"
      />
      <Textarea
        value={competitor.notes}
        onChange={(e) => onChange({ ...competitor, notes: e.target.value })}
        placeholder="Notatki o konkurencie..."
        rows={2}
      />
    </div>
  );
}

// ============================================================================
// STEP 6: Communication Style
// ============================================================================

function Step6CommunicationStyle({
  data,
  onChange,
}: {
  data: BrandWizardStep6;
  onChange: (data: BrandWizardStep6) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Poziom formalnosci: {data.formality_level}</Label>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Formalny</span>
          <input
            type="range"
            min="1"
            max="5"
            value={data.formality_level}
            onChange={(e) =>
              onChange({ ...data, formality_level: parseInt(e.target.value) })
            }
            className="flex-1"
          />
          <span className="text-sm text-muted-foreground">Swobodny</span>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="emoji-usage">Uzycie emoji</Label>
        <Select value={data.emoji_usage} onValueChange={(v) => onChange({ ...data, emoji_usage: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Wybierz" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Brak</SelectItem>
            <SelectItem value="minimal">Minimalne</SelectItem>
            <SelectItem value="moderate">Umiarkowane</SelectItem>
            <SelectItem value="frequent">Czeste</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <TagInput
        label="Slowa do uzywania"
        placeholder="Slowa, ktore pasuja do Twojej marki..."
        tags={data.words_to_use}
        onChange={(words_to_use) => onChange({ ...data, words_to_use })}
      />

      <TagInput
        label="Slowa do unikania"
        placeholder="Slowa, ktorych chcesz unikac..."
        tags={data.words_to_avoid}
        onChange={(words_to_avoid) => onChange({ ...data, words_to_avoid })}
      />

      <TagInput
        label="Przykladowe frazy"
        placeholder="Frazy w stylu Twojej marki..."
        tags={data.example_phrases}
        onChange={(example_phrases) => onChange({ ...data, example_phrases })}
      />
    </div>
  );
}

// ============================================================================
// STEP 7: Content Preferences
// ============================================================================

function Step7ContentPreferences({
  data,
  onChange,
}: {
  data: BrandWizardStep7;
  onChange: (data: BrandWizardStep7) => void;
}) {
  return (
    <div className="space-y-4">
      <TagInput
        label="Tematy/Filary tresci"
        placeholder="O czym chcesz mowic? np. edukacja, inspiracje..."
        tags={data.themes}
        onChange={(themes) => onChange({ ...data, themes })}
      />

      <div className="space-y-2">
        <Label htmlFor="hashtag-style">Styl hashtagow</Label>
        <Select value={data.hashtag_style} onValueChange={(v) => onChange({ ...data, hashtag_style: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Wybierz" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="branded">Glownie firmowe</SelectItem>
            <SelectItem value="trending">Glownie trendujace</SelectItem>
            <SelectItem value="mixed">Mieszane</SelectItem>
            <SelectItem value="minimal">Minimalne</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <TagInput
        label="Hashtagi firmowe"
        placeholder="Twoje firmowe hashtagi..."
        tags={data.branded_hashtags}
        onChange={(branded_hashtags) => onChange({ ...data, branded_hashtags })}
      />

      <div className="space-y-2">
        <Label htmlFor="post-frequency">Czestotliwosc postow</Label>
        <Input
          id="post-frequency"
          value={data.post_frequency}
          onChange={(e) => onChange({ ...data, post_frequency: e.target.value })}
          placeholder="np. 3-4 razy w tygodniu"
        />
      </div>

      <TagInput
        label="Preferowane formaty"
        placeholder="np. karuzela, reels, stories..."
        tags={data.preferred_formats}
        onChange={(preferred_formats) =>
          onChange({ ...data, preferred_formats })
        }
      />

      <TagInput
        label="Cele content marketingu"
        placeholder="np. budowanie swiadomosci, sprzedaz..."
        tags={data.content_goals}
        onChange={(content_goals) => onChange({ ...data, content_goals })}
      />
    </div>
  );
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

function TagInput({
  label,
  placeholder,
  tags,
  onChange,
}: {
  label: string;
  placeholder: string;
  tags: string[];
  onChange: (tags: string[]) => void;
}) {
  const [inputValue, setInputValue] = useState("");

  const addTag = () => {
    if (inputValue.trim() && !tags.includes(inputValue.trim())) {
      onChange([...tags, inputValue.trim()]);
      setInputValue("");
    }
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag();
    }
  };

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
        />
        <Button type="button" variant="outline" onClick={addTag}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {tags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className="cursor-pointer hover:bg-destructive/20"
              onClick={() => removeTag(tag)}
            >
              {tag}
              <X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
