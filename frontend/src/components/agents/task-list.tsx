"use client";

import { useTasks, useDeleteTask } from "@/hooks/use-tasks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Trash2, Eye, RefreshCw } from "lucide-react";
import { useState } from "react";
import type { TaskStatus } from "@/types/task";

interface TaskListProps {
  onSelectTask?: (taskId: string) => void;
  department?: string;
}

const statusConfig: Record<TaskStatus, { label: string; variant: "secondary" | "info" | "success" | "destructive" }> = {
  pending: { label: "Oczekujace", variant: "secondary" },
  processing: { label: "W trakcie", variant: "info" },
  completed: { label: "Ukonczone", variant: "success" },
  failed: { label: "Blad", variant: "destructive" },
};

const agentLabels: Record<string, string> = {
  instagram_specialist: "Instagram",
  copywriter: "Copywriter",
};

export function TaskList({ onSelectTask, department }: TaskListProps) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useTasks({
    page,
    per_page: 10,
    department,
    status: statusFilter || undefined,
  });

  const deleteTask = useDeleteTask();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pl-PL", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-destructive">
          Blad ladowania zadan
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Historia zadan</CardTitle>
        <div className="flex items-center gap-2">
          <Select
            value={statusFilter || "all"}
            onValueChange={(v) => {
              setStatusFilter(v === "all" ? "" : v);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filtruj" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Wszystkie</SelectItem>
              <SelectItem value="pending">Oczekujace</SelectItem>
              <SelectItem value="processing">W trakcie</SelectItem>
              <SelectItem value="completed">Ukonczone</SelectItem>
              <SelectItem value="failed">Bledy</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="ghost" size="icon" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !data?.tasks.length ? (
          <p className="text-muted-foreground text-sm text-center py-8">
            Brak zadan. Stworz pierwsze zadanie powyzej.
          </p>
        ) : (
          <div className="space-y-2">
            {data.tasks.map((task) => {
              const status = statusConfig[task.status];
              return (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">
                        {agentLabels[task.agent] || task.agent}
                      </span>
                      <Badge variant={status.variant} className="text-xs">
                        {status.label}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {(task.input as { brief?: string }).brief?.slice(0, 60)}...
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(task.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onSelectTask?.(task.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteTask.mutate(task.id)}
                      disabled={deleteTask.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}

            {/* Pagination */}
            {data.total > 10 && (
              <div className="flex justify-center gap-2 pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Poprzednia
                </Button>
                <span className="flex items-center text-sm text-muted-foreground">
                  {page} / {Math.ceil(data.total / 10)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(data.total / 10)}
                >
                  Nastepna
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
