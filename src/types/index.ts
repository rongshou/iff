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
  recommendPayload?: any;
}

export interface FavoriteSchool {
  name: string;
  country: string;
  qs_rank?: number;
  usnews_rank?: number;
  match_level: string;
  gpa_median?: number;
  matched_cases: number;
  toefl_display?: { type: string; value: number; label: string };
  meets_toefl?: boolean;
}
