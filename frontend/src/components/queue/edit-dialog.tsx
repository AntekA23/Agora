"use client";

import * as React from "react";
import { CalendarIcon, Loader2, Save } from "lucide-react";
import { formatDatePL } from "@/lib/utils";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  type ScheduledContent,
  type ContentStatus,
  useUpdateScheduledContent,
  statusLabels,
} from "@/hooks/use-scheduled-content";
import { useToast } from "@/hooks/use-toast";

interface EditDialogProps {
  item: ScheduledContent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

// Available statuses for editing (not all statuses can be set manually)
const editableStatuses: ContentStatus[] = [
  "draft",
  "queued",
  "scheduled",
  "pending_approval",
];

export function EditDialog({
  item,
  open,
  onOpenChange,
  onSuccess,
}: EditDialogProps) {
  const { toast } = useToast();
  const updateMutation = useUpdateScheduledContent();

  // Form state
  const [title, setTitle] = React.useState("");
  const [contentText, setContentText] = React.useState("");
  const [scheduledDate, setScheduledDate] = React.useState<Date | undefined>();
  const [scheduledTime, setScheduledTime] = React.useState("12:00");
  const [status, setStatus] = React.useState<ContentStatus>("draft");
  const [requiresApproval, setRequiresApproval] = React.useState(false);

  // Reset form when item changes
  React.useEffect(() => {
    if (item) {
      setTitle(item.title);

      // Extract text content
      const content = item.content as { text?: string; caption?: string };
      setContentText(content?.text || content?.caption || "");

      // Parse scheduled date/time
      if (item.scheduled_for) {
        const date = new Date(item.scheduled_for);
        setScheduledDate(date);
        // Extract time in Polish timezone
        setScheduledTime(formatDatePL(date, { hour: "2-digit", minute: "2-digit" }));
      } else {
        setScheduledDate(undefined);
        setScheduledTime("12:00");
      }

      setStatus(item.status);
      setRequiresApproval(item.requires_approval);
    }
  }, [item]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!item) return;

    try {
      // Build scheduled_for from date + time
      let scheduled_for: string | undefined;
      if (scheduledDate) {
        const [hours, minutes] = scheduledTime.split(":").map(Number);
        const dateWithTime = new Date(scheduledDate);
        dateWithTime.setHours(hours, minutes, 0, 0);
        scheduled_for = dateWithTime.toISOString();
      }

      // Build content object
      const contentObj = item.content as Record<string, unknown>;
      const updatedContent = {
        ...contentObj,
        text: contentText,
        caption: contentText, // Update both for compatibility
      };

      await updateMutation.mutateAsync({
        id: item.id,
        data: {
          title,
          content: updatedContent,
          scheduled_for,
          status,
          requires_approval: requiresApproval,
        },
      });

      toast({
        title: "Zapisano",
        description: "Treść została zaktualizowana.",
      });

      onOpenChange(false);
      onSuccess?.();
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się zapisać zmian.",
        variant: "destructive",
      });
    }
  };

  // Can only edit certain statuses
  const canEdit = item && !["published", "publishing"].includes(item.status);

  if (!item) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edytuj treść</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Tytuł</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Tytuł treści..."
              disabled={!canEdit}
            />
          </div>

          {/* Content text */}
          <div className="space-y-2">
            <Label htmlFor="content">Treść</Label>
            <Textarea
              id="content"
              value={contentText}
              onChange={(e) => setContentText(e.target.value)}
              placeholder="Treść do publikacji..."
              rows={6}
              disabled={!canEdit}
            />
          </div>

          {/* Scheduled date/time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Data publikacji</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !scheduledDate && "text-muted-foreground"
                    )}
                    disabled={!canEdit}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {scheduledDate ? (
                      formatDatePL(scheduledDate, { day: "numeric", month: "short", year: "numeric" })
                    ) : (
                      <span>Wybierz datę</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={scheduledDate}
                    onSelect={setScheduledDate}
                    disabled={(date) => date < new Date()}
                    locale={pl}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time">Godzina</Label>
              <Input
                id="time"
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                disabled={!canEdit}
              />
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={status}
              onValueChange={(v) => setStatus(v as ContentStatus)}
              disabled={!canEdit}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {editableStatuses.map((s) => (
                  <SelectItem key={s} value={s}>
                    {statusLabels[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Requires approval */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_approval"
              checked={requiresApproval}
              onCheckedChange={(checked) =>
                setRequiresApproval(checked === true)
              }
              disabled={!canEdit}
            />
            <Label
              htmlFor="requires_approval"
              className="text-sm font-normal cursor-pointer"
            >
              Wymagaj zatwierdzenia przed publikacją
            </Label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Anuluj
            </Button>
            <Button type="submit" disabled={!canEdit || updateMutation.isPending}>
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Zapisywanie...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Zapisz
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
