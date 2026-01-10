"use client";

import { useTask } from "@/hooks/use-tasks";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Check, ExternalLink, RefreshCw } from "lucide-react";
import { useState } from "react";

interface ChatTaskResultProps {
  taskId: string;
}

export function ChatTaskResult({ taskId }: ChatTaskResultProps) {
  const { data: task } = useTask(taskId);
  const [copied, setCopied] = useState(false);

  // Only show result when task is completed
  if (!task || task.status !== "completed" || !task.output) {
    return null;
  }

  const output = task.output as {
    post_text?: string;
    content?: string;
    hashtags?: string;
    image_url?: string;
    suggested_time?: string;
  };

  const text = output.post_text || output.content || "";
  const hashtags = output.hashtags || "";
  const imageUrl = output.image_url;

  const handleCopy = async () => {
    const fullText = hashtags ? `${text}\n\n${hashtags}` : text;
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="mt-3 border-green-200 dark:border-green-900 bg-green-50/50 dark:bg-green-950/20">
      <CardContent className="p-4 space-y-3">
        {/* Image preview */}
        {imageUrl && (
          <div className="rounded-lg overflow-hidden">
            <img
              src={imageUrl}
              alt="Wygenerowana grafika"
              className="w-full max-w-sm rounded-lg"
            />
          </div>
        )}

        {/* Text preview */}
        {text && (
          <div className="space-y-2">
            <p className="text-sm whitespace-pre-wrap line-clamp-6">{text}</p>
            {hashtags && (
              <p className="text-sm text-blue-600 dark:text-blue-400">
                {hashtags}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="h-8"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 mr-1" />
                Skopiowano
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Kopiuj tekst
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            onClick={() => window.open(`/tasks?selected=${taskId}`, "_blank")}
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            Pelny widok
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
