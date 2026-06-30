export interface SchoolMatchItem {
  name: string;
  qs_rank: number | null;
  usnews_rank: number | null;
  matched_cases: number;
  gpa_min: number | null;
  gpa_max: number | null;
  gpa_p50: number | null;
  majors: string[];
  meets_requirement: boolean;
  requirement_value: number | null;
  admission_chance: string;
  admission_score: number;
  p50_reference: number | null;
  gpa_gap: number | null;
}

export interface CountryMatchResult {
  country: string;
  matched_cases: number;
  matched_schools: number;
  schools: SchoolMatchItem[];
}

export interface BackgroundInfo {
  gpa_percent: number | null;
  gpa4: number | null;
  school_tier: number;
  school_tier_label: string;
}

export interface MatchSummary {
  total_cases: number;
  total_schools: number;
}

export interface PathwayProgram {
  provider: string;
  program_type: string;
  direction: string;
  location: string;
  duration: string;
  intake: string;
  academic_req: string;
  ielts_req: string;
  tuition_note: string;
}

export interface PathwaySuggestion {
  university: string;
  country: string;
  qs_rank: number | null;
  usnews_rank: number | null;
  programs: PathwayProgram[];
  reason: string;
}

export interface RecommendResult {
  background: BackgroundInfo;
  match_summary: MatchSummary;
  by_country: CountryMatchResult[];
  pathway_suggestions: PathwaySuggestion[];
  generated_at: string;
}

export interface RecommendRequest {
  target_countries: string[];
  gpa_score: number;
  gpa_format: string;
  study_level: string;
  target_major?: string;
  original_major?: string;
  undergraduate_school?: string;
}

export type ViewMode = "cards" | "table";

export interface MBTIType {
  type: string;
  name: string;
  learning_style: string;
}

export interface MBTIMajorResult {
  type: string;
  name: string;
  top_majors: string[];
  avoid_majors: string[];
  learning_style: string;
  career_path: string;
  study_tips: string;
}

export interface TimelinePhase {
  month: string;
  phase: string;
  tasks: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  reasoning?: string;
}

export interface ChatRequest {
  messages: { role: "user" | "assistant"; content: string }[];
  stream?: boolean;
}
