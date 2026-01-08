"use client";

import { useState } from "react";
import { useTask, useRetryTask } from "@/hooks/use-tasks";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Copy,
  Check,
  AlertCircle,
  Download,
  RefreshCw,
  CalendarPlus,
  Clock,
  Image,
  FileText,
  Hash,
  X,
  Instagram,
} from "lucide-react";
import { ScheduleDialog } from "@/components/queue/schedule-dialog";
import type { ContentType, ContentPlatform } from "@/hooks/use-scheduled-content";

interface TaskResultProps {
  taskId: string;
  onClose?: () => void;
}

interface TaskOutput {
  content?: string;
  post_text?: string;
  hashtags?: string;
  suggested_time?: string;
  image_prompt?: string;
  image_url?: string;
  total_gross?: number;
  total_net?: number;
  vat?: number;
  total_income?: number;
  total_expenses?: number;
  balance?: number;
}

const statusConfig = {
  pending: { label: "Oczekuje", variant: "secondary" as const, color: "text-yellow-500" },
  processing: { label: "Przetwarzanie", variant: "secondary" as const, color: "text-blue-500" },
  completed: { label: "Gotowe", variant: "default" as const, color: "text-green-500" },
  failed: { label: "Blad", variant: "destructive" as const, color: "text-red-500" },
};

const agentLabels: Record<string, string> = {
  instagram_specialist: "Post Instagram",
  copywriter: "Tekst reklamowy",
  invoice_worker: "Faktura VAT",
  cashflow_analyst: "Analiza Cashflow",
};

const agentIcons: Record<string, typeof Instagram> = {
  instagram_specialist: Instagram,
  copywriter: FileText,
  invoice_worker: FileText,
  cashflow_analyst: FileText,
};

// Map agent to content type for scheduling
const agentToContentType: Record<string, ContentType> = {
  instagram_specialist: "instagram_post",
  copywriter: "ad_copy",
};

// Map agent to platform for scheduling
const agentToPlatform: Record<string, ContentPlatform> = {
  instagram_specialist: "instagram",
  copywriter: "other",
};

