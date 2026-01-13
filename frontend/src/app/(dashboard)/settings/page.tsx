"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useCompany, useUpdateCompany } from "@/hooks/use-company";
import { useWizardStatus } from "@/hooks/use-brand-wizard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Loader2, Save, Building2, User, Settings, Wand2, CheckCircle2, Plug, ChevronRight } from "lucide-react";
import { IntegrationsSettings } from "@/components/settings/integrations-settings";

export default function SettingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { data: company, isLoading } = useCompany();
  const updateCompany = useUpdateCompany();
  const { data: wizardStatus } = useWizardStatus();

  const [activeTab, setActiveTab] = useState("settings");
  const [brandVoice, setBrandVoice] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("small");

  useEffect(() => {
    if (company) {
      setBrandVoice(company.settings?.brand_voice || "");
      setTargetAudience(company.settings?.target_audience || "");
      setIndustry(company.industry || "");
      setCompanySize(company.size || "small");
    }
  }, [company]);

  const handleSaveCompany = () => {
    updateCompany.mutate({
      industry,
      size: companySize,
      settings: {
        brand_voice: brandVoice,
        target_audience: targetAudience,
        language: "pl",
      },
    });
  };

  const handleOpenWizard = () => {
    router.push("/brand-setup");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Ustawienia</h1>
        <p className="text-muted-foreground mt-1">
          Zarzadzaj ustawieniami konta i firmy
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="settings" className="gap-2">
            <Settings className="h-4 w-4" />
            Ustawienia
          </TabsTrigger>
          <TabsTrigger value="integrations" className="gap-2">
            <Plug className="h-4 w-4" />
            Integracje
          </TabsTrigger>
        </TabsList>

        <TabsContent value="settings">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* User Profile */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profil
                </CardTitle>
                <CardDescription>Twoje dane osobowe</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Imie i nazwisko</Label>
                  <Input id="name" defaultValue={user?.name || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" defaultValue={user?.email || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Rola</Label>
                  <div>
                    <Badge variant={user?.role === "admin" ? "default" : "secondary"}>
                      {user?.role === "admin" ? "Administrator" : "Czlonek"}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Subscription Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Subskrypcja
                </CardTitle>
                <CardDescription>Informacje o planie</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Plan subskrypcji</Label>
                  <div>
                    <Badge variant="outline" className="capitalize">
                      {company?.subscription_plan || "free"}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Aktywne moduly</Label>
                  <div className="flex gap-2 flex-wrap">
                    {company?.enabled_agents?.map((agent) => (
                      <Badge key={agent} variant="secondary" className="capitalize">
                        {agent}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Company & Brand Settings - Merged */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-5 w-5" />
                      Firma i marka
                    </CardTitle>
                    <CardDescription>
                      Informacje o firmie i ustawienia komunikacji AI
                    </CardDescription>
                  </div>
                  <Button
                    variant={wizardStatus?.wizard_completed ? "outline" : "default"}
                    onClick={handleOpenWizard}
                  >
                    {wizardStatus?.wizard_completed ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Edytuj w kreatorze
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4 mr-2" />
                        Otworz Kreator Marki
                      </>
                    )}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Quick edit fields */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="companyName">Nazwa firmy</Label>
                    <Input id="companyName" value={company?.name || ""} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="industry">Branza</Label>
                    <Input
                      id="industry"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      placeholder="np. e-commerce"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="companySize">Wielkosc firmy</Label>
                    <Select value={companySize} onValueChange={setCompanySize}>
                      <SelectTrigger>
                        <SelectValue placeholder="Wybierz wielkosc" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="micro">Mikro (1-9)</SelectItem>
                        <SelectItem value="small">Mala (10-49)</SelectItem>
                        <SelectItem value="medium">Srednia (50-249)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="border-t border-border pt-4">
                  <h4 className="font-medium mb-4">Podstawowe ustawienia komunikacji</h4>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="brandVoice">Brand voice</Label>
                      <Textarea
                        id="brandVoice"
                        value={brandVoice}
                        onChange={(e) => setBrandVoice(e.target.value)}
                        placeholder="Opisz ton komunikacji Twojej marki, np. 'Profesjonalny ale przyjazny, unikamy korporacyjnego jezyka'"
                        rows={3}
                      />
                      <p className="text-xs text-muted-foreground">
                        Jak powinna brzmiec komunikacja Twojej firmy?
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="targetAudience">Grupa docelowa</Label>
                      <Textarea
                        id="targetAudience"
                        value={targetAudience}
                        onChange={(e) => setTargetAudience(e.target.value)}
                        placeholder="Opisz swojego idealnego klienta, np. 'Kobiety 25-40 lat zainteresowane zdrowym stylem zycia'"
                        rows={3}
                      />
                      <p className="text-xs text-muted-foreground">
                        Do kogo kierujesz swoje produkty/uslugi?
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <p className="text-sm text-muted-foreground">
                    Uzyj Kreatora Marki aby skonfigurowac pelny profil firmy
                  </p>
                  <Button
                    onClick={handleSaveCompany}
                    disabled={updateCompany.isPending}
                  >
                    {updateCompany.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Zapisywanie...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Zapisz zmiany
                      </>
                    )}
                  </Button>
                </div>

                {updateCompany.isSuccess && (
                  <p className="text-sm text-green-600">Zmiany zostaly zapisane!</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="integrations">
          <IntegrationsSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
