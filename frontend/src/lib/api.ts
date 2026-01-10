const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiError {
  detail: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

type QueuedRequest = {
  resolve: (token: string) => void;
  reject: (error: Error) => void;
};

class ApiClient {
  private baseUrl: string;
  private isRefreshing = false;
  private refreshQueue: QueuedRequest[] = [];

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("refresh_token");
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
  }

  private clearTokens(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  private async refreshAccessToken(): Promise<string | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return null;
      }

      const data: TokenResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch {
      this.clearTokens();
      return null;
    }
  }

  private async handleTokenRefresh(): Promise<string | null> {
    if (this.isRefreshing) {
      // Jeśli już trwa refresh, dodaj żądanie do kolejki
      return new Promise((resolve, reject) => {
        this.refreshQueue.push({ resolve, reject });
      });
    }

    this.isRefreshing = true;

    try {
      const newToken = await this.refreshAccessToken();

      if (newToken) {
        // Rozwiąż wszystkie oczekujące żądania z nowym tokenem
        this.refreshQueue.forEach((request) => request.resolve(newToken));
      } else {
        // Odrzuć wszystkie oczekujące żądania
        const error = new Error("Token refresh failed");
        this.refreshQueue.forEach((request) => request.reject(error));
      }

      return newToken;
    } finally {
      this.isRefreshing = false;
      this.refreshQueue = [];
    }
  }

  private redirectToLogin(): void {
    if (typeof window !== "undefined") {
      this.clearTokens();
      window.location.href = "/auth/login";
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry = false
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    // Obsługa błędu 401 - spróbuj odświeżyć token
    if (response.status === 401 && !isRetry) {
      // Nie próbuj refresh dla endpointów auth
      if (endpoint.includes("/auth/")) {
        const error: ApiError = await response.json().catch(() => ({
          detail: "Authentication failed",
        }));
        throw new Error(error.detail);
      }

      const newToken = await this.handleTokenRefresh();

      if (newToken) {
        // Ponów żądanie z nowym tokenem
        return this.request<T>(endpoint, options, true);
      } else {
        // Refresh się nie powiódł - przekieruj do logowania
        this.redirectToLogin();
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: "An error occurred",
      }));
      throw new Error(error.detail);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  // Metoda do manualnego odświeżenia tokenu (używana przez use-auth)
  async refreshToken(): Promise<boolean> {
    const newToken = await this.refreshAccessToken();
    return newToken !== null;
  }

  // Sprawdza czy token wygaśnie w ciągu podanej liczby sekund
  isTokenExpiringSoon(thresholdSeconds: number = 300): boolean {
    const token = this.getToken();
    if (!token) return true;

    try {
      // Dekodowanie JWT bez biblioteki (payload jest w base64)
      const parts = token.split(".");
      if (parts.length !== 3) return true;

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp * 1000; // exp jest w sekundach
      const now = Date.now();
      const timeUntilExpiry = expiresAt - now;

      return timeUntilExpiry < thresholdSeconds * 1000;
    } catch {
      return true;
    }
  }
}

export const api = new ApiClient(`${API_URL}/api/v1`);