export function TaskResult({ taskId, onClose }: TaskResultProps) {
  const { data: task, isLoading, error } = useTask(taskId);
  const retryTask = useRetryTask();
  const { toast } = useToast();

  const [copied, setCopied] = useState<string | null>(null);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  const exportToFile = (content: string, filename: string, type: string = "text/plain") => {
    const blob = new Blob([content], { type: `${type};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleRetry = () => {
    if (task) {
      retryTask.mutate(task.id);
    }
  };

  const handleScheduleSuccess = () => {
    toast({
      title: "Dodano do kolejki",
      description: "Treść została dodana do kolejki publikacji.",
    });
  };

  // Get content type and platform for scheduling based on agent type
  const getContentType = (): ContentType => {
    return agentToContentType[task?.agent || ""] || "other";
  };

  const getPlatform = (): ContentPlatform => {
    return agentToPlatform[task?.agent || ""] || "other";
  };

  // Get content object for scheduling
  const getScheduleContent = () => {
    if (!output) return {};

    if (output.post_text) {
      return {
        text: output.post_text,
        hashtags: output.hashtags ? output.hashtags.split(" ").filter(Boolean) : [],
        image_prompt: output.image_prompt,
        image_url: output.image_url,
      };
    }

    return {
      text: output.content || "",
    };
  };

  if (isLoading) {
    return (
      <Card className="border-2">
        <CardContent className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Ladowanie wynikow...</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !task) {
    return (
      <Card className="border-2 border-destructive/50">
        <CardContent className="flex flex-col items-center justify-center py-12 gap-3 text-destructive">
          <AlertCircle className="h-8 w-8" />
          <p className="font-medium">Nie mozna zaladowac zadania</p>
          <Button variant="outline" size="sm" onClick={onClose}>
            Zamknij
          </Button>
        </CardContent>
      </Card>
    );
  }

  const status = statusConfig[task.status];
  const AgentIcon = agentIcons[task.agent] || FileText;
  const output = task.output as TaskOutput | undefined;

  // Get the main content to copy
  const getMainContent = () => {
    if (!output) return "";
    if (output.post_text) {
      return output.post_text + (output.hashtags ? "\n\n" + output.hashtags : "");
    }
    return output.content || "";
  };

  const getExportFilename = () => {
    const date = new Date().toISOString().split("T")[0];
    const agentName = task.agent.replace("_", "-");
    return `agora-${agentName}-${date}.txt`;
  };

  return (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${task.status === "completed" ? "bg-green-500/10" : "bg-muted"}`}>
              <AgentIcon className={`h-5 w-5 ${status.color}`} />
            </div>
            <div>
              <CardTitle className="text-lg">
                {agentLabels[task.agent] || task.agent}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {task.input?.brief as string || "Zadanie"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={status.variant}>{status.label}</Badge>
            {onClose && (
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Processing state */}
        {(task.status === "processing" || task.status === "pending") && (
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
              <div className="relative flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            </div>
            <div className="text-center">
              <p className="font-medium">
                {task.status === "processing" ? "Agent pracuje..." : "W kolejce..."}
              </p>
              <p className="text-sm text-muted-foreground">
                To moze potrwac kilka sekund
              </p>
            </div>
          </div>
        )}

        {/* Failed state */}
        {task.status === "failed" && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-medium">Wystapil blad</p>
                <p className="text-sm opacity-80">{task.error || "Nieznany blad"}</p>
              </div>
            </div>
            <Button onClick={handleRetry} disabled={retryTask.isPending} className="w-full">
              {retryTask.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Sprobuj ponownie
            </Button>
          </div>
        )}

        {/* Completed state - Social Media Post */}
        {task.status === "completed" && output && (task.agent === "instagram_specialist" || output.post_text) && (
          <div className="space-y-4">
            {/* Success banner */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-700 dark:text-green-400">
              <Check className="h-5 w-5" />
              <span className="font-medium">Post gotowy!</span>
            </div>

            {/* Post preview */}
            <div className="border rounded-lg overflow-hidden">
              {/* Mock Instagram header */}
              <div className="flex items-center gap-3 p-3 border-b bg-muted/30">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500" />
                <span className="font-medium text-sm">twoja_firma</span>
              </div>

              {/* Image placeholder */}
              {output.image_prompt && (
                <div className="aspect-square bg-muted flex flex-col items-center justify-center gap-2 text-muted-foreground">
                  <Image className="h-12 w-12" />
                  <p className="text-xs text-center px-4">
                    {output.image_url ? "Grafika wygenerowana" : "Opis grafiki do wygenerowania"}
                  </p>
                </div>
              )}

              {/* Post text */}
              <div className="p-4 space-y-3">
                <p className="text-sm whitespace-pre-wrap">
                  {output.post_text || output.content}
                </p>
                {output.hashtags && (
                  <p className="text-sm text-primary">
                    {output.hashtags}
                  </p>
                )}
              </div>
            </div>

            {/* Suggested time */}
            {output.suggested_time && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Sugerowany czas: {output.suggested_time}</span>
              </div>
            )}

            {/* Image prompt */}
            {output.image_prompt && (
              <div className="p-3 rounded-lg bg-muted/50 space-y-1">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Image className="h-4 w-4" />
                  Opis grafiki
                </div>
                <p className="text-sm text-muted-foreground">{output.image_prompt}</p>
              </div>
            )}

            {/* Action buttons */}
            <div className="space-y-3">
              <p className="text-sm font-medium">Co dalej?</p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(getMainContent(), "text")}
                  className="gap-2"
                >
                  {copied === "text" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                  {copied === "text" ? "Skopiowano!" : "Kopiuj tekst"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => exportToFile(getMainContent(), getExportFilename())}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Pobierz
                </Button>
              </div>

              {output.hashtags && (
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(output.hashtags || "", "hashtags")}
                  className="w-full gap-2"
                >
                  {copied === "hashtags" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Hash className="h-4 w-4" />
                  )}
                  {copied === "hashtags" ? "Skopiowano!" : "Kopiuj hashtagi"}
                </Button>
              )}

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleRetry}
                  disabled={retryTask.isPending}
                  className="flex-1 gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${retryTask.isPending ? "animate-spin" : ""}`} />
                  Generuj inny
                </Button>
                <Button
                  onClick={() => setScheduleDialogOpen(true)}
                  className="flex-1 gap-2"
                >
                  <CalendarPlus className="h-4 w-4" />
                  Dodaj do kolejki
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Completed state - Copywriting */}
        {task.status === "completed" && output && task.agent === "copywriter" && !output.post_text && (
          <div className="space-y-4">
            {/* Success banner */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-700 dark:text-green-400">
              <Check className="h-5 w-5" />
              <span className="font-medium">Tekst gotowy!</span>
            </div>

            {/* Content preview */}
            <div className="p-4 rounded-lg border bg-muted/30">
              <p className="whitespace-pre-wrap text-sm">{output.content}</p>
            </div>

            {/* Action buttons */}
            <div className="space-y-3">
              <p className="text-sm font-medium">Co dalej?</p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(output.content || "", "text")}
                  className="gap-2"
                >
                  {copied === "text" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                  {copied === "text" ? "Skopiowano!" : "Kopiuj tekst"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => exportToFile(output.content || "", getExportFilename())}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Pobierz
                </Button>
              </div>
              <Button
                variant="outline"
                onClick={handleRetry}
                disabled={retryTask.isPending}
                className="w-full gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${retryTask.isPending ? "animate-spin" : ""}`} />
                Generuj inny wariant
              </Button>
            </div>
          </div>
        )}

        {/* Completed state - Finance (Invoice/Cashflow) */}
        {task.status === "completed" && output && (output.total_gross !== undefined || output.balance !== undefined) && (
          <div className="space-y-4">
            {/* Success banner */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-700 dark:text-green-400">
              <Check className="h-5 w-5" />
              <span className="font-medium">Dokument gotowy!</span>
            </div>

            {/* Invoice summary */}
            {output.total_gross !== undefined && (
              <div className="grid grid-cols-3 gap-4 p-4 rounded-lg border bg-muted/30">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Netto</p>
                  <p className="font-bold">{output.total_net?.toFixed(2)} PLN</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">VAT</p>
                  <p className="font-bold">{output.vat?.toFixed(2)} PLN</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Brutto</p>
                  <p className="font-bold text-primary">{output.total_gross?.toFixed(2)} PLN</p>
                </div>
              </div>
            )}

            {/* Cashflow summary */}
            {output.balance !== undefined && (
              <div className="grid grid-cols-3 gap-4 p-4 rounded-lg border bg-muted/30">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Przychody</p>
                  <p className="font-bold text-green-600">{output.total_income?.toFixed(2)} PLN</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Wydatki</p>
                  <p className="font-bold text-red-600">{output.total_expenses?.toFixed(2)} PLN</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Bilans</p>
                  <p className={`font-bold ${(output.balance ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {output.balance?.toFixed(2)} PLN
                  </p>
                </div>
              </div>
            )}

            {/* Full content */}
            {output.content && (
              <div className="p-4 rounded-lg border bg-muted/30 max-h-64 overflow-y-auto">
                <p className="whitespace-pre-wrap text-sm font-mono">{output.content}</p>
              </div>
            )}

            {/* Action buttons */}
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                onClick={() => copyToClipboard(output.content || "", "text")}
                className="gap-2"
              >
                {copied === "text" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied === "text" ? "Skopiowano!" : "Kopiuj"}
              </Button>
              <Button
                variant="outline"
                onClick={() => exportToFile(output.content || "", getExportFilename())}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Eksportuj
              </Button>
            </div>
          </div>
        )}

        {/* Generic completed state */}
        {task.status === "completed" && output && !output.post_text && !output.total_gross && !output.balance && task.agent !== "copywriter" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-700 dark:text-green-400">
              <Check className="h-5 w-5" />
              <span className="font-medium">Zadanie ukonczone!</span>
            </div>

            <div className="p-4 rounded-lg border bg-muted/30 max-h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm">{output.content}</p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                onClick={() => copyToClipboard(output.content || "", "text")}
                className="gap-2"
              >
                {copied === "text" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied === "text" ? "Skopiowano!" : "Kopiuj"}
              </Button>
              <Button
                variant="outline"
                onClick={() => exportToFile(output.content || "", getExportFilename())}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Pobierz
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      {/* Schedule Dialog */}
      {task && (
        <ScheduleDialog
          open={scheduleDialogOpen}
          onOpenChange={setScheduleDialogOpen}
          content={getScheduleContent()}
          contentType={getContentType()}
          platform={getPlatform()}
          sourceTaskId={task.id}
          onSuccess={handleScheduleSuccess}
        />
      )}
    </Card>
  );
}
