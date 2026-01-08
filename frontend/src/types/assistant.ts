/**
 * Assistant types for Command Center.
 */

export interface InterpretRequest {
  message: string;
}

export interface InterpretResponse {
  intent: string;
  confidence: number;
  suggested_agents: string[];
  missing_info: string[];
  follow_up_questions: string[];
  can_auto_execute: boolean;
  extracted_params: Record<string, unknown>;
  quick_action_id: string | null;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  description: string;
  intent: string;
}

export interface QuickActionsResponse {
  actions: QuickAction[];
}

export interface QuickActionRequest {
  action_id: string;
  params?: Record<string, unknown>;
}
