"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useTasks, useCreateInstagramTask, useCreateCopywriterTask } from "@/hooks/use-tasks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CommandInput } from "@/components/command-input";
import { QuickActions } from "@/components/quick-actions";
import { FollowUpDialog } from "@/components/follow-up-dialog";
import { TemplatePicker, TemplateForm } from "@/components/templates";
import { SmartNotifications, ContentCalendar } from "@/components/suggestions";
import { BrandReminderBanner } from "@/components/brand-reminder-banner";
import {
  CheckCircle,
  Clock,
  Loader2,
  AlertCircle,
  Sparkles,
  LayoutTemplate,
} from "lucide-react";
import type { InterpretResponse, QuickAction } from "@/types/assistant";
import type { Task } from "@/types/task";
import type { Template, TemplateCategory } from "@/hooks/use-templates";

const agentLabels: Record<string, string> = {
  instagram_specialist: "Instagram",
  copywriter: "Copywriter",
  invoice_specialist: "Faktury",
  cashflow_analyst: "Cashflow",
  hr_recruiter: "Rekrutacja",
  campaign_service: "Kampania",
};

const statusConfig: Record<
  string,
  { icon: typeof Clock; color: string; label: string }
> = {
  pending: { icon: Clock, color: "text-yellow-500", label: "Oczekuje" },
  processing: { icon: Loader2, color: "text-blue-500", label: "W trakcie" },
  completed: { icon: CheckCircle, color: "text-green-500", label: "Gotowe" },
  failed: { icon: AlertCircle, color: "text-red-500", label: "Blad" },
};

