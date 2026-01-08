"use client";

import * as React from "react";
import Link from "next/link";
import {
  Rocket,
  ChevronLeft,
  Loader2,
  Calendar,
  Sparkles,
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Mail,
  Check,
  AlertCircle,
  Eye,
  Trash2,
  Clock,
} from "lucide-react";
import { format, addDays } from "date-fns";
import { pl } from "date-fns/locale";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import {
  useBatchGeneration,
  varietyLabels,
  varietyDescriptions,
  countOptions,
  type VarietyLevel,
  type BatchGenerationResponse,
} from "@/hooks/use-batch-generation";
import {
  type ContentPlatform,
  platformLabels,
} from "@/hooks/use-scheduled-content";

const platformIcons: Record<ContentPlatform, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
  twitter: Twitter,
  email: Mail,
  other: Sparkles,
};

const platformContentTypes: Record<ContentPlatform, string> = {
  instagram: "instagram_post",
  facebook: "facebook_post",
  linkedin: "linkedin_post",
  twitter: "twitter_post",
  email: "email_newsletter",
  other: "other",
};

export default function BatchGenerationPage() {
  const { toast } = useToast();
  const batchMutation = useBatchGeneration();

  // Form state
  const [step, setStep] = React.useState(1);
  const [platform, setPlatform] = React.useState<ContentPlatform>("instagram");
  const [count, setCount] = React.useState(7);
  const [customCount, setCustomCount] = React.useState("");
  const [theme, setTheme] = React.useState("");
  const [variety, setVariety] = React.useState<VarietyLevel>("medium");
  const [autoSchedule, setAutoSchedule] = React.useState(true);
  const [requireApproval, setRequireApproval] = React.useState(false);
  const [startDate, setStartDate] = React.useState(
    format(addDays(new Date(), 1), "yyyy-MM-dd")
  );
  const [endDate, setEndDate] = React.useState(
    format(addDays(new Date(), 7), "yyyy-MM-dd")
  );

  // Result state
  const [result, setResult] = React.useState<BatchGenerationResponse | null>(null);

  const effectiveCount = customCount ? parseInt(customCount, 10) : count;

  const handleGenerate = async () => {
    if (!theme.trim()) {
      toast({
        title: "Błąd",
        description: "Podaj temat/motyw przewodni",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await batchMutation.mutateAsync({
        content_type: platformContentTypes[platform] as any,
        platform,
        count: effectiveCount,
        theme: theme.trim(),
        variety,
        date_range: autoSchedule
          ? { start: startDate, end: endDate }
          : undefined,
        auto_schedule: autoSchedule,
        require_approval: requireApproval,
      });

      setResult(response);
      setStep(3);

      toast({
        title: "Sukces!",
        description: `Wygenerowano ${response.total_generated} treści.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się wygenerować treści.",
        variant: "destructive",
      });
    }
  };

  const canProceed = () => {
    if (step === 1) return true;
    if (step === 2) return theme.trim().length >= 3;
    return true;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/queue">
            <ChevronLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Rocket className="h-8 w-8 text-primary" />
            Wypełnij kalendarz
          </h1>
          <p className="text-muted-foreground mt-1">
            Wygeneruj wiele treści naraz i zaplanuj publikacje
          </p>
        </div>
      </div>

      {/* Progress indicator */}
      {step < 3 && (
        <div className="flex items-center gap-2">
          {[1, 2].map((s) => (
            <div
              key={s}
              className={cn(
                "h-2 flex-1 rounded-full transition-colors",
                s <= step ? "bg-primary" : "bg-muted"
              )}
            />
          ))}
        </div>
      )}

      {/* Step 1: Platform & Count */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Konfiguracja</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Platform selection */}
            <div className="space-y-3">
              <Label>Platforma</Label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {(Object.keys(platformLabels) as ContentPlatform[])
                  .filter((p) => p !== "other")
                  .map((p) => {
                    const Icon = platformIcons[p];
                    return (
                      <div
                        key={p}
                        className={cn(
                          "p-4 rounded-lg border-2 cursor-pointer transition-colors flex items-center gap-3",
                          platform === p
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        )}
                        onClick={() => setPlatform(p)}
                      >
                        <Icon className="h-6 w-6" />
                        <span className="font-medium">{platformLabels[p]}</span>
                        {platform === p && (
                          <Check className="h-4 w-4 text-primary ml-auto" />
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Count selection */}
            <div className="space-y-3">
              <Label>Ile postów wygenerować?</Label>
              <div className="flex flex-wrap gap-2">
                {countOptions.map((c) => (
                  <Button
                    key={c}
                    type="button"
                    variant={count === c && !customCount ? "default" : "outline"}
                    size="sm"
                    onClick={() => {
                      setCount(c);
                      setCustomCount("");
                    }}
                  >
                    {c}
                  </Button>
                ))}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">lub</span>
                  <Input
                    type="number"
                    min={1}
                    max={30}
                    placeholder="Własna"
                    className="w-20"
                    value={customCount}
                    onChange={(e) => setCustomCount(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Variety selection */}
            <div className="space-y-3">
              <Label>Różnorodność treści</Label>
              <RadioGroup
                value={variety}
                onValueChange={(v) => setVariety(v as VarietyLevel)}
                className="flex gap-4"
              >
                {(Object.keys(varietyLabels) as VarietyLevel[]).map((v) => (
                  <div key={v} className="flex items-center space-x-2">
                    <RadioGroupItem value={v} id={v} />
                    <Label htmlFor={v} className="cursor-pointer">
                      {varietyLabels[v]}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
              <p className="text-sm text-muted-foreground">
                {varietyDescriptions[variety]}
              </p>
            </div>

            {/* Date range */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="auto-schedule"
                  checked={autoSchedule}
                  onCheckedChange={(c) => setAutoSchedule(c as boolean)}
                />
                <Label htmlFor="auto-schedule" className="cursor-pointer">
                  Automatycznie zaplanuj optymalne czasy
                </Label>
              </div>

              {autoSchedule && (
                <div className="grid grid-cols-2 gap-4 pl-6">
                  <div className="space-y-2">
                    <Label>Od</Label>
                    <Input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Do</Label>
                    <Input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Approval */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="require-approval"
                checked={requireApproval}
                onCheckedChange={(c) => setRequireApproval(c as boolean)}
              />
              <Label htmlFor="require-approval" className="cursor-pointer">
                Wymaga mojej zgody przed publikacją
              </Label>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setStep(2)} disabled={!canProceed()}>
                Dalej
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Theme */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Temat treści</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <Label>Temat/motyw przewodni</Label>
              <Textarea
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="np. Promocja wiosenna - nowa kolekcja kremów, rabaty do -30%, darmowa dostawa od 100zł"
                rows={4}
              />
              <p className="text-sm text-muted-foreground">
                Opisz główny temat wszystkich postów. Im więcej szczegółów podasz,
                tym lepiej dopasowane będą treści.
              </p>
            </div>

            {/* Summary */}
            <div className="p-4 rounded-lg bg-muted/50 space-y-2">
              <h4 className="font-medium">Podsumowanie</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>
                  <strong>Platforma:</strong> {platformLabels[platform]}
                </li>
                <li>
                  <strong>Liczba postów:</strong> {effectiveCount}
                </li>
                <li>
                  <strong>Różnorodność:</strong> {varietyLabels[variety]}
                </li>
                {autoSchedule && (
                  <li>
                    <strong>Okres:</strong>{" "}
                    {format(new Date(startDate), "d MMM", { locale: pl })} -{" "}
                    {format(new Date(endDate), "d MMM yyyy", { locale: pl })}
                  </li>
                )}
                <li>
                  <strong>Zatwierdzanie:</strong>{" "}
                  {requireApproval ? "Wymagane" : "Automatyczne"}
                </li>
              </ul>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Wstecz
              </Button>
              <Button
                onClick={handleGenerate}
                disabled={!canProceed() || batchMutation.isPending}
              >
                {batchMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generuj {effectiveCount} postów
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Results */}
      {step === 3 && result && (
        <div className="space-y-6">
          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Wygenerowano</p>
                    <p className="text-3xl font-bold text-green-500">
                      {result.total_generated}
                    </p>
                  </div>
                  <Check className="h-8 w-8 text-green-500/50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Zaplanowano</p>
                    <p className="text-3xl font-bold text-primary">
                      {result.total_scheduled}
                    </p>
                  </div>
                  <Calendar className="h-8 w-8 text-primary/50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Błędy</p>
                    <p className="text-3xl font-bold text-destructive">
                      {result.total_failed}
                    </p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-destructive/50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Żądano</p>
                    <p className="text-3xl font-bold">{result.total_requested}</p>
                  </div>
                  <Rocket className="h-8 w-8 text-muted-foreground/50" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scheduled items */}
          {result.scheduled_items.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Zaplanowane treści</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.scheduled_items.map((item, index) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-3 rounded-lg border bg-card"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-muted-foreground">
                          #{index + 1}
                        </span>
                        <div>
                          <p className="font-medium">{item.title}</p>
                          {item.scheduled_for && (
                            <p className="text-sm text-muted-foreground flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {format(
                                new Date(item.scheduled_for),
                                "EEEE, d MMM yyyy HH:mm",
                                { locale: pl }
                              )}
                            </p>
                          )}
                        </div>
                      </div>
                      <Badge
                        variant={
                          item.status === "scheduled"
                            ? "default"
                            : item.status === "pending_approval"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {item.status === "scheduled"
                          ? "Zaplanowany"
                          : item.status === "pending_approval"
                          ? "Do zatwierdzenia"
                          : item.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            <Button variant="outline" asChild>
              <Link href="/queue">
                <Calendar className="h-4 w-4 mr-2" />
                Zobacz kolejkę
              </Link>
            </Button>
            <Button
              onClick={() => {
                setStep(1);
                setResult(null);
                setTheme("");
              }}
            >
              <Rocket className="h-4 w-4 mr-2" />
              Generuj więcej
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
