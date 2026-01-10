"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useTokenRefresh } from "@/hooks/use-token-refresh";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, fetchUser } = useAuth();
  const [isChecking, setIsChecking] = useState(true);

  // Proaktywne odświeżanie tokenu przed wygaśnięciem
  useTokenRefresh();

  useEffect(() => {
    const checkAuth = async () => {
      await fetchUser();
      setIsChecking(false);
    };
    checkAuth();
  }, [fetchUser]);

  useEffect(() => {
    if (!isChecking && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isChecking, isAuthenticated, router]);

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
