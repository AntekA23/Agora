"use client";

import { useAuth } from "@/hooks/use-auth";
import { useDashboardAnalytics } from "@/hooks/use-analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  MessageSquare,
  TrendingUp,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
  BarChart3,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const agentLabels: Record<string, string> = {
  instagram_specialist: "Instagram",
  copywriter: "Copywriter",
  invoice_worker: "Faktury",
  cashflow_analyst: "Cashflow",
};

const departmentLabels: Record<string, string> = {
  marketing: "Marketing",
  finance: "Finanse",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: analytics, isLoading } = useDashboardAnalytics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const stats = [
    {
      name: "Zadania dzisiaj",
      value: analytics?.summary.tasks_today || 0,
      icon: MessageSquare,
      color: "text-blue-500",
    },
    {
      name: "Ten tydzien",
      value: analytics?.summary.tasks_week || 0,
      icon: TrendingUp,
      color: "text-green-500",
    },
    {
      name: "Wszystkie",
      value: analytics?.summary.total_tasks || 0,
      icon: FileText,
      color: "text-purple-500",
    },
    {
      name: "Skutecznosc",
      value: `${analytics?.summary.completion_rate || 0}%`,
      icon: CheckCircle,
      color: "text-emerald-500",
    },
  ];

  const statusIcons: Record<string, typeof Clock> = {
    pending: Clock,
    processing: Loader2,
    completed: CheckCircle,
    failed: AlertCircle,
  };

  const statusColors: Record<string, string> = {
    pending: "text-yellow-500",
    processing: "text-blue-500",
    completed: "text-green-500",
    failed: "text-red-500",
  };

  const maxActivity = Math.max(
    ...(analytics?.daily_activity?.map((d) => d.count) || [1])
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Witaj, {user?.name?.split(" ")[0] || "User"}
          </h1>
          <p className="text-muted-foreground mt-1">
            Oto podsumowanie aktywnosci Twoich agentow AI
          </p>
        </div>
        <Link href="/marketing">
          <Button>
            <MessageSquare className="h-4 w-4 mr-2" />
            Nowe zadanie
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.name}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Activity Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Aktywnosc (7 dni)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between h-32 gap-2">
              {analytics?.daily_activity?.map((day) => {
                const height = maxActivity > 0 ? (day.count / maxActivity) * 100 : 0;
                const date = new Date(day.date);
                const dayName = date.toLocaleDateString("pl-PL", { weekday: "short" });
                return (
                  <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className="w-full bg-primary rounded-t transition-all"
                      style={{ height: `${Math.max(height, 4)}%` }}
                      title={`${day.count} zadan`}
                    />
                    <span className="text-xs text-muted-foreground">{dayName}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Status zadan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(analytics?.tasks_by_status || {}).map(([status, count]) => {
                const Icon = statusIcons[status] || MessageSquare;
                const color = statusColors[status] || "text-muted-foreground";
                const labels: Record<string, string> = {
                  pending: "Oczekujace",
                  processing: "W trakcie",
                  completed: "Ukonczone",
                  failed: "Nieudane",
                };
                return (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${color}`} />
                      <span className="text-sm">{labels[status] || status}</span>
                    </div>
                    <Badge variant="secondary">{count}</Badge>
                  </div>
                );
              })}
              {Object.keys(analytics?.tasks_by_status || {}).length === 0 && (
                <p className="text-sm text-muted-foreground">Brak zadan</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* By Department */}
        <Card>
          <CardHeader>
            <CardTitle>Dzialy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(analytics?.tasks_by_department || {}).map(([dept, count]) => (
                <div key={dept} className="flex items-center justify-between">
                  <span className="text-sm">{departmentLabels[dept] || dept}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
              {Object.keys(analytics?.tasks_by_department || {}).length === 0 && (
                <p className="text-sm text-muted-foreground">Brak danych</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* By Agent */}
        <Card>
          <CardHeader>
            <CardTitle>Agenci</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(analytics?.tasks_by_agent || {}).map(([agent, count]) => (
                <div key={agent} className="flex items-center justify-between">
                  <span className="text-sm">{agentLabels[agent] || agent}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
              {Object.keys(analytics?.tasks_by_agent || {}).length === 0 && (
                <p className="text-sm text-muted-foreground">Brak danych</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
