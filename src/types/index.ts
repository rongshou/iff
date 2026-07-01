export interface MBTIMajorResult {
  type: string;
  name: string;
  top_majors: string[];
  avoid_majors: string[];
  learning_style: string;
  career_path: string;
  study_tips: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  reasoning?: string;
}
