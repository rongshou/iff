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
