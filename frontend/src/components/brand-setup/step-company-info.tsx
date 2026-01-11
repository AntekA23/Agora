"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Building2 } from "lucide-react";
import { TagInput } from "./tag-input";

export interface CompanyInfoData {
  name: string;
  industry: string;
  description: string;
  website: string;
  founded_year: number | null;
  location: string;
  mission: string;
  vision: string;
  values: string[];
}

interface StepCompanyInfoProps {
  data: CompanyInfoData;
  onChange: (data: CompanyInfoData) => void;
}

const INDUSTRIES = [
  { value: "technology", label: "Technologia / IT" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "retail", label: "Handel detaliczny" },
  { value: "services", label: "Uslugi" },
  { value: "healthcare", label: "Zdrowie / Medycyna" },
  { value: "education", label: "Edukacja" },
  { value: "finance", label: "Finanse / Ubezpieczenia" },
  { value: "real_estate", label: "Nieruchomosci" },
  { value: "hospitality", label: "Gastronomia / Hotelarstwo" },
  { value: "manufacturing", label: "Produkcja" },
  { value: "construction", label: "Budownictwo" },
  { value: "media", label: "Media / Rozrywka" },
  { value: "beauty", label: "Uroda / Kosmetyki" },
  { value: "fitness", label: "Fitness / Sport" },
  { value: "consulting", label: "Doradztwo / Consulting" },
  { value: "other", label: "Inna" },
];

export function StepCompanyInfo({ data, onChange }: StepCompanyInfoProps) {
  const updateField = <K extends keyof CompanyInfoData>(
    field: K,
    value: CompanyInfoData[K]
  ) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Building2 className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          O Twojej firmie
        </h2>
        <p className="text-muted-foreground">
          Podstawowe informacje o firmie i jej tozsamosci
        </p>
      </div>

      {/* Basic Info Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Informacje podstawowe
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="company-name">Nazwa firmy *</Label>
            <Input
              id="company-name"
              value={data.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="Nazwa Twojej firmy"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="industry">Branza *</Label>
            <Select
              value={data.industry}
              onValueChange={(v) => updateField("industry", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Wybierz branze" />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRIES.map((ind) => (
                  <SelectItem key={ind.value} value={ind.value}>
                    {ind.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Opis firmy *</Label>
          <Textarea
            id="description"
            value={data.description}
            onChange={(e) => updateField("description", e.target.value)}
            placeholder="Krotki opis tego, czym zajmuje sie Twoja firma, jakie problemy rozwiazuje..."
            rows={4}
          />
          <p className="text-xs text-muted-foreground">
            Ten opis pomoze AI lepiej zrozumiec Twoja firme i generowac trafniejsze tresci
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="website">Strona WWW</Label>
            <Input
              id="website"
              value={data.website}
              onChange={(e) => updateField("website", e.target.value)}
              placeholder="https://twoja-firma.pl"
              type="url"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="founded-year">Rok zalozenia</Label>
            <Input
              id="founded-year"
              type="number"
              value={data.founded_year || ""}
              onChange={(e) =>
                updateField(
                  "founded_year",
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
              placeholder="2020"
              min="1900"
              max={new Date().getFullYear()}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Lokalizacja</Label>
            <Input
              id="location"
              value={data.location}
              onChange={(e) => updateField("location", e.target.value)}
              placeholder="Warszawa"
            />
          </div>
        </div>
      </div>

      {/* Brand Identity Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Tozsamosc marki
        </h3>

        <div className="space-y-2">
          <Label htmlFor="mission">Misja firmy</Label>
          <Textarea
            id="mission"
            value={data.mission}
            onChange={(e) => updateField("mission", e.target.value)}
            placeholder="Po co istniejemy? Jaki problem rozwiazujemy dla naszych klientow?"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="vision">Wizja firmy</Label>
          <Textarea
            id="vision"
            value={data.vision}
            onChange={(e) => updateField("vision", e.target.value)}
            placeholder="Dokad zmierzamy? Jak widzimy przyszlosc naszej firmy?"
            rows={2}
          />
        </div>

        <TagInput
          label="Wartosci firmy"
          placeholder="np. jakosc, innowacyjnosc, rzetelnosc..."
          tags={data.values}
          onChange={(values) => updateField("values", values)}
        />
      </div>
    </div>
  );
}
