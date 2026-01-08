"use client";

import * as React from "react";
import {
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Mail,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Check,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import {
  useCreateScheduleRule,
  type ContentCategory,
  type ApprovalMode,
  type RuleFrequency,
  categoryLabels,
  approvalModeLabels,
  frequencyLabels,
  dayLabels,
} from "@/hooks/use-schedule-rules";
import {
  type ContentPlatform,
  type ContentType,
  platformLabels,
} from "@/hooks/use-scheduled-content";

interface RuleWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const platformIcons: Record<ContentPlatform, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
  twitter: Twitter,
  email: Mail,
  other: Sparkles,
};

const platformContentTypes: Record<ContentPlatform, ContentType> = {
  instagram: "instagram_post",
  facebook: "facebook_post",
  linkedin: "linkedin_post",
  twitter: "twitter_post",
  email: "email_newsletter",
  other: "other",
};

const styles = [
  "profesjonalny",
  "przyjazny",
  "inspirujący",
  "formalny",
  "zabawny",
  "ekspercki",
];

export function RuleWizard({ open, onOpenChange }: RuleWizardProps) {
  const { toast } = useToast();
  const createMutation = useCreateScheduleRule();

  const [step, setStep] = React.useState(1);
  const totalSteps = 4;

  // Step 1: Platform
  const [platform, setPlatform] = React.useState<ContentPlatform>("instagram");

  // Step 2: Content type
  const [category, setCategory] = React.useState<ContentCategory>("motivational");
  const [additionalInstructions, setAdditionalInstructions] = React.useState("");
  const [customPrompt, setCustomPrompt] = React.useState("");
  const [style, setStyle] = React.useState("profesjonalny");

  // Step 3: Schedule
  const [frequency, setFrequency] = React.useState<RuleFrequency>("weekly");
  const [daysOfWeek, setDaysOfWeek] = React.useState<number[]>([0]);
  const [dayOfMonth, setDayOfMonth] = React.useState(1);
  const [time, setTime] = React.useState("08:00");

  // Step 4: Approval & Name
  const [approvalMode, setApprovalMode] = React.useState<ApprovalMode>("require_approval");
  const [notificationMinutes, setNotificationMinutes] = React.useState(60);
  const [name, setName] = React.useState("");
  const [maxQueueSize, setMaxQueueSize] = React.useState(4);

  // Reset when dialog closes
  React.useEffect(() => {
    if (!open) {
      setStep(1);
      setPlatform("instagram");
      setCategory("motivational");
      setAdditionalInstructions("");
      setCustomPrompt("");
      setStyle("profesjonalny");
      setFrequency("weekly");
      setDaysOfWeek([0]);
      setDayOfMonth(1);
      setTime("08:00");
      setApprovalMode("require_approval");
      setNotificationMinutes(60);
      setName("");
      setMaxQueueSize(4);
    }
  }, [open]);

  const handleDayToggle = (day: number) => {
    if (daysOfWeek.includes(day)) {
      setDaysOfWeek(daysOfWeek.filter((d) => d !== day));
    } else {
      setDaysOfWeek([...daysOfWeek, day].sort());
    }
  };

  const canProceed = () => {
    if (step === 1) return true;
    if (step === 2) return category !== "custom" || customPrompt.trim().length > 0;
    if (step === 3) {
      if (frequency === "weekly") return daysOfWeek.length > 0;
      return true;
    }
    if (step === 4) return name.trim().length > 0;
    return true;
  };

  const handleSubmit = async () => {
    try {
      await createMutation.mutateAsync({
        name,
        content_type: platformContentTypes[platform],
        platform,
        content_template: {
          category,
          prompt_template: customPrompt,
          style,
          include_hashtags: true,
          include_emoji: true,
          additional_instructions: additionalInstructions,
        },
        schedule: {
          frequency,
          days_of_week: daysOfWeek,
          day_of_month: frequency === "monthly" ? dayOfMonth : undefined,
          time,
          timezone: "Europe/Warsaw",
        },
        approval_mode: approvalMode,
        notify_before_publish: approvalMode === "require_approval",
        notification_minutes: notificationMinutes,
        max_queue_size: maxQueueSize,
      });

      toast({
        title: "Utworzono",
        description: `Reguła "${name}" została utworzona.`,
      });

      onOpenChange(false);
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się utworzyć reguły.",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Nowa automatyzacja
            <span className="text-sm font-normal text-muted-foreground ml-auto">
              Krok {step}/{totalSteps}
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="py-4">
          {/* Step 1: Platform */}
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Co chcesz automatyzować?
              </p>
              <div className="grid grid-cols-2 gap-3">
                {(Object.keys(platformLabels) as ContentPlatform[])
                  .filter((p) => p !== "other")
                  .map((p) => {
                    const Icon = platformIcons[p];
                    return (
                      <div
                        key={p}
                        className={cn(
                          "p-4 rounded-lg border-2 cursor-pointer transition-colors flex flex-col items-center gap-2",
                          platform === p
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        )}
                        onClick={() => setPlatform(p)}
                      >
                        <Icon className="h-8 w-8" />
                        <span className="font-medium">{platformLabels[p]}</span>
                        {platform === p && (
                          <Check className="h-4 w-4 text-primary" />
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Step 2: Content type */}
          {step === 2 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Jaki rodzaj treści?
              </p>
              <RadioGroup
                value={category}
                onValueChange={(v) => setCategory(v as ContentCategory)}
                className="space-y-2"
              >
                {(Object.keys(categoryLabels) as ContentCategory[]).map((c) => (
                  <div
                    key={c}
                    className={cn(
                      "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                      category === c
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setCategory(c)}
                  >
                    <RadioGroupItem value={c} id={c} />
                    <Label htmlFor={c} className="cursor-pointer flex-1">
                      {categoryLabels[c]}
                    </Label>
                  </div>
                ))}
              </RadioGroup>

              {category === "custom" && (
                <div className="space-y-2 mt-4">
                  <Label>Własny prompt</Label>
                  <Textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="Opisz jakiego rodzaju treści chcesz generować..."
                    rows={3}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label>Dodatkowe instrukcje (opcjonalne)</Label>
                <Textarea
                  value={additionalInstructions}
                  onChange={(e) => setAdditionalInstructions(e.target.value)}
                  placeholder="np. Zawsze wspominaj o darmowej dostawie..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label>Styl/ton komunikacji</Label>
                <Select value={style} onValueChange={setStyle}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {styles.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Step 3: Schedule */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Jak często?</p>

              <RadioGroup
                value={frequency}
                onValueChange={(v) => setFrequency(v as RuleFrequency)}
                className="space-y-2"
              >
                {(Object.keys(frequencyLabels) as RuleFrequency[]).map((f) => (
                  <div
                    key={f}
                    className={cn(
                      "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                      frequency === f
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setFrequency(f)}
                  >
                    <RadioGroupItem value={f} id={f} />
                    <Label htmlFor={f} className="cursor-pointer">
                      {frequencyLabels[f]}
                    </Label>
                  </div>
                ))}
              </RadioGroup>

              {frequency === "weekly" && (
                <div className="space-y-2">
                  <Label>Dni tygodnia</Label>
                  <div className="flex gap-2">
                    {[0, 1, 2, 3, 4, 5, 6].map((day) => (
                      <Button
                        key={day}
                        type="button"
                        variant={daysOfWeek.includes(day) ? "default" : "outline"}
                        size="sm"
                        className="w-10"
                        onClick={() => handleDayToggle(day)}
                      >
                        {dayLabels[day]}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {frequency === "monthly" && (
                <div className="space-y-2">
                  <Label>Dzień miesiąca</Label>
                  <Select
                    value={String(dayOfMonth)}
                    onValueChange={(v) => setDayOfMonth(Number(v))}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 28 }, (_, i) => i + 1).map((d) => (
                        <SelectItem key={d} value={String(d)}>
                          {d}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2">
                <Label>Godzina</Label>
                <Select value={time} onValueChange={setTime}>
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: 24 }, (_, i) => {
                      const h = i.toString().padStart(2, "0");
                      return (
                        <SelectItem key={h} value={`${h}:00`}>
                          {h}:00
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Step 4: Approval & Name */}
          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Jak ma działać publikacja?
              </p>

              <RadioGroup
                value={approvalMode}
                onValueChange={(v) => setApprovalMode(v as ApprovalMode)}
                className="space-y-2"
              >
                {(Object.keys(approvalModeLabels) as ApprovalMode[]).map((m) => (
                  <div
                    key={m}
                    className={cn(
                      "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                      approvalMode === m
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setApprovalMode(m)}
                  >
                    <RadioGroupItem value={m} id={m} />
                    <Label htmlFor={m} className="cursor-pointer">
                      {approvalModeLabels[m]}
                    </Label>
                  </div>
                ))}
              </RadioGroup>

              {approvalMode === "require_approval" && (
                <div className="space-y-2 pl-4">
                  <Label>Powiadom przed publikacją</Label>
                  <Select
                    value={String(notificationMinutes)}
                    onValueChange={(v) => setNotificationMinutes(Number(v))}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">30 minut</SelectItem>
                      <SelectItem value="60">1 godzinę</SelectItem>
                      <SelectItem value="120">2 godziny</SelectItem>
                      <SelectItem value="1440">24 godziny</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2 pt-4 border-t">
                <Label>Nazwa automatyzacji</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="np. Motywacyjne poniedziałki"
                />
              </div>

              <div className="space-y-2">
                <Label>Max treści w kolejce</Label>
                <Select
                  value={String(maxQueueSize)}
                  onValueChange={(v) => setMaxQueueSize(Number(v))}
                >
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[2, 4, 6, 8, 10].map((n) => (
                      <SelectItem key={n} value={String(n)}>
                        {n}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between">
          <Button
            variant="outline"
            onClick={() => (step > 1 ? setStep(step - 1) : onOpenChange(false))}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            {step > 1 ? "Wstecz" : "Anuluj"}
          </Button>

          {step < totalSteps ? (
            <Button onClick={() => setStep(step + 1)} disabled={!canProceed()}>
              Dalej
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!canProceed() || createMutation.isPending}
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Tworzenie...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Utwórz automatyzację
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
