"use client";

import * as React from "react";
import { formatDistanceToNow, format } from "date-fns";
import { pl } from "date-fns/locale";
import {
  AlertCircle,
  Check,
  X,
  Eye,
  Clock,
  CheckCheck,
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Mail,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import {
  useApproveContent,
  useRejectContent,
  useBulkApproveContent,
  type ScheduledContent,
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

interface ApprovalSectionProps {
  items: ScheduledContent[];
  onView: (item: ScheduledContent) => void;
  isLoading?: boolean;
}

export function ApprovalSection({ items, onView, isLoading }: ApprovalSectionProps) {
  const { toast } = useToast();
  const approveMutation = useApproveContent();
  const rejectMutation = useRejectContent();
  const bulkApproveMutation = useBulkApproveContent();

  const [processingIds, setProcessingIds] = React.useState<Set<string>>(new Set());

  if (items.length === 0) {
    return null;
  }

  const handleApprove = async (item: ScheduledContent) => {
    setProcessingIds((prev) => new Set(prev).add(item.id));
    try {
      await approveMutation.mutateAsync({ id: item.id });
      toast({
        title: "Zatwierdzono",
        description: `"${item.title}" została zatwierdzona do publikacji.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się zatwierdzić treści.",
        variant: "destructive",
      });
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  };

  const handleReject = async (item: ScheduledContent) => {
    setProcessingIds((prev) => new Set(prev).add(item.id));
    try {
      await rejectMutation.mutateAsync(item.id);
      toast({
        title: "Odrzucono",
        description: `"${item.title}" została przeniesiona do szkiców.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się odrzucić treści.",
        variant: "destructive",
      });
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  };

  const handleApproveAll = async () => {
    const ids = items.map((item) => item.id);
    try {
      await bulkApproveMutation.mutateAsync(ids);
      toast({
        title: "Zatwierdzono wszystkie",
        description: `${ids.length} treści zostało zatwierdzonych.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się zatwierdzić treści.",
        variant: "destructive",
      });
    }
  };

  return (
    <Card className="border-orange-500/50 bg-orange-500/5">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <AlertCircle className="h-5 w-5" />
            Wymaga zatwierdzenia ({items.length})
          </CardTitle>
          {items.length > 1 && (
            <Button
              size="sm"
              onClick={handleApproveAll}
              disabled={bulkApproveMutation.isPending}
            >
              {bulkApproveMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <CheckCheck className="h-4 w-4 mr-1" />
              )}
              Zatwierdź wszystkie
            </Button>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          Treści czekające na Twoją decyzję przed publikacją
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item) => {
          const Icon = platformIcons[item.platform];
          const isProcessing = processingIds.has(item.id);
          const timeUntilPublish = item.scheduled_for
            ? formatDistanceToNow(new Date(item.scheduled_for), { locale: pl })
            : null;

          return (
            <div
              key={item.id}
              className={cn(
                "p-4 rounded-lg border bg-card transition-opacity",
                isProcessing && "opacity-50"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <Icon className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-medium truncate">{item.title}</h4>
                      <Badge variant="outline" className="flex-shrink-0">
                        {platformLabels[item.platform]}
                      </Badge>
                    </div>

                    <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                      {typeof item.content?.text === "string"
                        ? item.content.text
                        : typeof item.content?.caption === "string"
                        ? item.content.caption
                        : "Brak treści"}
                    </p>

                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      {item.scheduled_for && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Publikacja za {timeUntilPublish}
                        </span>
                      )}
                      {item.source_rule_id && (
                        <Badge variant="secondary" className="text-xs">
                          Automatyzacja
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onView(item)}
                    disabled={isProcessing}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-green-600 hover:text-green-700 hover:bg-green-100 dark:hover:bg-green-900/20"
                    onClick={() => handleApprove(item)}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={() => handleReject(item)}
                    disabled={isProcessing}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
