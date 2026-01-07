export interface User {
  id: string;
  email: string;
  name: string;
  company_id: string | null;
  role: "admin" | "member";
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: "light" | "dark";
  language: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  industry: string;
  size: "micro" | "small" | "medium";
  settings: CompanySettings;
  enabled_agents: string[];
  subscription_plan: string;
  subscription_valid_until: string | null;
  created_at: string;
}

export interface CompanySettings {
  brand_voice: string;
  target_audience: string;
  language: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  company_name: string;
}
