"use client";

import { useState } from "react";
import { useCreateCopywriterTask } from "@/hooks/use-tasks";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, PenTool } from "lucide-react";

interface CopywriterFormProps {
  onTaskCreated?: (taskId: string) => void;
}

export function CopywriterForm({ onTaskCreated }: CopywriterFormProps) {
  const [brief, setBrief] = useState("");
  const [copyType, setCopyType] = useState<"ad" | "email" | "landing" | "slogan" | "description">("ad");
  const [maxLength, setMaxLength] = useState<string>("");

  const { mutate, isPending, error } = useCreateCopywriterTask();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (brief.length < 10) return;

    mutate(
      {
        brief,
        copy_type: copyType,
        max_length: maxLength ? parseInt(maxLength) : undefined,
      },
      {
        onSuccess: (task) => {
          setBrief("");
          onTaskCreated?.(task.id);
        },
      }
    );
  };

  const copyTypeLabels = {
    ad: "Tekst reklamowy",
    email: "Email marketingowy",
    landing: "Landing page",
    slogan: "Slogan / haslo",
    description: "Opis produktu",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PenTool className="h-5 w-5" />
          Copywriter
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
              {error instanceof Error ? error.message : "Wystapil blad"}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="copyBrief">Brief</Label>
            <Textarea
              id="copyBrief"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="Opisz co ma zawierac tekst, np. 'Reklama nowego kursu online o inwestowaniu dla poczatkujacych, podkreslic prostote i szybkie rezultaty'"
              rows={4}
              required
              minLength={10}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="copyType">Typ tekstu</Label>
              <Select value={copyType} onValueChange={(v) => setCopyType(v as typeof copyType)}>
                <SelectTrigger>
                  <SelectValue placeholder="Wybierz typ" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(copyTypeLabels).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxLength">Max. dlugosc (opcjonalnie)</Label>
              <Input
                id="maxLength"
                type="number"
                value={maxLength}
                onChange={(e) => setMaxLength(e.target.value)}
                placeholder="np. 500"
                min={50}
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isPending || brief.length < 10}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generowanie...
              </>
            ) : (
              "Wygeneruj tekst"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
