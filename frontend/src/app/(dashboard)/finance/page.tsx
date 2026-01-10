"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  useDepartmentStats,
  agentLabels,
} from "@/hooks/use-department-stats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  CheckCircle,
  Clock,
  Loader2,
  AlertCircle,
  Receipt,
  TrendingUp,
  Calculator,
  MessageSquare,
  ArrowRight,
  BarChart3,
  Wallet,
} from "lucide-react";

const agentIcons: Record<string, typeof FileText> = {
  invoice_specialist: Receipt,
  cashflow_analyst: TrendingUp,
};

const statusConfig: Record<string, { color: string; label: string }> = {
  completed: { color: "text-green-500", label: "Gotowe" },
  pending: { color: "text-yellow-500", label: "Oczekuje" },
  processing: { color: "text-blue-500", label: "W trakcie" },
  failed: { color: "text-red-500", label: "Błąd" },
};

export default function FinancePage() {
  const router = useRouter();
  const { data: stats, isLoading, error } = useDepartmentStats("finance");

  const handleQuickAction = (action: string) => {
    router.push(`/chat?action=${action}`);
  };

  const handleViewTask = (taskId: string) => {
    router.push(`/tasks?id=${taskId}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>Nie można załadować danych</span>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "przed chwilą";
    if (diffMins < 60) return `${diffMins} min temu`;
    if (diffHours < 24) return `${diffHours}h temu`;
    if (diffDays === 1) return "wczoraj";
    return `${diffDays} dni temu`;
  };

  const maxTrend = Math.max(...stats.weekly_trend.map((d) => d.count), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Wallet className="h-8 w-8 text-primary" />
            Finanse
          </h1>
          <p className="text-muted-foreground mt-1">
            Przegląd operacji finansowych
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Wszystkie</p>
                <p className="text-3xl font-bold">{stats.summary.total_tasks}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-muted-foreground/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Ten tydzień</p>
                <p className="text-3xl font-bold">{stats.summary.tasks_this_week}</p>
              </div>
              <FileText className="h-8 w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Ukończone</p>
                <p className="text-3xl font-bold text-green-500">{stats.summary.completed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">W kolejce</p>
                <p className="text-3xl font-bold text-yellow-500">{stats.summary.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Weekly Trend + Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Weekly Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Aktywność tygodniowa</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-2 h-32">
                {stats.weekly_trend.map((day, idx) => {
                  const height = (day.count / maxTrend) * 100;
                  const dayName = new Date(day.date).toLocaleDateString("pl-PL", {
                    timeZone: "Europe/Warsaw",
                    weekday: "short",
                  });
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full bg-muted rounded-t relative" style={{ height: "100px" }}>
                        <div
                          className="absolute bottom-0 w-full bg-primary rounded-t transition-all"
                          style={{ height: `${height}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{dayName}</span>
                      <span className="text-xs font-medium">{day.count}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Szybkie akcje</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                <Button
                  variant="outline"
                  className="h-auto py-4 justify-start gap-3"
                  onClick={() => handleQuickAction("invoice")}
                >
                  <div className="p-2 rounded-lg bg-green-500/10">
                    <Receipt className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Nowa faktura</p>
                    <p className="text-xs text-muted-foreground">Wygeneruj fakturę VAT</p>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto py-4 justify-start gap-3"
                  onClick={() => handleQuickAction("cashflow")}
                >
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <TrendingUp className="h-5 w-5 text-blue-500" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Analiza cashflow</p>
                    <p className="text-xs text-muted-foreground">Sprawdź przepływy</p>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto py-4 justify-start gap-3"
                  onClick={() => handleQuickAction("budget")}
                >
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Calculator className="h-5 w-5 text-purple-500" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Planowanie budżetu</p>
                    <p className="text-xs text-muted-foreground">Zaplanuj wydatki</p>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto py-4 justify-start gap-3"
                  onClick={() => router.push("/chat")}
                >
                  <div className="p-2 rounded-lg bg-primary/10">
                    <MessageSquare className="h-5 w-5 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Zapytaj asystenta</p>
                    <p className="text-xs text-muted-foreground">Opisz czego potrzebujesz</p>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Recent Tasks + Agents */}
        <div className="space-y-6">
          {/* Agent Stats */}
          {stats.tasks_by_agent.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Użycie agentów</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.tasks_by_agent.map((agent) => {
                    const Icon = agentIcons[agent.agent] || FileText;
                    const label = agentLabels[agent.agent] || agent.agent;
                    const percentage = Math.round((agent.count / stats.summary.total_tasks) * 100);
                    return (
                      <div key={agent.agent} className="flex items-center gap-3">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <div className="flex items-center justify-between text-sm">
                            <span>{label}</span>
                            <span className="text-muted-foreground">{agent.count}</span>
                          </div>
                          <div className="h-1.5 bg-muted rounded-full mt-1">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Tasks */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Ostatnie dokumenty</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/tasks?department=finance")}
              >
                Wszystkie
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </CardHeader>
            <CardContent>
              {stats.recent_tasks.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Brak zadań
                </p>
              ) : (
                <div className="space-y-3">
                  {stats.recent_tasks.slice(0, 5).map((task) => {
                    const status = statusConfig[task.status] || statusConfig.pending;
                    return (
                      <button
                        key={task.id}
                        onClick={() => handleViewTask(task.id)}
                        className="w-full text-left p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-sm font-medium truncate">
                              {task.title || task.type}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {agentLabels[task.agent] || task.agent} • {formatDate(task.created_at)}
                            </p>
                          </div>
                          <Badge
                            variant={task.status === "completed" ? "default" : "secondary"}
                            className="shrink-0"
                          >
                            {status.label}
                          </Badge>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
