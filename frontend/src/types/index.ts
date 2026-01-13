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
  wizard_completed?: boolean;
}

// Brand Wizard Types
export interface BrandWizardStep1 {
  company_description: string;
  founded_year: number | null;
  location: string;
  website: string;
}

export interface BrandWizardStep2 {
  mission: string;
  vision: string;
  values: string[];
  personality_traits: string[];
  unique_value_proposition: string;
}

export interface BrandWizardStep3 {
  description: string;
  age_from: number | null;
  age_to: number | null;
  gender: string;
  locations: string[];
  interests: string[];
  pain_points: string[];
  goals: string[];
  where_they_are: string[];
}

export interface ProductInput {
  name: string;
  description: string;
  price: number | null;
  category: string;
  features: string[];
  unique_selling_points: string[];
  visual_description: string;  // Opis wizualny dla AI (po angielsku)
}

export interface ServiceInput {
  name: string;
  description: string;
  price_from: number | null;
  price_to: number | null;
  duration: string;
  benefits: string[];
  visual_description: string;  // Opis wizualny dla AI (po angielsku)
}

export interface CompetitorInput {
  name: string;
  website: string;
  strengths: string[];
  weaknesses: string[];
  notes: string;
}

export interface BrandWizardStep4 {
  products: ProductInput[];
  services: ServiceInput[];
  price_positioning: string;
}

export interface BrandWizardStep5 {
  competitors: CompetitorInput[];
  market_position: string;
  key_differentiators: string[];
}

export interface BrandWizardStep6 {
  formality_level: number;
  emoji_usage: string;
  words_to_use: string[];
  words_to_avoid: string[];
  example_phrases: string[];
}

export interface BrandWizardStep7 {
  themes: string[];
  hashtag_style: string;
  branded_hashtags: string[];
  post_frequency: string;
  preferred_formats: string[];
  content_goals: string[];
}

export interface BrandWizardComplete {
  step1: BrandWizardStep1;
  step2: BrandWizardStep2;
  step3: BrandWizardStep3;
  step4: BrandWizardStep4;
  step5: BrandWizardStep5;
  step6: BrandWizardStep6;
  step7: BrandWizardStep7;
}

export interface WebsiteAnalyzeResponse {
  success: boolean;
  data: Record<string, unknown>;
  error?: string;
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
