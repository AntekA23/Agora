"use client";

import { useState } from "react";
import { useCreateInvoiceTask } from "@/hooks/use-finance";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, FileText, Plus, Trash2 } from "lucide-react";
import type { InvoiceItem } from "@/types/finance";

interface InvoiceFormProps {
  onTaskCreated?: (taskId: string) => void;
}

export function InvoiceForm({ onTaskCreated }: InvoiceFormProps) {
  const [clientName, setClientName] = useState("");
  const [clientAddress, setClientAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<InvoiceItem[]>([
    { name: "", quantity: 1, price: 0 },
  ]);

  const { mutate, isPending, error } = useCreateInvoiceTask();

  const addItem = () => {
    setItems([...items, { name: "", quantity: 1, price: 0 }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof InvoiceItem, value: string | number) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    setItems(newItems);
  };

  const total = items.reduce((sum, item) => sum + item.quantity * item.price, 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!clientName || !clientAddress || items.some(i => !i.name || i.price <= 0)) {
      return;
    }

    mutate(
      { client_name: clientName, client_address: clientAddress, items, notes },
      {
        onSuccess: (task) => {
          setClientName("");
          setClientAddress("");
          setNotes("");
          setItems([{ name: "", quantity: 1, price: 0 }]);
          onTaskCreated?.(task.id);
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Faktura VAT
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
              {error instanceof Error ? error.message : "Wystapil blad"}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="clientName">Nazwa klienta</Label>
              <Input
                id="clientName"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="Firma ABC Sp. z o.o."
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="clientAddress">Adres</Label>
              <Input
                id="clientAddress"
                value={clientAddress}
                onChange={(e) => setClientAddress(e.target.value)}
                placeholder="ul. Przykladowa 1, 00-001 Warszawa"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Pozycje faktury</Label>
            {items.map((item, index) => (
              <div key={index} className="flex gap-2 items-end">
                <div className="flex-1">
                  <Input
                    value={item.name}
                    onChange={(e) => updateItem(index, "name", e.target.value)}
                    placeholder="Nazwa uslugi/produktu"
                    required
                  />
                </div>
                <div className="w-20">
                  <Input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => updateItem(index, "quantity", parseInt(e.target.value) || 1)}
                    min={1}
                    required
                  />
                </div>
                <div className="w-28">
                  <Input
                    type="number"
                    value={item.price || ""}
                    onChange={(e) => updateItem(index, "price", parseFloat(e.target.value) || 0)}
                    placeholder="Cena"
                    min={0}
                    step={0.01}
                    required
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeItem(index)}
                  disabled={items.length === 1}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={addItem}>
              <Plus className="h-4 w-4 mr-1" />
              Dodaj pozycje
            </Button>
          </div>

          <div className="text-right text-sm text-muted-foreground">
            Suma netto: <span className="font-medium">{total.toFixed(2)} PLN</span>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Uwagi (opcjonalnie)</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Dodatkowe informacje..."
              rows={2}
            />
          </div>

          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generowanie...
              </>
            ) : (
              "Wygeneruj fakture"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
