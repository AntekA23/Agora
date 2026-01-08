"use client";

import { useState } from "react";
import { useCreateInstagramTask } from "@/hooks/use-tasks";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Instagram } from "lucide-react";

interface InstagramFormProps {
  onTaskCreated?: (taskId: string) => void;
}

export function InstagramForm({ onTaskCreated }: InstagramFormProps) {
  const [brief, setBrief] = useState("");
  const [postType, setPostType] = useState<"post" | "story" | "reel" | "carousel">("post");
  const [includeHashtags, setIncludeHashtags] = useState(true);

  const { mutate, isPending, error } = useCreateInstagramTask();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (brief.length < 10) return;

    mutate(
      { brief, post_type: postType, include_hashtags: includeHashtags },
      {
        onSuccess: (task) => {
          setBrief("");
          onTaskCreated?.(task.id);
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Instagram className="h-5 w-5" />
          Instagram Post
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
            <Label htmlFor="brief">Brief</Label>
            <Textarea
              id="brief"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="Opisz co ma zawierac post, np. 'Post o nowej kolekcji wiosennej, podkresl naturalne materialy i pastelowe kolory'"
              rows={4}
              required
              minLength={10}
            />
            <p className="text-xs text-muted-foreground">
              Minimum 10 znakow. Im bardziej szczegolowy brief, tym lepszy wynik.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="postType">Typ postu</Label>
              <Select value={postType} onValueChange={(v) => setPostType(v as typeof postType)}>
                <SelectTrigger>
                  <SelectValue placeholder="Wybierz typ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="post">Post na feed</SelectItem>
                  <SelectItem value="story">Story</SelectItem>
                  <SelectItem value="reel">Reels</SelectItem>
                  <SelectItem value="carousel">Karuzela</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="hashtags">Hashtagi</Label>
              <Select value={includeHashtags ? "yes" : "no"} onValueChange={(v) => setIncludeHashtags(v === "yes")}>
                <SelectTrigger>
                  <SelectValue placeholder="Wybierz" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Dodaj hashtagi</SelectItem>
                  <SelectItem value="no">Bez hashtagow</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isPending || brief.length < 10}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generowanie...
              </>
            ) : (
              "Wygeneruj post"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