export default function CommandCenterPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { data: tasksData, isLoading: tasksLoading } = useTasks({
    per_page: 5,
  });
  const createInstagramTask = useCreateInstagramTask();
  const createCopywriterTask = useCreateCopywriterTask();

  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [currentResult, setCurrentResult] =
    React.useState<InterpretResponse | null>(null);
  const [originalMessage, setOriginalMessage] = React.useState("");

  // Template states
  const [templatePickerOpen, setTemplatePickerOpen] = React.useState(false);
  const [templateFormOpen, setTemplateFormOpen] = React.useState(false);
  const [selectedCategory, setSelectedCategory] = React.useState<TemplateCategory | null>(null);
  const [selectedTemplate, setSelectedTemplate] = React.useState<Template | null>(null);
  const [isSubmittingTemplate, setIsSubmittingTemplate] = React.useState(false);

  const handleInterpretResult = React.useCallback(
    (result: InterpretResponse, message: string) => {
      setCurrentResult(result);
      setOriginalMessage(message);

      if (result.can_auto_execute) {
        redirectToAgent(result);
      } else if (result.follow_up_questions.length > 0) {
        setDialogOpen(true);
      }
    },
    []
  );

  const handleQuickAction = React.useCallback(
    (result: InterpretResponse, action: QuickAction) => {
      setCurrentResult(result);
      setOriginalMessage(action.label);

      if (result.can_auto_execute) {
        redirectToAgent(result);
      } else if (result.follow_up_questions.length > 0) {
        setDialogOpen(true);
      }
    },
    []
  );

  const handleFollowUpSubmit = React.useCallback(
    (answers: Record<string, string>) => {
      if (!currentResult) return;

      const params = { ...currentResult.extracted_params, ...answers };
      redirectToAgentWithParams(currentResult.intent, params);
      setDialogOpen(false);
    },
    [currentResult]
  );

  // Template handlers
  const handleSelectTemplate = (category: TemplateCategory, template: Template) => {
    setSelectedCategory(category);
    setSelectedTemplate(template);
    setTemplatePickerOpen(false);
    setTemplateFormOpen(true);
  };

  const handleTemplateSubmit = async (params: Record<string, unknown>, prompt: string) => {
    if (!selectedCategory || !selectedTemplate) return;

    setIsSubmittingTemplate(true);

    try {
      // Determine which agent to use based on category
      if (selectedCategory.id === "social_media") {
        await createInstagramTask.mutateAsync({
          brief: prompt,
          post_type: "post",
          include_hashtags: true,
        });
      } else if (selectedCategory.id === "copywriting") {
        await createCopywriterTask.mutateAsync({
          brief: prompt,
          copy_type: "ad",
        });
      }

      // Close form and redirect to tasks
      setTemplateFormOpen(false);
      router.push("/tasks");
    } catch (error) {
      console.error("Error creating task from template:", error);
    } finally {
      setIsSubmittingTemplate(false);
    }
  };

  const redirectToAgent = (result: InterpretResponse) => {
    const intentRoutes: Record<string, string> = {
      social_media_post: "/marketing",
      marketing_copy: "/marketing",
      campaign: "/campaigns",
      invoice: "/finance",
      cashflow_analysis: "/finance",
      job_posting: "/hr",
      interview_questions: "/hr",
      onboarding: "/hr",
      sales_proposal: "/sales",
      lead_scoring: "/sales",
      followup_email: "/sales",
      contract_review: "/legal",
      privacy_policy: "/legal",
      terms_of_service: "/legal",
      gdpr_check: "/legal",
      ticket_response: "/support",
      faq: "/support",
      sentiment_analysis: "/support",
    };

    const route = intentRoutes[result.intent] || "/marketing";
    const params = new URLSearchParams();

    if (result.extracted_params.topic) {
      params.set("brief", String(result.extracted_params.topic));
    }
    if (result.quick_action_id) {
      params.set("action", result.quick_action_id);
    }

    const queryString = params.toString();
    router.push(route + (queryString ? "?" + queryString : ""));
  };

  const redirectToAgentWithParams = (
    intent: string,
    params: Record<string, unknown>
  ) => {
    const intentRoutes: Record<string, string> = {
      social_media_post: "/marketing",
      marketing_copy: "/marketing",
      campaign: "/campaigns",
      invoice: "/finance",
      cashflow_analysis: "/finance",
      job_posting: "/hr",
      sales_proposal: "/sales",
      contract_review: "/legal",
      ticket_response: "/support",
    };

    const route = intentRoutes[intent] || "/marketing";
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.set(key, String(value));
      }
    });

    const queryString = searchParams.toString();
    router.push(route + (queryString ? "?" + queryString : ""));
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "przed chwila";
    if (diffMins < 60) return diffMins + " min temu";
    if (diffHours < 24) return diffHours + "h temu";
    if (diffDays === 1) return "wczoraj";
    return diffDays + " dni temu";
  };

  const recentTasks = tasksData?.tasks ?? [];
  const firstName = user?.name?.split(" ")[0] || "User";

  return (
    <div className="space-y-8">
      <BrandReminderBanner />

      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Witaj, {firstName}</h1>
        <p className="text-muted-foreground">Co chcesz dzis zrobic?</p>
      </div>

      <div className="max-w-2xl mx-auto">
        <Card className="border-2">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="font-medium">Opisz czego potrzebujesz</span>
            </div>
            <CommandInput
              onInterpret={handleInterpretResult}
              placeholder='np. "Post na Instagram o nowej promocji -20%"'
            />
          </CardContent>
        </Card>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          <span>lub wybierz szybka akcje</span>
          <div className="h-px flex-1 bg-border" />
        </div>
        <div className="flex justify-center">
          <QuickActions onSelect={handleQuickAction} />
        </div>
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => setTemplatePickerOpen(true)}
            className="gap-2"
          >
            <LayoutTemplate className="h-4 w-4" />
            Wszystkie szablony
          </Button>
        </div>
      </div>

      {/* Suggestions and Calendar Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <SmartNotifications maxItems={4} showTrends={true} />
        <ContentCalendar daysAhead={30} />
      </div>

      {recentTasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Ostatnie zadania</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {tasksLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : (
                recentTasks.map((task: Task) => {
                  const config =
                    statusConfig[task.status] || statusConfig.pending;
                  const StatusIcon = config.icon;
                  const agentLabel = agentLabels[task.agent] || task.agent;

                  const title =
                    (task.input?.brief as string) ||
                    (task.input?.description as string) ||
                    task.type;

                  return (
                    <div
                      key={task.id}
                      className="flex items-center justify-between py-2 border-b border-border last:border-0"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <StatusIcon
                          className={
                            "h-4 w-4 shrink-0 " +
                            config.color +
                            (task.status === "processing" ? " animate-spin" : "")
                          }
                        />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{title}</p>
                          <p className="text-xs text-muted-foreground">
                            {agentLabel} • {formatRelativeTime(task.created_at)}
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant={
                          task.status === "completed"
                            ? "default"
                            : task.status === "failed"
                            ? "destructive"
                            : "secondary"
                        }
                        className="shrink-0"
                      >
                        {config.label}
                      </Badge>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <FollowUpDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        result={currentResult}
        originalMessage={originalMessage}
        onSubmit={handleFollowUpSubmit}
      />

      <TemplatePicker
        open={templatePickerOpen}
        onOpenChange={setTemplatePickerOpen}
        onSelectTemplate={handleSelectTemplate}
      />

      <TemplateForm
        open={templateFormOpen}
        onOpenChange={setTemplateFormOpen}
        category={selectedCategory}
        template={selectedTemplate}
        onSubmit={handleTemplateSubmit}
        isSubmitting={isSubmittingTemplate}
      />
    </div>
  );
}
