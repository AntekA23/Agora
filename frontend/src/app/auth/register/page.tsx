"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const name = formData.get("name") as string;
    const company_name = formData.get("company_name") as string;

    if (password.length < 8) {
      setError("Haslo musi miec minimum 8 znakow");
      return;
    }

    try {
      await register({ email, password, name, company_name });
      // Redirect to brand setup wizard for new users
      router.push("/brand-setup");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Stworz konto</CardTitle>
        <CardDescription>
          Zarejestruj sie i zacznij automatyzowac swoja firme
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="name">Imie i nazwisko</Label>
            <Input
              id="name"
              name="name"
              type="text"
              placeholder="Jan Kowalski"
              required
              autoComplete="name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="jan@firma.pl"
              required
              autoComplete="email"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company_name">Nazwa firmy</Label>
            <Input
              id="company_name"
              name="company_name"
              type="text"
              placeholder="Moja Firma Sp. z o.o."
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Haslo</Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="Minimum 8 znakow"
              required
              autoComplete="new-password"
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Rejestracja..." : "Zarejestruj sie"}
          </Button>
          <p className="text-sm text-muted-foreground text-center">
            Masz juz konto?{" "}
            <Link
              href="/auth/login"
              className="text-primary underline-offset-4 hover:underline"
            >
              Zaloguj sie
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
