"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Calendar,
  Filter,
  Plus,
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
  Loader2,
  AlertCircle,
  Rocket,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import {
  useScheduledContent,
  useScheduledContentStats,
  useDeleteScheduledContent,
  useApproveContent,
  useRejectContent,
  type ScheduledContent,
  type ContentStatus,
  type ContentPlatform,
  platformLabels,
} from "@/hooks/use-scheduled-content";
import { QueueList } from "@/components/queue/queue-list";
import { EditDialog } from "@/components/queue/edit-dialog";
import { PreviewDialog } from "@/components/queue/preview-dialog";
import { ApprovalSection } from "@/components/queue/approval-section";

export default function QueuePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  // Filters
  const [statusFilter, setStatusFilter] = React.useState<ContentStatus | "all">("all");
  const [platformFilter, setPlatformFilter] = React.useState<ContentPlatform | "all">("all");

  // Dialog state
  const [deleteItem, setDeleteItem] = React.useState<ScheduledContent | null>(null);
  const [editItem, setEditItem] = React.useState<ScheduledContent | null>(null);
  const [previewItem, setPreviewItem] = React.useState<ScheduledContent | null>(null);

  // Build filters
  const filters = React.useMemo(() => {
    const f: {
      status?: ContentStatus[];
      platform?: ContentPlatform[];
      per_page: number;
    } = { per_page: 50 };

    if (statusFilter !== "all") {
      f.status = [statusFilter];
    }
    if (platformFilter !== "all") {
      f.platform = [platformFilter];
    }

    return f;
  }, [statusFilter, platformFilter]);

  // Queries
  const { data, isLoading, error } = useScheduledContent(filters);
  const { data: stats } = useScheduledContentStats();

  // Mutations
  const deleteMutation = useDeleteScheduledContent();
  const approveMutation = useApproveContent();
  const rejectMutation = useRejectContent();

  // Handlers
  const handleView = (item: ScheduledContent) => {
    setPreviewItem(item);
  };

  const handleEdit = (item: ScheduledContent) => {
    setEditItem(item);
  };

  const handleDelete = async () => {
    if (!deleteItem) return;

    try {
      await deleteMutation.mutateAsync(deleteItem.id);
      toast({
        title: "Usunięto",
        description: "Treść została usunięta z kolejki.",
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się usunąć treści.",
        variant: "destructive",
      });
    } finally {
      setDeleteItem(null);
    }
  };

  const handleApprove = async (item: ScheduledContent) => {
    try {
      await approveMutation.mutateAsync({ id: item.id });
      toast({
        title: "Zatwierdzono",
        description: "Treść została zatwierdzona do publikacji.",
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się zatwierdzić treści.",
        variant: "destructive",
      });
    }
  };

  const handleReject = async (item: ScheduledContent) => {
    try {
      await rejectMutation.mutateAsync(item.id);
      toast({
        title: "Odrzucono",
        description: "Treść została przeniesiona do szkiców.",
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się odrzucić treści.",
        variant: "destructive",
      });
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>Nie można załadować kolejki</span>
      </div>
    );
  }

  const pendingApprovalCount = stats?.by_status?.pending_approval || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calendar className="h-8 w-8 text-primary" />
            Kolejka treści
          </h1>
          <p className="text-muted-foreground mt-1">
            Zarządzaj zaplanowanymi publikacjami
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/queue/batch">
              <Rocket className="h-4 w-4 mr-2" />
              Wypełnij kalendarz
            </Link>
          </Button>
          <Button onClick={() => router.push("/chat")}>
            <Plus className="h-4 w-4 mr-2" />
            Nowa treść
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Wszystkie</p>
                <p className="text-3xl font-bold">{stats?.total || 0}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-muted-foreground/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Zaplanowane</p>
                <p className="text-3xl font-bold">
                  {stats?.scheduled_this_week || 0}
                </p>
              </div>
              <Clock className="h-8 w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Opublikowane</p>
                <p className="text-3xl font-bold text-green-500">
                  {stats?.published_this_week || 0}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Do zatwierdzenia</p>
                <p className="text-3xl font-bold text-yellow-500">
                  {pendingApprovalCount}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Filtry:</span>
        </div>

        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as ContentStatus | "all")}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Wszystkie statusy</SelectItem>
            <SelectItem value="draft">Szkice</SelectItem>
            <SelectItem value="queued">W kolejce</SelectItem>
            <SelectItem value="scheduled">Zaplanowane</SelectItem>
            <SelectItem value="pending_approval">Do zatwierdzenia</SelectItem>
            <SelectItem value="published">Opublikowane</SelectItem>
            <SelectItem value="failed">Błędy</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={platformFilter}
          onValueChange={(v) => setPlatformFilter(v as ContentPlatform | "all")}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Platforma" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Wszystkie platformy</SelectItem>
            {Object.entries(platformLabels).map(([key, label]) => (
              <SelectItem key={key} value={key}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Approval Section */}
      {statusFilter === "all" && (
        <ApprovalSection
          items={data?.items.filter((item) => item.status === "pending_approval") || []}
          onView={handleView}
          isLoading={isLoading}
        />
      )}

      {/* Queue List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {statusFilter === "all"
              ? "Wszystkie treści"
              : `Filtr: ${statusFilter}`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <QueueList
            items={data?.items || []}
            isLoading={isLoading}
            groupByStatus={statusFilter === "all"}
            onView={handleView}
            onEdit={handleEdit}
            onDelete={setDeleteItem}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteItem} onOpenChange={() => setDeleteItem(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Usuń treść</AlertDialogTitle>
            <AlertDialogDescription>
              Czy na pewno chcesz usunąć &quot;{deleteItem?.title}&quot;? Ta
              akcja jest nieodwracalna.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Usuń"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Dialog */}
      <EditDialog
        item={editItem}
        open={!!editItem}
        onOpenChange={(open) => !open && setEditItem(null)}
      />

      {/* Preview Dialog */}
      <PreviewDialog
        item={previewItem}
        open={!!previewItem}
        onOpenChange={(open) => !open && setPreviewItem(null)}
        onEdit={() => {
          if (previewItem) {
            setEditItem(previewItem);
            setPreviewItem(null);
          }
        }}
      />
    </div>
  );
}
