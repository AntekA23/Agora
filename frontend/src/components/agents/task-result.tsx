"use client";

import { useTask } from "@/hooks/use-tasks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Copy, Check, AlertCircle, Download, FileText } from "lucide-react";
import { useState } from "react";

interface TaskResultProps {
  taskId: string;
  onClose?: () => void;
}

const statusConfig = {
  pending: { label: "Oczekuje", variant: "secondary" as const },
  processing: { label: "Przetwarzanie", variant: "info" as const },
  completed: { label: "Ukonczone", variant: "success" as const },
  failed: { label: "Blad", variant: "destructive" as const },
};

export function TaskResult({ taskId, onClose }: TaskResultProps) {
  const { data: task, isLoading, error } = useTask(taskId);
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportToFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !task) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8 text-destructive">
          <AlertCircle className="h-5 w-5 mr-2" />
          Nie mozna zaladowac zadania
        </CardContent>
      </Card>
    );
  }

  const status = statusConfig[task.status];
  const agentLabels: Record<string, string> = {
    instagram_specialist: "Instagram Post",
    copywriter: "Copywriting",
    invoice_worker: "Faktura VAT",
    cashflow_analyst: "Analiza Cashflow",
  };

  const getExportFilename = () => {
    const date = new Date().toISOString().split("T")[0];
    const agentName = task.agent.replace("_", "-");
    return `agora-${agentName}-${date}.txt`;
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="space-y-1">
          <CardTitle className="text-lg">Wynik zadania</CardTitle>
          <p className="text-sm text-muted-foreground">
            {agentLabels[task.agent] || task.agent}
          </p>
        </div>
        <Badge variant={status.variant}>{status.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {task.status === "processing" && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Agent pracuje nad Twoim zadaniem...</span>
          </div>
        )}

        {task.status === "pending" && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Zadanie w kolejce...</span>
          </div>
        )}

        {task.status === "failed" && task.error && (
          <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
            {task.error}
          </div>
        )}

        {task.status === "completed" && task.output && (
          <div className="space-y-4">
            {/* Export buttons */}
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(String(task.output?.content || ""))}
              >
                {copied ? (
                  <Check className="h-4 w-4 mr-1" />
                ) : (
                  <Copy className="h-4 w-4 mr-1" />
                )}
                {copied ? "Skopiowano" : "Kopiuj"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => exportToFile(String(task.output?.content || ""), getExportFilename())}
              >
                <Download className="h-4 w-4 mr-1" />
                Eksportuj
              </Button>
            </div>

            {/* Main content */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Wygenerowany content</Label>
              <div className="p-4 bg-muted rounded-lg whitespace-pre-wrap text-sm max-h-96 overflow-y-auto">
                {String(task.output.content || "")}
              </div>
            </div>

            {/* Extracted fields for Instagram */}
            {task.output.post_text && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Tekst postu</Label>
                <div className="p-3 bg-muted/50 rounded-lg text-sm">
                  {String(task.output.post_text)}
                </div>
              </div>
            )}

            {task.output.hashtags && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Hashtagi</Label>
                <div className="p-3 bg-muted/50 rounded-lg text-sm">
                  {String(task.output.hashtags)}
                </div>
              </div>
            )}

            {task.output.suggested_time && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Sugerowany czas publikacji</Label>
                <div className="p-3 bg-muted/50 rounded-lg text-sm">
                  {String(task.output.suggested_time)}
                </div>
              </div>
            )}

            {task.output.image_prompt && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Opis grafiki</Label>
                <div className="p-3 bg-muted/50 rounded-lg text-sm">
                  {String(task.output.image_prompt)}
                </div>
              </div>
            )}

            {/* Finance specific fields */}
            {task.output.total_gross !== undefined && (
              <div className="grid grid-cols-3 gap-4 p-3 bg-muted/50 rounded-lg">
                <div>
                  <Label className="text-xs text-muted-foreground">Netto</Label>
                  <p className="font-medium">{task.output.total_net?.toFixed(2)} PLN</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">VAT (23%)</Label>
                  <p className="font-medium">{task.output.vat?.toFixed(2)} PLN</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Brutto</Label>
                  <p className="font-medium">{task.output.total_gross?.toFixed(2)} PLN</p>
                </div>
              </div>
            )}

            {task.output.balance !== undefined && (
              <div className="grid grid-cols-3 gap-4 p-3 bg-muted/50 rounded-lg">
                <div>
                  <Label className="text-xs text-muted-foreground">Przychody</Label>
                  <p className="font-medium text-green-600">{task.output.total_income?.toFixed(2)} PLN</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Wydatki</Label>
                  <p className="font-medium text-red-600">{task.output.total_expenses?.toFixed(2)} PLN</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Bilans</Label>
                  <p className={`font-medium ${task.output.balance >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {task.output.balance?.toFixed(2)} PLN
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {onClose && (
          <Button variant="outline" onClick={onClose} className="w-full">
            Zamknij
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={className}>{children}</p>;
}
