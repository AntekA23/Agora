"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useCompany, useUpdateCompany } from "@/hooks/use-company";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Documentation } from "@/components/documentation";
import { Loader2, Save, Building2, User, Palette, Book, Settings } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const { data: company, isLoading } = useCompany();
  const updateCompany = useUpdateCompany();

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
          <TabsTrigger value="documentation" className="gap-2">
            <Book className="h-4 w-4" />
            Dokumentacja
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

            {/* Company Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Firma
                </CardTitle>
                <CardDescription>Informacje o firmie</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="companyName">Nazwa firmy</Label>
                  <Input id="companyName" value={company?.name || ""} disabled />
                </div>
                <div className="grid grid-cols-2 gap-4">
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
                    <Label htmlFor="companySize">Wielkosc</Label>
                    <Select
                      id="companySize"
                      value={companySize}
                      onChange={(e) => setCompanySize(e.target.value)}
                    >
                      <option value="micro">Mikro (1-9)</option>
                      <option value="small">Mala (10-49)</option>
                      <option value="medium">Srednia (50-249)</option>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Plan subskrypcji</Label>
                  <div>
                    <Badge variant="outline" className="capitalize">
                      {company?.subscription_plan || "free"}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Brand Settings */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="h-5 w-5" />
                  Ustawienia marki
                </CardTitle>
                <CardDescription>
                  Te ustawienia wplywaja na sposob komunikacji agentow AI
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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

                {updateCompany.isSuccess && (
                  <p className="text-sm text-green-600">Zmiany zostaly zapisane!</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="documentation">
          <Documentation />
        </TabsContent>
      </Tabs>
    </div>
  );
}
