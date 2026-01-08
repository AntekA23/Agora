"use client";

import { formatDistanceToNow, format } from "date-fns";
import { pl } from "date-fns/locale";
import {
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Mail,
  FileText,
  MoreHorizontal,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Pencil,
  Trash2,
  Check,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  type ScheduledContent,
  type ContentPlatform,
  type ContentStatus,
  statusLabels,
  platformLabels,
} from "@/hooks/use-scheduled-content";

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

const statusBadgeVariants: Record<ContentStatus, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "outline",
  queued: "secondary",
  scheduled: "default",
  pending_approval: "secondary",
  publishing: "default",
  published: "default",
  failed: "destructive",
};

interface QueueItemProps {
  item: ScheduledContent;
  onView?: (item: ScheduledContent) => void;
  onEdit?: (item: ScheduledContent) => void;
  onDelete?: (item: ScheduledContent) => void;
  onApprove?: (item: ScheduledContent) => void;
  onReject?: (item: ScheduledContent) => void;
}

export function QueueItem({
  item,
  onView,
  onEdit,
  onDelete,
  onApprove,
  onReject,
}: QueueItemProps) {
  const PlatformIcon = platformIcons[item.platform];
  const platformColor = platformColors[item.platform];

  const formatScheduledTime = () => {
    if (!item.scheduled_for) return "Brak terminu";
    const date = new Date(item.scheduled_for);
    const now = new Date();
    const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return format(date, "d MMM yyyy, HH:mm", { locale: pl });
    } else if (diffDays === 0) {
      return `Dziś o ${format(date, "HH:mm")}`;
    } else if (diffDays === 1) {
      return `Jutro o ${format(date, "HH:mm")}`;
    } else if (diffDays < 7) {
      return format(date, "EEEE, HH:mm", { locale: pl });
    } else {
      return format(date, "d MMM, HH:mm", { locale: pl });
    }
  };

  const getContentPreview = () => {
    const content = item.content as { text?: string; caption?: string };
    const text = content?.text || content?.caption || "";
    if (text.length > 100) {
      return text.slice(0, 100) + "...";
    }
    return text;
  };

  const isPendingApproval = item.status === "pending_approval";
  const canEdit = !["published", "publishing"].includes(item.status);
  const canDelete = item.status !== "published";

  return (
    <div className="group relative p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors">
      <div className="flex items-start gap-4">
        {/* Platform Icon */}
        <div className={`p-2 rounded-lg bg-muted ${platformColor}`}>
          <PlatformIcon className="h-5 w-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="font-medium truncate">{item.title}</h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                {platformLabels[item.platform]}
                {item.scheduled_for && (
                  <>
                    {" "}
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatScheduledTime()}
                    </span>
                  </>
                )}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={statusBadgeVariants[item.status]}>
                {statusLabels[item.status]}
              </Badge>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onView?.(item)}>
                    <Eye className="h-4 w-4 mr-2" />
                    Podgląd
                  </DropdownMenuItem>
                  {canEdit && (
                    <DropdownMenuItem onClick={() => onEdit?.(item)}>
                      <Pencil className="h-4 w-4 mr-2" />
                      Edytuj
                    </DropdownMenuItem>
                  )}
                  {isPendingApproval && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => onApprove?.(item)}>
                        <Check className="h-4 w-4 mr-2" />
                        Zatwierdź
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onReject?.(item)}>
                        <X className="h-4 w-4 mr-2" />
                        Odrzuć
                      </DropdownMenuItem>
                    </>
                  )}
                  {canDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => onDelete?.(item)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Usuń
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Content Preview */}
          {getContentPreview() && (
            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
              {getContentPreview()}
            </p>
          )}

          {/* Status-specific info */}
          {item.status === "published" && item.engagement_stats && (
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              {item.engagement_stats.likes !== undefined && (
                <span>{item.engagement_stats.likes} polubień</span>
              )}
              {item.engagement_stats.comments !== undefined && (
                <span>{item.engagement_stats.comments} komentarzy</span>
              )}
            </div>
          )}

          {item.status === "failed" && item.error_message && (
            <div className="flex items-center gap-2 mt-2 text-xs text-destructive">
              <AlertCircle className="h-3 w-3" />
              {item.error_message}
            </div>
          )}

          {isPendingApproval && (
            <div className="flex items-center gap-2 mt-3">
              <Button
                size="sm"
                variant="default"
                onClick={() => onApprove?.(item)}
              >
                <Check className="h-4 w-4 mr-1" />
                Zatwierdź
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onReject?.(item)}
              >
                <X className="h-4 w-4 mr-1" />
                Odrzuć
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
