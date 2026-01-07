"use client";

import { useState } from "react";
import { InstagramForm } from "@/components/agents/instagram-form";
import { CopywriterForm } from "@/components/agents/copywriter-form";
import { TaskResult } from "@/components/agents/task-result";
import { TaskList } from "@/components/agents/task-list";
import { Button } from "@/components/ui/button";
import { Instagram, PenTool } from "lucide-react";

type ActiveForm = "instagram" | "copywriter";

export default function MarketingPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [activeForm, setActiveForm] = useState<ActiveForm>("instagram");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Marketing</h1>
        <p className="text-muted-foreground mt-1">
          Tworz content marketingowy z pomoca agentow AI
        </p>
      </div>

      {/* Form selector */}
      <div className="flex gap-2">
        <Button
          variant={activeForm === "instagram" ? "default" : "outline"}
          onClick={() => setActiveForm("instagram")}
        >
          <Instagram className="h-4 w-4 mr-2" />
          Instagram
        </Button>
        <Button
          variant={activeForm === "copywriter" ? "default" : "outline"}
          onClick={() => setActiveForm("copywriter")}
        >
          <PenTool className="h-4 w-4 mr-2" />
          Copywriter
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left column - Forms */}
        <div className="space-y-6">
          {activeForm === "instagram" ? (
            <InstagramForm onTaskCreated={setSelectedTaskId} />
          ) : (
            <CopywriterForm onTaskCreated={setSelectedTaskId} />
          )}
        </div>

        {/* Right column - Result & History */}
        <div className="space-y-6">
          {selectedTaskId && (
            <TaskResult
              taskId={selectedTaskId}
              onClose={() => setSelectedTaskId(null)}
            />
          )}
          <TaskList
            department="marketing"
            onSelectTask={setSelectedTaskId}
          />
        </div>
      </div>
    </div>
  );
}
