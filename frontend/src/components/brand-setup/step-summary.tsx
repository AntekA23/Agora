"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  Building2,
  Users,
  MessageSquare,
  Edit,
} from "lucide-react";
import type { CompanyInfoData } from "./step-company-info";
import type { MarketData } from "./step-market";
import type { CommunicationData } from "./step-communication";

interface StepSummaryProps {
  companyInfo: CompanyInfoData;
  market: MarketData;
  communication: CommunicationData;
  onEditStep: (step: number) => void;
}

export function StepSummary({
  companyInfo,
  market,
  communication,
  onEditStep,
}: StepSummaryProps) {
  const getToneLabel = (tone: string) => {
    const tones: Record<string, string> = {
      professional: "Profesjonalny",
      friendly: "Przyjazny",
      inspiring: "Inspirujacy",
      educational: "Edukacyjny",
      humorous: "Humorystyczny",
      luxurious: "Luksusowy",
    };
    return tones[tone] || tone;
  };

  const getEmojiLabel = (emoji: string) => {
    const emojis: Record<string, string> = {
      none: "Brak",
      minimal: "Minimalne",
      moderate: "Umiarkowane",
      frequent: "Czeste",
    };
    return emojis[emoji] || emoji;
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Podsumowanie
        </h2>
        <p className="text-muted-foreground">
          Sprawdz wprowadzone dane przed zapisaniem
        </p>
      </div>

      {/* Company Info Summary */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-4 bg-muted/30 border-b border-border">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-foreground">O firmie</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEditStep(1)}
          >
            <Edit className="w-4 h-4 mr-1" />
            Edytuj
          </Button>
        </div>
        <div className="p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Nazwa firmy</p>
              <p className="font-medium text-foreground">
                {companyInfo.name || "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Branza</p>
              <p className="font-medium text-foreground">
                {companyInfo.industry || "-"}
              </p>
            </div>
          </div>
          {companyInfo.description && (
            <div>
              <p className="text-xs text-muted-foreground">Opis</p>
              <p className="text-sm text-foreground">{companyInfo.description}</p>
            </div>
          )}
          {companyInfo.mission && (
            <div>
              <p className="text-xs text-muted-foreground">Misja</p>
              <p className="text-sm text-foreground">{companyInfo.mission}</p>
            </div>
          )}
          {companyInfo.values.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Wartosci</p>
              <div className="flex flex-wrap gap-1">
                {companyInfo.values.map((value) => (
                  <Badge key={value} variant="secondary">
                    {value}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Market Summary */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-4 bg-muted/30 border-b border-border">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-foreground">Klienci i rynek</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEditStep(2)}
          >
            <Edit className="w-4 h-4 mr-1" />
            Edytuj
          </Button>
        </div>
        <div className="p-4 space-y-3">
          {market.target_audience && (
            <div>
              <p className="text-xs text-muted-foreground">Grupa docelowa</p>
              <p className="text-sm text-foreground">{market.target_audience}</p>
            </div>
          )}
          {market.products.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Produkty ({market.products.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {market.products.map((p, i) => (
                  <Badge key={i} variant="outline">
                    {p.name || `Produkt ${i + 1}`}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {market.services.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Uslugi ({market.services.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {market.services.map((s, i) => (
                  <Badge key={i} variant="outline">
                    {s.name || `Usluga ${i + 1}`}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {market.unique_selling_points.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Przewagi konkurencyjne
              </p>
              <div className="flex flex-wrap gap-1">
                {market.unique_selling_points.map((usp) => (
                  <Badge key={usp} variant="secondary">
                    {usp}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Communication Summary */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-4 bg-muted/30 border-b border-border">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-foreground">Styl komunikacji</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEditStep(3)}
          >
            <Edit className="w-4 h-4 mr-1" />
            Edytuj
          </Button>
        </div>
        <div className="p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Ton</p>
              <p className="font-medium text-foreground">
                {getToneLabel(communication.tone) || "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Formalnosc</p>
              <p className="font-medium text-foreground">
                {communication.formality_level}/5
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Emoji</p>
              <p className="font-medium text-foreground">
                {getEmojiLabel(communication.emoji_usage)}
              </p>
            </div>
          </div>
          {communication.voice_description && (
            <div>
              <p className="text-xs text-muted-foreground">Glos marki</p>
              <p className="text-sm text-foreground">
                {communication.voice_description}
              </p>
            </div>
          )}
          {communication.preferred_formats.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Preferowane formaty
              </p>
              <div className="flex flex-wrap gap-1">
                {communication.preferred_formats.map((format) => (
                  <Badge key={format} variant="secondary">
                    {format}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {communication.content_themes.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Tematy tresci</p>
              <div className="flex flex-wrap gap-1">
                {communication.content_themes.map((theme) => (
                  <Badge key={theme} variant="outline">
                    {theme}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Ready message */}
      <div className="text-center p-6 bg-green-500/5 border border-green-500/20 rounded-lg">
        <CheckCircle2 className="w-8 h-8 text-green-500 mx-auto mb-2" />
        <p className="font-medium text-foreground">
          Wszystko gotowe!
        </p>
        <p className="text-sm text-muted-foreground">
          Kliknij &quot;Zakoncz&quot; aby zapisaz dane i rozpoczac prace z Agora
        </p>
      </div>
    </div>
  );
}
