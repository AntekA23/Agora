"use client";

import * as React from "react";
import { formatDatePL } from "@/lib/utils";
import {
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Mail,
  FileText,
  Calendar,
  Clock,
  User,
  Tag,
  ExternalLink,
  Copy,
  Check,
  Pencil,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  type ScheduledContent,
  type ContentPlatform,
  statusLabels,
  platformLabels,
  contentTypeLabels,
} from "@/hooks/use-scheduled-content";
import { useToast } from "@/hooks/use-toast";

const platformIcons: Record<ContentPlatform, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
  twitter: Twitter,
  email: Mail,
  other: FileText,
};

const platformColors: Record<ContentPlatform, string> = {
  instagram: "text-pink-500",
  facebook: "text-blue-600",
  linkedin: "text-blue-700",
  twitter: "text-sky-500",
  email: "text-amber-500",
  other: "text-muted-foreground",
};

const statusBadgeVariants: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  draft: "outline",
  queued: "secondary",
  scheduled: "default",
  pending_approval: "secondary",
  publishing: "default",
  published: "default",
  failed: "destructive",
};

interface PreviewDialogProps {
  item: ScheduledContent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit?: () => void;
}

export function PreviewDialog({
  item,
  open,
  onOpenChange,
  onEdit,
}: PreviewDialogProps) {
  const { toast } = useToast();
  const [copied, setCopied] = React.useState(false);

  if (!item) return null;

  const PlatformIcon = platformIcons[item.platform];
  const platformColor = platformColors[item.platform];

  // Extract content text
  const content = item.content as {
    text?: string;
    caption?: string;
    hashtags?: string[];
  };
  const contentText = content?.text || content?.caption || "";
  const hashtags = content?.hashtags || [];

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(contentText);
      setCopied(true);
      toast({
        title: "Skopiowano",
        description: "Treść została skopiowana do schowka.",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się skopiować treści.",
        variant: "destructive",
      });
    }
  };

  const canEdit = !["published", "publishing"].includes(item.status);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-muted ${platformColor}`}>
                <PlatformIcon className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-left">{item.title}</DialogTitle>
                <p className="text-sm text-muted-foreground">
                  {platformLabels[item.platform]}
                </p>
              </div>
            </div>
            <Badge variant={statusBadgeVariants[item.status]}>
              {statusLabels[item.status]}
            </Badge>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          {/* Content preview */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
              {contentText || (
                <span className="text-muted-foreground italic">
                  Brak treści tekstowej
                </span>
              )}
            </div>

            {/* Hashtags */}
            {hashtags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {hashtags.map((tag) => (
                  <span
                    key={tag}
                    className="text-sm text-primary hover:underline cursor-default"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Media preview */}
          {item.media_urls && item.media_urls.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Media</p>
              <div className="grid grid-cols-2 gap-2">
                {item.media_urls.map((url, index) => (
                  <div
                    key={index}
                    className="aspect-square rounded-lg border bg-muted overflow-hidden"
                  >
                    <img
                      src={url}
                      alt={`Media ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Typ:</span>
                <span>{contentTypeLabels[item.content_type]}</span>
              </div>

              {item.scheduled_for && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Zaplanowano:</span>
                  <span>
                    {formatDatePL(item.scheduled_for, {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              )}

              {item.published_at && (
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">Opublikowano:</span>
                  <span>
                    {formatDatePL(item.published_at, {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Utworzono:</span>
                <span>
                  {formatDatePL(item.created_at, {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>

              {item.requires_approval && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Zatwierdzenie:</span>
                  <span>
                    {item.approved_by ? "Zatwierdzono" : "Wymagane"}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Engagement stats (if published) */}
          {item.status === "published" && item.engagement_stats && (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-sm font-medium">Statystyki</p>
                <div className="flex gap-6">
                  {item.engagement_stats.likes !== undefined && (
                    <div className="text-center">
                      <p className="text-2xl font-bold">
                        {item.engagement_stats.likes}
                      </p>
                      <p className="text-xs text-muted-foreground">Polubienia</p>
                    </div>
                  )}
                  {item.engagement_stats.comments !== undefined && (
                    <div className="text-center">
                      <p className="text-2xl font-bold">
                        {item.engagement_stats.comments}
                      </p>
                      <p className="text-xs text-muted-foreground">Komentarze</p>
                    </div>
                  )}
                  {item.engagement_stats.shares !== undefined && (
                    <div className="text-center">
                      <p className="text-2xl font-bold">
                        {item.engagement_stats.shares}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Udostępnienia
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Error message */}
          {item.status === "failed" && item.error_message && (
            <>
              <Separator />
              <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
                <p className="text-sm font-medium text-destructive">
                  Błąd publikacji
                </p>
                <p className="text-sm text-destructive/80 mt-1">
                  {item.error_message}
                </p>
              </div>
            </>
          )}

          {/* External link */}
          {item.platform_post_url && (
            <a
              href={item.platform_post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              Zobacz na {platformLabels[item.platform]}
            </a>
          )}
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between">
          <Button variant="outline" onClick={handleCopy}>
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Skopiowano
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-2" />
                Kopiuj treść
              </>
            )}
          </Button>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Zamknij
            </Button>
            {canEdit && onEdit && (
              <Button onClick={onEdit}>
                <Pencil className="h-4 w-4 mr-2" />
                Edytuj
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
