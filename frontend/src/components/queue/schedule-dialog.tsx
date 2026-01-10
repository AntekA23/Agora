"use client";

import * as React from "react";
import { pl } from "date-fns/locale";
import { formatDatePL, formatDateOnlyPL } from "@/lib/utils";
import {
  Calendar as CalendarIcon,
  Clock,
  Loader2,
  Sparkles,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import {
  useCreateScheduledContent,
  type ContentType,
  type ContentPlatform,
  platformLabels,
  contentTypeLabels,
} from "@/hooks/use-scheduled-content";
import {
  useSchedulingSuggestions,
  formatConfidence,
  type SuggestTimeResponse,
  type TimeAlternative,
} from "@/hooks/use-scheduling-suggestions";

interface ScheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  content: {
    text?: string;
    hashtags?: string[];
    caption?: string;
  };
  contentType: ContentType;
  platform: ContentPlatform;
  sourceTaskId?: string;
  sourceConversationId?: string;
  onSuccess?: () => void;
}

type ScheduleOption = "queue" | "schedule" | "ai";

export function ScheduleDialog({
  open,
  onOpenChange,
  content,
  contentType,
  platform,
  sourceTaskId,
  sourceConversationId,
  onSuccess,
}: ScheduleDialogProps) {
  const createMutation = useCreateScheduledContent();
  const suggestionsMutation = useSchedulingSuggestions();

  const [title, setTitle] = React.useState("");
  const [scheduleOption, setScheduleOption] =
    React.useState<ScheduleOption>("queue");
  const [selectedDate, setSelectedDate] = React.useState<Date | undefined>();
  const [selectedTime, setSelectedTime] = React.useState("12:00");
  const [suggestions, setSuggestions] =
    React.useState<SuggestTimeResponse | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = React.useState<
    "primary" | number | "custom"
  >("primary");

  // Generate title from content
  React.useEffect(() => {
    if (open && !title) {
      const text = content?.text || content?.caption || "";
      const firstLine = text.split("\n")[0];
      const generated =
        firstLine.slice(0, 50) + (firstLine.length > 50 ? "..." : "");
      setTitle(
        generated ||
          `${contentTypeLabels[contentType]} - ${formatDateOnlyPL(new Date())}`
      );
    }
  }, [open, content, contentType, title]);

  // Reset state when dialog closes
  React.useEffect(() => {
    if (!open) {
      setTitle("");
      setScheduleOption("queue");
      setSelectedDate(undefined);
      setSelectedTime("12:00");
      setSuggestions(null);
      setSelectedSuggestion("primary");
    }
  }, [open]);

  // Fetch suggestions when "ai" option is selected
  React.useEffect(() => {
    if (scheduleOption === "ai" && !suggestions && !suggestionsMutation.isPending) {
      suggestionsMutation.mutate(
        {
          content_type: contentType,
          platform,
          content,
          preferences: {
            avoid_weekends: false,
          },
        },
        {
          onSuccess: (data) => {
            setSuggestions(data);
            setSelectedSuggestion("primary");
          },
        }
      );
    }
  }, [scheduleOption, suggestions, contentType, platform, content, suggestionsMutation]);

  const handleSubmit = async () => {
    let scheduledFor: string | undefined;

    if (scheduleOption === "schedule" && selectedDate) {
      const [hours, minutes] = selectedTime.split(":").map(Number);
      const date = new Date(selectedDate);
      date.setHours(hours, minutes, 0, 0);
      scheduledFor = date.toISOString();
    } else if (scheduleOption === "ai" && suggestions) {
      if (selectedSuggestion === "primary") {
        scheduledFor = suggestions.suggested_time;
      } else if (selectedSuggestion === "custom" && selectedDate) {
        const [hours, minutes] = selectedTime.split(":").map(Number);
        const date = new Date(selectedDate);
        date.setHours(hours, minutes, 0, 0);
        scheduledFor = date.toISOString();
      } else if (typeof selectedSuggestion === "number") {
        scheduledFor = suggestions.alternatives[selectedSuggestion]?.time;
      }
    }

    try {
      await createMutation.mutateAsync({
        title,
        content_type: contentType,
        platform,
        content,
        scheduled_for: scheduledFor,
        source_task_id: sourceTaskId,
        source_conversation_id: sourceConversationId,
        requires_approval: false,
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      console.error("Failed to schedule content:", error);
    }
  };

  // Generate time options
  const timeOptions = React.useMemo(() => {
    const options = [];
    for (let hour = 6; hour <= 23; hour++) {
      for (const minute of ["00", "30"]) {
        options.push(`${hour.toString().padStart(2, "0")}:${minute}`);
      }
    }
    return options;
  }, []);

  const formatSuggestionDate = (isoString: string) => {
    return formatDatePL(isoString, {
      weekday: "long",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CalendarIcon className="h-5 w-5" />
            Dodaj do kolejki
          </DialogTitle>
          <DialogDescription>
            Zaplanuj publikację na {platformLabels[platform]}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Tytuł roboczy</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="np. Post o promocji wiosennej"
            />
          </div>

          {/* Schedule Options */}
          <div className="space-y-3">
            <Label>Kiedy opublikować?</Label>
            <RadioGroup
              value={scheduleOption}
              onValueChange={(v) => setScheduleOption(v as ScheduleOption)}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="queue" id="queue" />
                <Label htmlFor="queue" className="font-normal cursor-pointer">
                  Dodaj do kolejki (opublikuję później)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="ai" id="ai" />
                <Label htmlFor="ai" className="font-normal cursor-pointer flex items-center gap-1">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Pozwól AI wybrać optymalny czas
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="schedule" id="schedule" />
                <Label
                  htmlFor="schedule"
                  className="font-normal cursor-pointer"
                >
                  Zaplanuj na konkretny czas
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* AI Suggestions */}
          {scheduleOption === "ai" && (
            <div className="space-y-3 pl-6">
              {suggestionsMutation.isPending ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analizuję optymalny czas...
                </div>
              ) : suggestions ? (
                <div className="space-y-3">
                  {/* Primary Suggestion */}
                  <div
                    className={cn(
                      "p-3 rounded-lg border-2 cursor-pointer transition-colors",
                      selectedSuggestion === "primary"
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedSuggestion("primary")}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        <span className="font-medium">
                          {formatSuggestionDate(suggestions.suggested_time)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatConfidence(suggestions.confidence)} pewności
                        </span>
                        {selectedSuggestion === "primary" && (
                          <Check className="h-4 w-4 text-primary" />
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {suggestions.reasoning}
                    </p>
                  </div>

                  {/* Alternatives */}
                  {suggestions.alternatives.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground">
                        Alternatywy:
                      </p>
                      {suggestions.alternatives.map(
                        (alt: TimeAlternative, index: number) => (
                          <div
                            key={index}
                            className={cn(
                              "p-2 rounded-lg border cursor-pointer transition-colors text-sm",
                              selectedSuggestion === index
                                ? "border-primary bg-primary/5"
                                : "border-border hover:border-primary/50"
                            )}
                            onClick={() => setSelectedSuggestion(index)}
                          >
                            <div className="flex items-center justify-between">
                              <span>{formatSuggestionDate(alt.time)}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">
                                  {formatConfidence(alt.score)}
                                </span>
                                {selectedSuggestion === index && (
                                  <Check className="h-4 w-4 text-primary" />
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  )}

                  {/* Custom option */}
                  <div
                    className={cn(
                      "p-2 rounded-lg border cursor-pointer transition-colors text-sm",
                      selectedSuggestion === "custom"
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedSuggestion("custom")}
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      <span>Wybierz własny termin</span>
                      {selectedSuggestion === "custom" && (
                        <Check className="h-4 w-4 text-primary ml-auto" />
                      )}
                    </div>
                  </div>

                  {/* Custom Date/Time Picker */}
                  {selectedSuggestion === "custom" && (
                    <div className="flex gap-3 mt-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-[160px] justify-start text-left font-normal",
                              !selectedDate && "text-muted-foreground"
                            )}
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {selectedDate ? (
                              formatDatePL(selectedDate, { day: "numeric", month: "short", year: "numeric" })
                            ) : (
                              "Wybierz datę"
                            )}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={selectedDate}
                            onSelect={setSelectedDate}
                            disabled={(date) => date < new Date()}
                            locale={pl}
                          />
                        </PopoverContent>
                      </Popover>

                      <Select
                        value={selectedTime}
                        onValueChange={setSelectedTime}
                      >
                        <SelectTrigger className="w-[100px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {timeOptions.map((time) => (
                            <SelectItem key={time} value={time}>
                              {time}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              ) : suggestionsMutation.isError ? (
                <div className="text-sm text-destructive">
                  Nie udało się pobrać sugestii. Wybierz inną opcję.
                </div>
              ) : null}
            </div>
          )}

          {/* Date & Time Picker (manual option) */}
          {scheduleOption === "schedule" && (
            <div className="space-y-3 pl-6">
              <div className="flex gap-3">
                {/* Date Picker */}
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[180px] justify-start text-left font-normal",
                        !selectedDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {selectedDate ? (
                        formatDatePL(selectedDate, { day: "numeric", month: "short", year: "numeric" })
                      ) : (
                        "Wybierz datę"
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={selectedDate}
                      onSelect={setSelectedDate}
                      initialFocus
                      disabled={(date) => date < new Date()}
                      locale={pl}
                    />
                  </PopoverContent>
                </Popover>

                {/* Time Picker */}
                <Select value={selectedTime} onValueChange={setSelectedTime}>
                  <SelectTrigger className="w-[120px]">
                    <Clock className="mr-2 h-4 w-4" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {timeOptions.map((time) => (
                      <SelectItem key={time} value={time}>
                        {time}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Content Preview */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">Podgląd treści</Label>
            <div className="p-3 bg-muted rounded-lg text-sm max-h-32 overflow-y-auto">
              {content?.text || content?.caption || "Brak treści"}
              {content?.hashtags && content.hashtags.length > 0 && (
                <p className="text-muted-foreground mt-2">
                  {content.hashtags.join(" ")}
                </p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Anuluj
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={
              createMutation.isPending ||
              !title ||
              (scheduleOption === "schedule" && !selectedDate) ||
              (scheduleOption === "ai" &&
                selectedSuggestion === "custom" &&
                !selectedDate)
            }
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Dodawanie...
              </>
            ) : (
              "Dodaj do kolejki"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
