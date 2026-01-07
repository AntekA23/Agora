export type TaskStatus = "pending" | "processing" | "completed" | "failed";

export interface Task {
  id: string;
  company_id: string;
  user_id: string;
  department: string;
  agent: string;
  type: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  status: TaskStatus;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  per_page: number;
}

export interface InstagramTaskInput {
  brief: string;
  post_type: "post" | "story" | "reel" | "carousel";
  include_hashtags: boolean;
}

export interface CopywriterTaskInput {
  brief: string;
  copy_type: "ad" | "email" | "landing" | "slogan" | "description";
  max_length?: number;
}
