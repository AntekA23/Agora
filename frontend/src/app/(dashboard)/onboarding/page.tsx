"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

/**
 * Old onboarding page - now redirects to the new fullscreen Brand Wizard.
 * This page is kept for backwards compatibility with old links.
 */
export default function OnboardingRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the new brand setup wizard
    router.replace("/brand-setup");
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
      <p className="text-muted-foreground">Przekierowywanie do Kreatora Marki...</p>
    </div>
  );
}
