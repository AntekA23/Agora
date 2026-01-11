"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Users, Plus, Trash2 } from "lucide-react";
import { TagInput } from "./tag-input";

export interface ProductItem {
  name: string;
  description: string;
}

export interface MarketData {
  target_audience: string;
  audience_age_from: number | null;
  audience_age_to: number | null;
  audience_locations: string[];
  audience_interests: string[];
  products: ProductItem[];
  services: ProductItem[];
  unique_selling_points: string[];
}

interface StepMarketProps {
  data: MarketData;
  onChange: (data: MarketData) => void;
}

export function StepMarket({ data, onChange }: StepMarketProps) {
  const updateField = <K extends keyof MarketData>(
    field: K,
    value: MarketData[K]
  ) => {
    onChange({ ...data, [field]: value });
  };

  const addProduct = () => {
    updateField("products", [...data.products, { name: "", description: "" }]);
  };

  const updateProduct = (index: number, product: ProductItem) => {
    const products = [...data.products];
    products[index] = product;
    updateField("products", products);
  };

  const removeProduct = (index: number) => {
    updateField(
      "products",
      data.products.filter((_, i) => i !== index)
    );
  };

  const addService = () => {
    updateField("services", [...data.services, { name: "", description: "" }]);
  };

  const updateService = (index: number, service: ProductItem) => {
    const services = [...data.services];
    services[index] = service;
    updateField("services", services);
  };

  const removeService = (index: number) => {
    updateField(
      "services",
      data.services.filter((_, i) => i !== index)
    );
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Users className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Klienci i rynek
        </h2>
        <p className="text-muted-foreground">
          Opisz swoich klientow i oferte
        </p>
      </div>

      {/* Target Audience Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Grupa docelowa
        </h3>

        <div className="space-y-2">
          <Label htmlFor="target-audience">Opis grupy docelowej *</Label>
          <Textarea
            id="target-audience"
            value={data.target_audience}
            onChange={(e) => updateField("target_audience", e.target.value)}
            placeholder="Opisz swojego idealnego klienta - kim jest, czym sie zajmuje, jakie ma potrzeby..."
            rows={3}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="age-from">Wiek od</Label>
            <Input
              id="age-from"
              type="number"
              value={data.audience_age_from || ""}
              onChange={(e) =>
                updateField(
                  "audience_age_from",
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
              placeholder="18"
              min="1"
              max="100"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="age-to">Wiek do</Label>
            <Input
              id="age-to"
              type="number"
              value={data.audience_age_to || ""}
              onChange={(e) =>
                updateField(
                  "audience_age_to",
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
              placeholder="65"
              min="1"
              max="100"
            />
          </div>
        </div>

        <TagInput
          label="Lokalizacje klientow"
          placeholder="np. Warszawa, Krakow, cala Polska..."
          tags={data.audience_locations}
          onChange={(locations) => updateField("audience_locations", locations)}
        />

        <TagInput
          label="Zainteresowania klientow"
          placeholder="np. biznes, marketing, technologia..."
          tags={data.audience_interests}
          onChange={(interests) => updateField("audience_interests", interests)}
        />
      </div>

      {/* Products Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-2">
          <h3 className="text-lg font-semibold text-foreground">Produkty</h3>
          <Button variant="outline" size="sm" onClick={addProduct}>
            <Plus className="h-4 w-4 mr-1" />
            Dodaj produkt
          </Button>
        </div>

        {data.products.length > 0 ? (
          <div className="space-y-3">
            {data.products.map((product, index) => (
              <div
                key={index}
                className="p-4 border border-border rounded-lg bg-card space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <Input
                    value={product.name}
                    onChange={(e) =>
                      updateProduct(index, { ...product, name: e.target.value })
                    }
                    placeholder="Nazwa produktu"
                    className="font-medium"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeProduct(index)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
                <Textarea
                  value={product.description}
                  onChange={(e) =>
                    updateProduct(index, {
                      ...product,
                      description: e.target.value,
                    })
                  }
                  placeholder="Krotki opis produktu"
                  rows={2}
                />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
            Brak produktow. Kliknij &quot;Dodaj produkt&quot; aby dodac.
          </p>
        )}
      </div>

      {/* Services Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-2">
          <h3 className="text-lg font-semibold text-foreground">Uslugi</h3>
          <Button variant="outline" size="sm" onClick={addService}>
            <Plus className="h-4 w-4 mr-1" />
            Dodaj usluge
          </Button>
        </div>

        {data.services.length > 0 ? (
          <div className="space-y-3">
            {data.services.map((service, index) => (
              <div
                key={index}
                className="p-4 border border-border rounded-lg bg-card space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <Input
                    value={service.name}
                    onChange={(e) =>
                      updateService(index, { ...service, name: e.target.value })
                    }
                    placeholder="Nazwa uslugi"
                    className="font-medium"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeService(index)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
                <Textarea
                  value={service.description}
                  onChange={(e) =>
                    updateService(index, {
                      ...service,
                      description: e.target.value,
                    })
                  }
                  placeholder="Krotki opis uslugi"
                  rows={2}
                />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
            Brak uslug. Kliknij &quot;Dodaj usluge&quot; aby dodac.
          </p>
        )}
      </div>

      {/* USPs Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">
          Przewagi konkurencyjne
        </h3>

        <TagInput
          label="Co wyroznia Twoja firme?"
          placeholder="np. najszybsza dostawa, 10 lat doswiadczenia..."
          tags={data.unique_selling_points}
          onChange={(usps) => updateField("unique_selling_points", usps)}
        />
      </div>
    </div>
  );
}
