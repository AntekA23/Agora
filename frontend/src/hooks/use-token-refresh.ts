"use client";

import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useAuth } from "./use-auth";

const REFRESH_CHECK_INTERVAL = 60 * 1000; // Sprawdzaj co minutę
const TOKEN_EXPIRY_THRESHOLD = 5 * 60; // Odśwież jeśli zostało mniej niż 5 minut

/**
 * Hook do proaktywnego odświeżania tokenu przed jego wygaśnięciem.
 * Powinien być używany w głównym layoucie lub ProtectedRoute.
 */
export function useTokenRefresh() {
  const { isAuthenticated, refreshToken, logout } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      // Wyczyść interval gdy użytkownik się wylogował
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const checkAndRefreshToken = async () => {
      // Sprawdź czy token wygasa wkrótce
      if (api.isTokenExpiringSoon(TOKEN_EXPIRY_THRESHOLD)) {
        const success = await refreshToken();
        if (!success) {
          // Refresh się nie powiódł - wyloguj
          logout();
        }
      }
    };

    // Sprawdź od razu przy montowaniu
    checkAndRefreshToken();

    // Ustaw interval do regularnego sprawdzania
    intervalRef.current = setInterval(checkAndRefreshToken, REFRESH_CHECK_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAuthenticated, refreshToken, logout]);
}
