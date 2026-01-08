"use client";

import * as React from "react";
import {
  useTemplates,
  useRecentTemplates,
  TemplateCategory,
  Template,
} from "@/hooks/use-templates";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Instagram,
  FileText,
  PackagePlus,
  Percent,
  Lightbulb,
  Calendar,
  Clapperboard,
  Sparkles,
  Megaphone,
  Mail,
  Quote,
  Globe,
  PenTool,
  Clock,
  Loader2,
  ChevronRight,
} from "lucide-react";

// Icon mapping
const iconMap: Record<string, React.ElementType> = {
  instagram: Instagram,
  "file-text": FileText,
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

interface TemplatePickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectTemplate: (category: TemplateCategory, template: Template) => void;
}

export function TemplatePicker({
  open,
  onOpenChange,
  onSelectTemplate,
}: TemplatePickerProps) {
  const { data: templatesData, isLoading } = useTemplates();
  const { data: recentTemplates } = useRecentTemplates(3);
  const [activeTab, setActiveTab] = React.useState("social_media");

  const categories = templatesData?.categories ?? [];

  // Update active tab when categories load
  React.useEffect(() => {
    if (categories.length > 0 && !categories.find((c) => c.id === activeTab)) {
      setActiveTab(categories[0].id);
    }
  }, [categories, activeTab]);

  const getIcon = (iconName: string) => {
    return iconMap[iconName] || Sparkles;
  };

  const handleSelectTemplate = (
    category: TemplateCategory,
    template: Template
  ) => {
    onSelectTemplate(category, template);
    onOpenChange(false);
  };

  const findTemplateById = (categoryId: string, templateId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    const template = category?.templates.find((t) => t.id === templateId);
    return { category, template };
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Wybierz szablon</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="flex-1 overflow-hidden">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
              <TabsList className="w-full justify-start">
                {categories.map((category) => {
                  const CategoryIcon = getIcon(category.icon);
                  return (
                    <TabsTrigger
                      key={category.id}
                      value={category.id}
                      className="gap-2"
                    >
                      <CategoryIcon className="h-4 w-4" />
                      {category.name}
                    </TabsTrigger>
                  );
                })}
              </TabsList>

              {/* Recent templates */}
              {recentTemplates && recentTemplates.length > 0 && (
                <div className="mt-4 mb-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <Clock className="h-4 w-4" />
                    <span>Ostatnio uzywane</span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {recentTemplates.map((entry, idx) => {
                      const { category, template } = findTemplateById(
                        entry.category_id,
                        entry.template_id
                      );
                      if (!category || !template) return null;
                      const TemplateIcon = getIcon(template.icon);
                      return (
                        <Button
                          key={idx}
                          variant="outline"
                          size="sm"
                          className="gap-2"
                          onClick={() => handleSelectTemplate(category, template)}
                        >
                          <TemplateIcon className="h-3 w-3" />
                          {template.name}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Template lists */}
              <div className="flex-1 overflow-auto mt-4">
                {categories.map((category) => (
                  <TabsContent
                    key={category.id}
                    value={category.id}
                    className="mt-0 space-y-2"
                  >
                    {category.templates.map((template) => {
                      const TemplateIcon = getIcon(template.icon);
                      return (
                        <button
                          key={template.id}
                          onClick={() => handleSelectTemplate(category, template)}
                          className="w-full flex items-center justify-between p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors text-left"
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                              <TemplateIcon className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">{template.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {template.description}
                              </p>
                            </div>
                          </div>
                          <ChevronRight className="h-5 w-5 text-muted-foreground" />
                        </button>
                      );
                    })}
                  </TabsContent>
                ))}
              </div>
            </Tabs>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
