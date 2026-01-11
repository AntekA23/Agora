"use client";

import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { MessageSquare } from "lucide-react";
import { TagInput } from "./tag-input";
import { cn } from "@/lib/utils";

export interface CommunicationData {
  tone: string;
  voice_description: string;
  formality_level: number;
  emoji_usage: string;
  brand_values: string[];
  words_to_use: string[];
  words_to_avoid: string[];
  preferred_formats: string[];
  content_themes: string[];
}

interface StepCommunicationProps {
  data: CommunicationData;
  onChange: (data: CommunicationData) => void;
}

const TONE_OPTIONS = [
  { value: "professional", label: "Profesjonalny", desc: "Formalny, rzeczowy, ekspercki" },
  { value: "friendly", label: "Przyjazny", desc: "Ciepry, bezposredni, otwarty" },
  { value: "inspiring", label: "Inspirujacy", desc: "Motywujacy, pelny energii" },
  { value: "educational", label: "Edukacyjny", desc: "Pouczajacy, merytoryczny" },
  { value: "humorous", label: "Humorystyczny", desc: "Lekki, zabawny, ludzki" },
  { value: "luxurious", label: "Luksusowy", desc: "Elegancki, ekskluzywny" },
];

const EMOJI_OPTIONS = [
  { value: "none", label: "Brak", desc: "Bez emoji" },
  { value: "minimal", label: "Minimalne", desc: "Rzadko, subtelnie" },
  { value: "moderate", label: "Umiarkowane", desc: "Czasami, dla podkreslenia" },
  { value: "frequent", label: "Czesto", desc: "Regularnie w tresciach" },
];

const FORMAT_OPTIONS = [
  { value: "post", label: "Posty" },
  { value: "carousel", label: "Karuzele" },
  { value: "reels", label: "Reels/Video" },
  { value: "stories", label: "Stories" },
  { value: "infographics", label: "Infografiki" },
  { value: "quotes", label: "Cytaty" },
  { value: "tutorials", label: "Poradniki" },
  { value: "behind_scenes", label: "Za kulisami" },
];

export function StepCommunication({ data, onChange }: StepCommunicationProps) {
  const updateField = <K extends keyof CommunicationData>(
    field: K,
    value: CommunicationData[K]
  ) => {
    onChange({ ...data, [field]: value });
  };

  const toggleFormat = (format: string) => {
    const formats = data.preferred_formats.includes(format)
      ? data.preferred_formats.filter((f) => f !== format)
      : [...data.preferred_formats, format];
    updateField("preferred_formats", formats);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <MessageSquare className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Styl komunikacji
        </h2>
        <p className="text-muted-foreground">
          Okresl jak Twoja marka powinna sie komunikowac
        </p>
      </div>

      {/* Tone Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Ton komunikacji
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {TONE_OPTIONS.map((tone) => (
            <button
              key={tone.value}
              type="button"
              onClick={() => updateField("tone", tone.value)}
              className={cn(
                "p-4 rounded-lg border text-left transition-colors",
                data.tone === tone.value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <p className="font-medium text-foreground">{tone.label}</p>
              <p className="text-xs text-muted-foreground mt-1">{tone.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Voice Description */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="voice-description">Glos marki</Label>
          <Textarea
            id="voice-description"
            value={data.voice_description}
            onChange={(e) => updateField("voice_description", e.target.value)}
            placeholder="Opisz, jak Twoja marka powinna brzmiez. Np. 'Komunikujemy sie jak dobry przyjaciel, ktory zna sie na rzeczy - bez sztywnosci, ale z merytoryczna wartoscia'"
            rows={3}
          />
        </div>
      </div>

      {/* Formality Level */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Poziom formalnosci: {data.formality_level}</Label>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Formalny</span>
            <input
              type="range"
              min="1"
              max="5"
              value={data.formality_level}
              onChange={(e) =>
                updateField("formality_level", parseInt(e.target.value))
              }
              className="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <span className="text-sm text-muted-foreground">Swobodny</span>
          </div>
        </div>
      </div>

      {/* Emoji Usage */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Uzycie emoji
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {EMOJI_OPTIONS.map((emoji) => (
            <button
              key={emoji.value}
              type="button"
              onClick={() => updateField("emoji_usage", emoji.value)}
              className={cn(
                "p-3 rounded-lg border text-center transition-colors",
                data.emoji_usage === emoji.value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <p className="font-medium text-foreground text-sm">
                {emoji.label}
              </p>
              <p className="text-xs text-muted-foreground">{emoji.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Brand Values */}
      <div className="space-y-4">
        <TagInput
          label="Wartosci marki w komunikacji"
          placeholder="np. autentycznosc, wiarygodnosc..."
          tags={data.brand_values}
          onChange={(values) => updateField("brand_values", values)}
        />

        <TagInput
          label="Slowa do uzywania"
          placeholder="Slowa pasujace do Twojej marki..."
          tags={data.words_to_use}
          onChange={(words) => updateField("words_to_use", words)}
        />

        <TagInput
          label="Slowa do unikania"
          placeholder="Slowa, ktorych lepiej nie uzywaz..."
          tags={data.words_to_avoid}
          onChange={(words) => updateField("words_to_avoid", words)}
        />
      </div>

      {/* Content Formats */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Preferowane formaty tresci
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {FORMAT_OPTIONS.map((format) => (
            <div
              key={format.value}
              className={cn(
                "flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition-colors",
                data.preferred_formats.includes(format.value)
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
              onClick={() => toggleFormat(format.value)}
            >
              <Checkbox
                checked={data.preferred_formats.includes(format.value)}
                onCheckedChange={() => toggleFormat(format.value)}
              />
              <Label className="cursor-pointer">{format.label}</Label>
            </div>
          ))}
        </div>
      </div>

      {/* Content Themes */}
      <div className="space-y-4">
        <TagInput
          label="Tematy tresci"
          placeholder="O czym chcesz mowic? np. edukacja, inspiracje..."
          tags={data.content_themes}
          onChange={(themes) => updateField("content_themes", themes)}
        />
      </div>
    </div>
  );
}
