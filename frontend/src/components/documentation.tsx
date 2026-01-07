"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Book,
  Sparkles,
  FileText,
  TrendingUp,
  Users,
  Briefcase,
  Scale,
  HeadphonesIcon,
  Bell,
  Mic,
  Target,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Zap,
  Globe,
  Image,
  FileDown
} from "lucide-react";

interface DocSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function DocSection({ title, icon, children, defaultOpen = false }: DocSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border rounded-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {icon}
          <span className="font-medium">{title}</span>
        </div>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4 pt-2 border-t">
          {children}
        </div>
      )}
    </div>
  );
}

function FeatureItem({ title, description, status = "available" }: {
  title: string;
  description: string;
  status?: "available" | "beta" | "planned";
}) {
  return (
    <div className="flex gap-3 py-2">
      <div className="mt-0.5">
        {status === "available" && <CheckCircle className="h-4 w-4 text-green-500" />}
        {status === "beta" && <Zap className="h-4 w-4 text-yellow-500" />}
        {status === "planned" && <AlertTriangle className="h-4 w-4 text-muted-foreground" />}
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="font-medium">{title}</span>
          {status === "beta" && <Badge variant="outline" className="text-xs">Beta</Badge>}
          {status === "planned" && <Badge variant="secondary" className="text-xs">Planowane</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

export function Documentation() {
  return (
    <div className="space-y-6">
      {/* Wprowadzenie */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Book className="h-5 w-5" />
            Dokumentacja Agora
          </CardTitle>
          <CardDescription>
            Kompletny przewodnik po platformie AI dla biznesu
          </CardDescription>
        </CardHeader>
        <CardContent className="prose prose-sm dark:prose-invert max-w-none">
          <p>
            <strong>Agora</strong> to platforma SaaS oferujaca zespoly wyspecjalizowanych agentow AI,
            ktorzy pomagaja w codziennych zadaniach biznesowych. Zamiast zatrudniac specjalistow
            od marketingu, finansow czy HR - mozesz skorzystac z naszych agentow AI.
          </p>
          <div className="flex gap-2 flex-wrap mt-4">
            <Badge>Marketing</Badge>
            <Badge>Finanse</Badge>
            <Badge>HR</Badge>
            <Badge>Sprzedaz</Badge>
            <Badge>Prawo</Badge>
            <Badge>Wsparcie</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Sekcje dokumentacji */}
      <div className="space-y-3">

        {/* Marketing */}
        <DocSection
          title="Marketing"
          icon={<Sparkles className="h-5 w-5 text-pink-500" />}
          defaultOpen={true}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci marketingowi pomagaja w tworzeniu tresci i kampanii.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Instagram Specialist"
              description="Generuje posty na Instagram z hashtagami, emoji i call-to-action. Wyszukuje aktualne trendy przez internet."
            />
            <FeatureItem
              title="Copywriter"
              description="Tworzy teksty marketingowe: opisy produktow, emaile, posty na social media, artykuly blogowe."
            />
            <FeatureItem
              title="Generowanie grafik"
              description="Tworzy grafiki do postow za pomoca AI (Together.ai). Opcja dostepna przy generowaniu posta."
            />
            <FeatureItem
              title="Kampanie multi-agentowe"
              description="Koordynacja wielu agentow do stworzenia kompletnej kampanii marketingowej."
              status="beta"
            />
          </div>

          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-sm font-medium">Jak uzywac:</p>
            <ol className="text-sm text-muted-foreground mt-2 space-y-1 list-decimal list-inside">
              <li>Przejdz do sekcji &quot;Marketing&quot; w menu</li>
              <li>Wybierz agenta (Instagram lub Copywriter)</li>
              <li>Wypelnij brief - opisz co chcesz stworzyc</li>
              <li>Opcjonalnie zaznacz &quot;Generuj grafike&quot;</li>
              <li>Kliknij &quot;Generuj&quot; i poczekaj na wynik</li>
            </ol>
          </div>
        </DocSection>

        {/* Finanse */}
        <DocSection
          title="Finanse"
          icon={<TrendingUp className="h-5 w-5 text-green-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci finansowi pomagaja w analizie i dokumentacji finansowej.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Analiza faktur"
              description="Analizuje faktury, kategoryzuje wydatki, wykrywa anomalie i sugeruje optymalizacje."
            />
            <FeatureItem
              title="Analiza Cashflow"
              description="Analizuje przeplyw gotowki, prognozuje przyszle przeplywy, identyfikuje trendy."
            />
            <FeatureItem
              title="Generowanie PDF"
              description="Eksportuje faktury i raporty do profesjonalnych dokumentow PDF."
            />
          </div>

          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-sm font-medium">Jak uzywac:</p>
            <ol className="text-sm text-muted-foreground mt-2 space-y-1 list-decimal list-inside">
              <li>Przejdz do sekcji &quot;Finanse&quot; w menu</li>
              <li>Wybierz typ analizy (Faktury lub Cashflow)</li>
              <li>Wprowadz dane finansowe lub opis sytuacji</li>
              <li>Agent przeanalizuje dane i zwroci raport</li>
            </ol>
          </div>
        </DocSection>

        {/* HR */}
        <DocSection
          title="HR - Zasoby Ludzkie"
          icon={<Users className="h-5 w-5 text-blue-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci HR pomagaja w rekrutacji i zarzadzaniu zespolem.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Recruiter"
              description="Tworzy ogloszenia o prace, bada wynagrodzenia rynkowe, generuje opisy stanowisk."
            />
            <FeatureItem
              title="Interviewer"
              description="Przygotowuje pytania rekrutacyjne dopasowane do stanowiska i kompetencji."
            />
            <FeatureItem
              title="Onboarding"
              description="Generuje plany wdrozeniowe dla nowych pracownikow."
            />
          </div>
        </DocSection>

        {/* Sprzedaz */}
        <DocSection
          title="Sprzedaz"
          icon={<Briefcase className="h-5 w-5 text-orange-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci sprzedazowi wspieraja procesy sprzedazowe.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Proposal Generator"
              description="Tworzy profesjonalne oferty handlowe na podstawie opisu klienta i produktu."
            />
            <FeatureItem
              title="Lead Scorer"
              description="Ocenia leady wedlug metodologii BANT (Budget, Authority, Need, Timeline)."
            />
            <FeatureItem
              title="CRM Assistant"
              description="Analizuje klientow, generuje follow-upy, sugeruje kolejne kroki."
            />
          </div>
        </DocSection>

        {/* Prawo */}
        <DocSection
          title="Prawo"
          icon={<Scale className="h-5 w-5 text-purple-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci prawni pomagaja w dokumentach i compliance.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Contract Reviewer"
              description="Analizuje umowy, identyfikuje ryzyka, sugeruje zmiany."
            />
            <FeatureItem
              title="GDPR Assistant"
              description="Sprawdza zgodnosc z RODO, generuje polityki prywatnosci."
            />
            <FeatureItem
              title="Terms Generator"
              description="Tworzy regulaminy, polityki zwrotow, warunki uslug."
            />
          </div>

          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              <AlertTriangle className="h-4 w-4 inline mr-1" />
              <strong>Uwaga:</strong> Agenci prawni to narzedzia wspierajace, nie zastepuja porady prawnika.
              Zawsze konsultuj wazne dokumenty z profesjonalista.
            </p>
          </div>
        </DocSection>

        {/* Wsparcie */}
        <DocSection
          title="Wsparcie Klienta"
          icon={<HeadphonesIcon className="h-5 w-5 text-cyan-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Agenci wsparcia pomagaja w obsludze klientow.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Ticket Handler"
              description="Analizuje zgloszenia, kategoryzuje problemy, sugeruje odpowiedzi."
            />
            <FeatureItem
              title="FAQ Generator"
              description="Tworzy baze czesto zadawanych pytan na podstawie zgloszen."
            />
            <FeatureItem
              title="Sentiment Analyst"
              description="Analizuje sentyment wiadomosci od klientow, wykrywa negatywne opinie."
            />
          </div>
        </DocSection>

        {/* Monitoring */}
        <DocSection
          title="Monitoring i Alerty"
          icon={<Bell className="h-5 w-5 text-red-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            System proaktywnych powiadomien i monitoringu.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Monitor Cashflow"
              description="Ostrzega o niskim stanie konta, nietypowych wydatkach, problemach z plynnoscia."
            />
            <FeatureItem
              title="Monitor Faktur"
              description="Przypomina o niezaplaconych fakturach, zblizajacych sie terminach."
            />
            <FeatureItem
              title="Monitor Contentu"
              description="Ostrzega gdy brakuje zaplanowanych postow na social media."
            />
            <FeatureItem
              title="Monitor Trendow"
              description="Wykrywa nowe trendy w branzy, sugeruje reakcje."
              status="beta"
            />
          </div>
        </DocSection>

        {/* Glos */}
        <DocSection
          title="Interfejs Glosowy"
          icon={<Mic className="h-5 w-5 text-indigo-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Komunikacja glosowa z systemem (wymaga API OpenAI).
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Speech-to-Text"
              description="Transkrypcja mowy na tekst przez Whisper API."
              status="beta"
            />
            <FeatureItem
              title="Text-to-Speech"
              description="Synteza mowy - system odpowiada glosowo."
              status="beta"
            />
            <FeatureItem
              title="Voice Agent"
              description="Konwersacyjny agent glosowy do szybkich polecen."
              status="beta"
            />
          </div>

          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-sm">
              <strong>Dostepne komendy glosowe:</strong> &quot;Stworz post&quot;, &quot;Wystaw fakture&quot;,
              &quot;Sprawdz finanse&quot;, &quot;Pokaz alerty&quot;, &quot;Napisz email&quot;
            </p>
          </div>
        </DocSection>

        {/* Cele autonomiczne */}
        <DocSection
          title="Cele Autonomiczne"
          icon={<Target className="h-5 w-5 text-emerald-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            System autonomicznej realizacji celow biznesowych.
          </p>

          <div className="space-y-1">
            <FeatureItem
              title="Definiowanie celow"
              description="Ustaw cel biznesowy (np. 'Zwieksz engagement o 20%'), a AI sam zaplanuje kroki."
              status="beta"
            />
            <FeatureItem
              title="Automatyczne planowanie"
              description="Agent bada rynek, analizuje konkurencje i tworzy strategie."
              status="beta"
            />
            <FeatureItem
              title="Wykonywanie krokow"
              description="System autonomicznie wykonuje zaplanowane zadania."
              status="beta"
            />
            <FeatureItem
              title="Raportowanie postepu"
              description="Regularne raporty o postepie w realizacji celu."
              status="beta"
            />
          </div>
        </DocSection>

        {/* Dodatkowe funkcje */}
        <DocSection
          title="Dodatkowe Funkcje"
          icon={<Zap className="h-5 w-5 text-yellow-500" />}
        >
          <div className="space-y-1">
            <FeatureItem
              title="Wyszukiwanie internetowe (Tavily)"
              description="Agenci moga wyszukiwac aktualne informacje w internecie - trendy, konkurencje, dane rynkowe."
              status="available"
            />
            <FeatureItem
              title="Generowanie grafik AI"
              description="Tworzenie grafik do postow przez Together.ai (model Flux)."
              status="available"
            />
            <FeatureItem
              title="Eksport do PDF"
              description="Eksport faktur i raportow do profesjonalnych dokumentow PDF."
              status="available"
            />
            <FeatureItem
              title="Pamiec agentow"
              description="Agenci pamietaja poprzednie zadania i ucza sie z feedbacku."
              status="available"
            />
            <FeatureItem
              title="System feedbacku"
              description="Oceniaj wyniki agentow (1-5 gwiazdek) aby poprawiac jakosc."
              status="available"
            />
            <FeatureItem
              title="A/B Testing"
              description="Tworzenie i testowanie wariantow tresci marketingowych."
              status="beta"
            />
          </div>
        </DocSection>

        {/* Znane ograniczenia */}
        <DocSection
          title="Znane Ograniczenia"
          icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            Obecne ograniczenia i niedociagniecia systemu.
          </p>

          <div className="space-y-3">
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Wylogowywanie przy odswiezeniu</p>
              <p className="text-sm text-muted-foreground">
                Sesja moze wygasac przy odswiezaniu strony. Pracujemy nad poprawka.
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Brak integracji z social media</p>
              <p className="text-sm text-muted-foreground">
                Obecnie nie mozna publikowac bezposrednio na Instagram/Facebook.
                Trzeba recznie skopiowac wygenerowana tresc.
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Brak integracji z systemami ksiegowymi</p>
              <p className="text-sm text-muted-foreground">
                Faktury generowane sa w systemie, ale nie lacza sie z Fakturownia, iFirma itp.
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Jakosc generowanych tresci</p>
              <p className="text-sm text-muted-foreground">
                Tresci generowane przez AI moga wymagac edycji. Zawsze przegladaj przed publikacja.
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Ograniczone jezyki</p>
              <p className="text-sm text-muted-foreground">
                System zoptymalizowany pod jezyk polski. Inne jezyki moga dzialac gorzej.
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Funkcje Beta</p>
              <p className="text-sm text-muted-foreground">
                Funkcje oznaczone jako &quot;Beta&quot; moga byc niestabilne lub niekompletne.
              </p>
            </div>
          </div>
        </DocSection>

        {/* Wymagane klucze API */}
        <DocSection
          title="Wymagane Klucze API"
          icon={<Globe className="h-5 w-5 text-gray-500" />}
        >
          <p className="text-sm text-muted-foreground mb-4">
            System wymaga kluczy API do dzialania niektorych funkcji.
          </p>

          <div className="space-y-2">
            <div className="flex justify-between items-center p-2 bg-muted rounded">
              <span className="text-sm font-medium">OpenAI API</span>
              <Badge>Wymagany</Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-3">
              Glowny silnik AI - wymagany do wszystkich agentow.
            </p>

            <div className="flex justify-between items-center p-2 bg-muted rounded">
              <span className="text-sm font-medium">Tavily API</span>
              <Badge variant="outline">Opcjonalny</Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-3">
              Wyszukiwanie internetowe - bez niego agenci nie maja dostepu do aktualnych informacji.
            </p>

            <div className="flex justify-between items-center p-2 bg-muted rounded">
              <span className="text-sm font-medium">Together.ai API</span>
              <Badge variant="outline">Opcjonalny</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Generowanie grafik - bez niego opcja &quot;Generuj grafike&quot; nie zadziala.
            </p>
          </div>
        </DocSection>

      </div>

      {/* Wsparcie */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              Masz pytania lub problemy? Skontaktuj sie z nami.
            </p>
            <p className="text-sm font-medium mt-2">
              support@agora.pl
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
