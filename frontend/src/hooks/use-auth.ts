"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";
import type { User, TokenResponse, LoginRequest, RegisterRequest } from "@/types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,

      login: async (data: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response = await api.post<TokenResponse>("/auth/login", data);
          localStorage.setItem("access_token", response.access_token);
          localStorage.setItem("refresh_token", response.refresh_token);

          const user = await api.get<User>("/auth/me");
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true });
        try {
          const response = await api.post<TokenResponse>("/auth/register", data);
          localStorage.setItem("access_token", response.access_token);
          localStorage.setItem("refresh_token", response.refresh_token);

          const user = await api.get<User>("/auth/me");
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await api.get<User>("/auth/me");
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          // API client sam obsłuży 401 i spróbuje refresh
          // Jeśli się nie uda, tokeny zostaną usunięte przez API client
          const hasToken = localStorage.getItem("access_token");
          if (!hasToken) {
            set({ user: null, isAuthenticated: false, isLoading: false });
          } else {
            // Token nadal istnieje - może to być inny błąd
            set({ isLoading: false });
          }
        }
      },

      refreshToken: async () => {
        try {
          const success = await api.refreshToken();
          if (!success) {
            get().logout();
          }
          return success;
        } catch {
          get().logout();
          return false;
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }),
    }
  )
);
