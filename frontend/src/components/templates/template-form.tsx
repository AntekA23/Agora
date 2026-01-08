"use client";

import * as React from "react";
import {
  Template,
  TemplateCategory,
  TemplateField,
  useTemplateHistory,
  useSaveTemplateHistory,
} from "@/hooks/use-templates";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Loader2,
  RotateCcw,
  History,
  PackagePlus,
  Percent,
  Lightbulb,
  Calendar,
  Clapperboard,
  Megaphone,
  Mail,
  Quote,
  Globe,
  PenTool,
} from "lucide-react";

// Icon mapping
const iconMap: Record<string, React.ElementType> = {
  "package-plus": PackagePlus,
  percent: Percent,
  lightbulb: Lightbulb,
  calendar: Calendar,
  clapperboard: Clapperboard,
  sparkles: Sparkles,
  megaphone: Megaphone,
  mail: Mail,
  quote: Quote,
  globe: Globe,
  "pen-tool": PenTool,
};

interface TemplateFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  category: TemplateCategory | null;
  template: Template | null;
  onSubmit: (params: Record<string, unknown>, prompt: string) => void;
  isSubmitting?: boolean;
}

export function TemplateForm({
  open,
  onOpenChange,
  category,
  template,
  onSubmit,
  isSubmitting = false,
}: TemplateFormProps) {
  const [formData, setFormData] = React.useState<Record<string, unknown>>({});
  const [hasLoadedHistory, setHasLoadedHistory] = React.useState(false);

  const { data: historyData } = useTemplateHistory(
    category?.id || "",
    template?.id || ""
  );
  const saveHistory = useSaveTemplateHistory();

  // Reset form when template changes
  React.useEffect(() => {
    if (template) {
      const initialData: Record<string, unknown> = {};
      template.fields.forEach((field) => {
        if (field.type === "checkbox") {
          initialData[field.name] = false;
        } else if (field.type === "select" && field.options?.length) {
          initialData[field.name] = field.options[0];
        } else {
          initialData[field.name] = "";
        }
      });
      setFormData(initialData);
      setHasLoadedHistory(false);
    }
  }, [template]);

  // Load history when available
  React.useEffect(() => {
    if (historyData?.last_used && !hasLoadedHistory && template) {
      setHasLoadedHistory(true);
    }
  }, [historyData, hasLoadedHistory, template]);

  const loadFromHistory = () => {
    if (historyData?.last_used) {
      setFormData((prev) => ({
        ...prev,
        ...historyData.last_used,
      }));
    }
  };

  const resetForm = () => {
    if (template) {
      const initialData: Record<string, unknown> = {};
      template.fields.forEach((field) => {
        if (field.type === "checkbox") {
          initialData[field.name] = false;
        } else if (field.type === "select" && field.options?.length) {
          initialData[field.name] = field.options[0];
        } else {
          initialData[field.name] = "";
        }
      });
      setFormData(initialData);
    }
  };

  const updateField = (name: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const shouldShowField = (field: TemplateField): boolean => {
    if (!field.showIf || Object.keys(field.showIf).length === 0) {
      return true;
    }
    return Object.entries(field.showIf).every(
      ([key, value]) => formData[key] === value
    );
  };

  const isFormValid = (): boolean => {
    if (!template) return false;
    return template.fields.every((field) => {
      if (!field.required) return true;
      if (!shouldShowField(field)) return true;
      const value = formData[field.name];
      if (field.type === "checkbox") return true;
      return value !== undefined && value !== "";
    });
  };

  const buildPrompt = (): string => {
    if (!template) return "";
    let prompt = template.default_prompt;

    // Replace placeholders with actual values
    Object.entries(formData).forEach(([key, value]) => {
      const placeholder = `{${key}}`;
      prompt = prompt.replace(placeholder, String(value || ""));
    });

    // Handle special cases
    if (formData.price) {
      prompt = prompt.replace("{price_text}", `Cena: ${formData.price}.`);
    } else {
      prompt = prompt.replace("{price_text}", "");
    }

    if (formData.valid_until) {
      prompt = prompt.replace("{validity}", `Wazne do: ${formData.valid_until}.`);
    } else {
      prompt = prompt.replace("{validity}", "");
    }

    if (formData.discount === "Inna wartosc" && formData.discount_custom) {
      prompt = prompt.replace("{discount_value}", String(formData.discount_custom));
    } else if (formData.discount) {
      prompt = prompt.replace("{discount_value}", String(formData.discount));
    }

    if (formData.promo_code) {
      prompt = prompt.replace("{promo_code_text}", `Kod: ${formData.promo_code}.`);
    } else {
      prompt = prompt.replace("{promo_code_text}", "");
    }

    if (formData.event_date) {
      prompt = prompt.replace("{date_text}", `Data: ${formData.event_date}.`);
    } else {
      prompt = prompt.replace("{date_text}", "");
    }

    if (formData.include_cta) {
      prompt = prompt.replace("{cta_instruction}", "Dodaj wezwanie do dzialania.");
    } else {
      prompt = prompt.replace("{cta_instruction}", "");
    }

    if (formData.seo_keywords) {
      prompt = prompt.replace("{seo_text}", `Slowa kluczowe SEO: ${formData.seo_keywords}.`);
    } else {
      prompt = prompt.replace("{seo_text}", "");
    }

    return prompt.trim();
  };

  const handleSubmit = () => {
    if (!category || !template) return;

    const prompt = buildPrompt();

    // Save to history
    saveHistory.mutate({
      template_id: template.id,
      category_id: category.id,
      params: formData,
    });

    onSubmit(formData, prompt);
  };

  if (!template || !category) return null;

  const TemplateIcon = iconMap[template.icon] || Sparkles;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
              <TemplateIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>{template.name}</DialogTitle>
              <p className="text-sm text-muted-foreground">{category.name}</p>
            </div>
          </div>
        </DialogHeader>

        {/* Auto-recall banner */}
        {historyData?.last_used && historyData.usage_count > 0 && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 text-sm">
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-muted-foreground" />
              <span>
                Uzyles tego szablonu{" "}
                <strong>{historyData.usage_count}x</strong>
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={loadFromHistory}>
              Uzyj poprzednich
            </Button>
          </div>
        )}

        {/* Form fields */}
        <div className="flex-1 overflow-auto space-y-4 py-4">
          {template.fields.map((field) => {
            if (!shouldShowField(field)) return null;

            return (
              <div key={field.name} className="space-y-2">
                <Label htmlFor={field.name}>
                  {field.label}
                  {field.required && (
                    <span className="text-destructive ml-1">*</span>
                  )}
                </Label>

                {field.type === "text" && (
                  <Input
                    id={field.name}
                    value={String(formData[field.name] || "")}
                    onChange={(e) => updateField(field.name, e.target.value)}
                    placeholder={`Wpisz ${field.label.toLowerCase()}...`}
                  />
                )}

                {field.type === "textarea" && (
                  <Textarea
                    id={field.name}
                    value={String(formData[field.name] || "")}
                    onChange={(e) => updateField(field.name, e.target.value)}
                    placeholder={`Wpisz ${field.label.toLowerCase()}...`}
                    rows={3}
                  />
                )}

                {field.type === "select" && field.options && (
                  <Select
                    value={String(formData[field.name] || field.options[0] || "")}
                    onValueChange={(v) => updateField(field.name, v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Wybierz..." />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {field.type === "date" && (
                  <Input
                    id={field.name}
                    type="date"
                    value={String(formData[field.name] || "")}
                    onChange={(e) => updateField(field.name, e.target.value)}
                  />
                )}

                {field.type === "checkbox" && (
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id={field.name}
                      checked={Boolean(formData[field.name])}
                      onCheckedChange={(checked) =>
                        updateField(field.name, checked)
                      }
                    />
                    <label
                      htmlFor={field.name}
                      className="text-sm cursor-pointer"
                    >
                      {field.label}
                    </label>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between">
          <Button variant="ghost" size="sm" onClick={resetForm}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Resetuj
          </Button>
          <Button onClick={handleSubmit} disabled={!isFormValid() || isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generowanie...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generuj
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
