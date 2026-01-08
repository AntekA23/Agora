"use client";

import * as React from "react";
import {
  Bot,
  Plus,
  Play,
  Pause,
  Trash2,
  MoreHorizontal,
  Clock,
  Calendar,
  Sparkles,
  AlertCircle,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { pl } from "date-fns/locale";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  useScheduleRules,
  useScheduleRuleStats,
  useToggleScheduleRule,
  useDeleteScheduleRule,
  useGenerateNow,
  type ScheduleRule,
  frequencyLabels,
  categoryLabels,
  dayLabels,
} from "@/hooks/use-schedule-rules";
import { platformLabels } from "@/hooks/use-scheduled-content";
import { RuleWizard } from "@/components/automation/rule-wizard";

export default function AutomationPage() {
  const { toast } = useToast();

  const { data, isLoading, error } = useScheduleRules();
  const { data: stats } = useScheduleRuleStats();

  const toggleMutation = useToggleScheduleRule();
  const deleteMutation = useDeleteScheduleRule();
  const generateNowMutation = useGenerateNow();

  const [wizardOpen, setWizardOpen] = React.useState(false);
  const [deleteRule, setDeleteRule] = React.useState<ScheduleRule | null>(null);

  const handleToggle = async (rule: ScheduleRule) => {
    try {
      await toggleMutation.mutateAsync(rule.id);
      toast({
        title: rule.is_active ? "Wstrzymano" : "Wznowiono",
        description: rule.is_active
          ? `Reguła "${rule.name}" została wstrzymana.`
          : `Reguła "${rule.name}" została wznowiona.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się zmienić statusu reguły.",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async () => {
    if (!deleteRule) return;

    try {
      await deleteMutation.mutateAsync(deleteRule.id);
      toast({
        title: "Usunięto",
        description: `Reguła "${deleteRule.name}" została usunięta.`,
      });
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się usunąć reguły.",
        variant: "destructive",
      });
    } finally {
      setDeleteRule(null);
    }
  };

  const handleGenerateNow = async (rule: ScheduleRule) => {
    try {
      const result = await generateNowMutation.mutateAsync({ id: rule.id });
      if (result.success) {
        toast({
          title: "Wygenerowano",
          description: "Nowa treść została dodana do kolejki.",
        });
      } else {
        toast({
          title: "Błąd",
          description: result.error || "Nie udało się wygenerować treści.",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Błąd",
        description: "Nie udało się wygenerować treści.",
        variant: "destructive",
      });
    }
  };

  const formatSchedule = (rule: ScheduleRule) => {
    const { schedule } = rule;
    const time = schedule.time;

    if (schedule.frequency === "daily") {
      return `Codziennie o ${time}`;
    } else if (schedule.frequency === "weekly") {
      const days = schedule.days_of_week.map((d) => dayLabels[d]).join(", ");
      return `${days} o ${time}`;
    } else {
      return `${schedule.day_of_month}. dnia miesiąca o ${time}`;
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>Nie można załadować automatyzacji</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bot className="h-8 w-8 text-primary" />
            Automatyzacje
          </h1>
          <p className="text-muted-foreground mt-1">
            Automatyczne generowanie i publikowanie treści
          </p>
        </div>
        <Button onClick={() => setWizardOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nowa reguła
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Wszystkie reguły</p>
                <p className="text-3xl font-bold">{stats?.total_rules || 0}</p>
              </div>
              <Bot className="h-8 w-8 text-muted-foreground/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Aktywne</p>
                <p className="text-3xl font-bold text-green-500">
                  {stats?.active_rules || 0}
                </p>
              </div>
              <Play className="h-8 w-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Wygenerowano</p>
                <p className="text-3xl font-bold">{stats?.total_generated || 0}</p>
              </div>
              <Sparkles className="h-8 w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Opublikowano</p>
                <p className="text-3xl font-bold text-blue-500">
                  {stats?.total_published || 0}
                </p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rules List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Reguły automatyzacji</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : data?.items.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-1">Brak reguł</h3>
              <p className="text-muted-foreground mb-4">
                Stwórz pierwszą regułę automatyzacji, aby system generował treści
                automatycznie.
              </p>
              <Button onClick={() => setWizardOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Stwórz pierwszą regułę
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {data?.items.map((rule) => (
                <div
                  key={rule.id}
                  className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      {/* Status indicator */}
                      <div
                        className={`w-3 h-3 rounded-full mt-1.5 ${
                          rule.is_active ? "bg-green-500" : "bg-muted-foreground"
                        }`}
                      />

                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{rule.name}</h3>
                          <Badge variant="outline">
                            {platformLabels[rule.platform]}
                          </Badge>
                          {!rule.is_active && (
                            <Badge variant="secondary">Wstrzymana</Badge>
                          )}
                        </div>

                        <p className="text-sm text-muted-foreground mt-1">
                          {categoryLabels[rule.content_template.category]} •{" "}
                          {formatSchedule(rule)}
                        </p>

                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {rule.next_execution ? (
                              <>
                                Następna:{" "}
                                {formatDistanceToNow(new Date(rule.next_execution), {
                                  addSuffix: true,
                                  locale: pl,
                                })}
                              </>
                            ) : (
                              "Brak zaplanowanej"
                            )}
                          </span>
                          <span>
                            W kolejce: {rule.queue_count}/{rule.max_queue_size}
                          </span>
                          <span>Wygenerowano: {rule.total_generated}</span>
                        </div>

                        {rule.last_error && (
                          <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {rule.last_error}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggle(rule)}
                        disabled={toggleMutation.isPending}
                      >
                        {rule.is_active ? (
                          <>
                            <Pause className="h-4 w-4 mr-1" />
                            Wstrzymaj
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-1" />
                            Wznów
                          </>
                        )}
                      </Button>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleGenerateNow(rule)}
                            disabled={generateNowMutation.isPending}
                          >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Generuj teraz
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => setDeleteRule(rule)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Usuń
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rule Wizard */}
      <RuleWizard open={wizardOpen} onOpenChange={setWizardOpen} />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteRule} onOpenChange={() => setDeleteRule(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Usuń regułę</AlertDialogTitle>
            <AlertDialogDescription>
              Czy na pewno chcesz usunąć regułę &quot;{deleteRule?.name}&quot;?
              Ta akcja jest nieodwracalna. Treści już wygenerowane przez tę
              regułę pozostaną w kolejce.
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
    </div>
  );
}
