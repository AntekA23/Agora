"use client";

import { useState } from "react";
import Link from "next/link";
import { TaskList } from "@/components/agents/task-list";
import { TaskResult } from "@/components/agents/task-result";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function TasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Zadania</h1>
          <p className="text-muted-foreground mt-1">
            Przegladaj wszystkie zadania agentow AI
          </p>
        </div>
        <Link href="/marketing">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nowe zadanie
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <TaskList onSelectTask={setSelectedTaskId} />

        {selectedTaskId && (
          <TaskResult
            taskId={selectedTaskId}
            onClose={() => setSelectedTaskId(null)}
          />
        )}
      </div>
    </div>
  );
}
