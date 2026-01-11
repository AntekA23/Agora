"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Globe, Loader2, ChevronRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepQuickStartProps {
  onAnalyze: (url: string) => Promise<void>;
  onSkip: () => void;
  isAnalyzing: boolean;
}

export function StepQuickStart({ onAnalyze, onSkip, isAnalyzing }: StepQuickStartProps) {
  const [url, setUrl] = useState("");

  const handleAnalyze = async () => {
    if (url) {
      await onAnalyze(url);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Sparkles className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Szybki start z AI
        </h2>
        <p className="text-muted-foreground">
          Podaj adres strony internetowej swojej firmy, a automatycznie
          wyciagniemy podstawowe informacje. Ten krok jest opcjonalny.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="website-url" className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Adres strony WWW
          </Label>
          <div className="flex gap-3">
            <Input
              id="website-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://twoja-firma.pl"
              type="url"
              className="flex-1"
              disabled={isAnalyzing}
            />
            <Button
              onClick={handleAnalyze}
              disabled={!url || isAnalyzing}
              className="min-w-[120px]"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analizuje...
                </>
              ) : (
                "Analizuj"
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Wykorzystamy AI do analizy zawartosci strony i wypelnienia formularza
          </p>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">lub</span>
          </div>
        </div>

        <div className="text-center">
          <Button
            variant="outline"
            onClick={onSkip}
            disabled={isAnalyzing}
            className="min-w-[200px]"
          >
            Wypelnie recznie
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* Benefits list */}
      <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { title: "Oszczednosc czasu", desc: "Automatyczne wypelnianie formularza" },
          { title: "Dokladnosc", desc: "AI analizuje tresc strony" },
          { title: "Personalizacja", desc: "Mozesz pozniej edytowac dane" },
        ].map((benefit, index) => (
          <div
            key={index}
            className={cn(
              "p-4 rounded-lg border border-border bg-card",
              "text-center"
            )}
          >
            <h3 className="font-medium text-foreground text-sm mb-1">
              {benefit.title}
            </h3>
            <p className="text-xs text-muted-foreground">{benefit.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
