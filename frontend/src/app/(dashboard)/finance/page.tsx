"use client";

import { useState } from "react";
import { InvoiceForm } from "@/components/agents/invoice-form";
import { TaskResult } from "@/components/agents/task-result";
import { TaskList } from "@/components/agents/task-list";

export default function FinancePage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Finanse</h1>
        <p className="text-muted-foreground mt-1">
          Generuj faktury i analizuj przeplywy z pomoca AI
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <InvoiceForm onTaskCreated={setSelectedTaskId} />
        </div>

        <div className="space-y-6">
          {selectedTaskId && (
            <TaskResult
              taskId={selectedTaskId}
              onClose={() => setSelectedTaskId(null)}
            />
          )}
          <TaskList
            department="finance"
            onSelectTask={setSelectedTaskId}
          />
        </div>
      </div>
    </div>
  );
}
