const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function userIdFromToken(token: string): string {
  try {
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(b64)) as { sub?: string };
    return payload.sub ?? "anon";
  } catch {
    return "anon";
  }
}

export function historyKey(token: string): string {
  return `tl_history_${userIdFromToken(token)}`;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface SessionResponse {
  id: string;
  user_id: string;
  passage_id: string;
  status: string;
  passage_content?: string;
  mode?: undefined; // regular sessions carry no mode field
}

export async function createGuestSession(): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/guest`, { method: "POST" });
  if (!res.ok) throw new Error(`Guest creation failed: ${res.status}`);
  return res.json() as Promise<TokenResponse>;
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  return res.json() as Promise<TokenResponse>;
}

export async function register(
  email: string,
  displayName: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, display_name: displayName, password }),
  });
  if (!res.ok) throw new Error(`Registration failed: ${res.status}`);
  return res.json() as Promise<TokenResponse>;
}

export type SessionMode = "mine" | "cloze" | "drill";

export interface MineSessionResponse {
  id: string;
  mode: "mine";
  passage: string;
  target_words: string[];
}

export interface ClozeItem {
  full: string;
  stem: string;
  answer: string;
}

export interface ClozeSessionResponse {
  id: string;
  mode: "cloze";
  items: ClozeItem[];
}

export interface DrillRound {
  round_type: "model" | "vary" | "produce";
  text: string;
  stem?: string;
  target_word?: string;
}

export interface DrillSessionResponse {
  id: string;
  mode: "drill";
  rounds: DrillRound[];
  grammar_target: string;
}

export type AnySessionResponse =
  | SessionResponse
  | MineSessionResponse
  | ClozeSessionResponse
  | DrillSessionResponse;

export async function startSession(
  token: string,
  mode?: SessionMode,
): Promise<AnySessionResponse> {
  const url = mode
    ? `${API_BASE}/api/v1/sessions?mode=${mode}`
    : `${API_BASE}/api/v1/sessions`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(`${res.status}:${body.detail ?? ""}`);
  }
  return res.json() as Promise<AnySessionResponse>;
}

export async function abandonSession(token: string, sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/abandon`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function completeSession(
  token: string,
  sessionId: string,
  wpm: number,
  accuracy: number,
  durationSeconds: number,
): Promise<void> {
  await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      keystrokes: [],
      metrics: { wpm, accuracy, duration_seconds: durationSeconds, per_key_stats: {} },
    }),
  });
}

export async function refreshToken(token: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  return res.json() as Promise<TokenResponse>;
}

export interface SkillsResponse {
  motor: { overall_wpm: number; overall_accuracy: number; weak_keys: string[] };
  cognitive: {
    grammar_level: number;
    vocabulary_tier: number;
    cefr_level: string;
    weak_areas: string[];
    strong_areas: string[];
  };
}

export async function fetchSkills(token: string): Promise<SkillsResponse> {
  const res = await fetch(`${API_BASE}/api/v1/users/me/skills`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Skills fetch failed: ${res.status}`);
  return res.json() as Promise<SkillsResponse>;
}

export function createKeystrokeSocket(sessionId: string, token: string): WebSocket {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/api/v1/sessions/${sessionId}/stream?token=${token}`);
}

// ── Vocab ────────────────────────────────────────────────────────────────────

export interface VocabWordResponse {
  word: string;
  cefr_level: string;
  pos: string;
  definition: string;
  etymology: string;
  register: string;
  contrast_note: string;
  memory_hook: string;
  examples: string[];
  sentence_stem: string;
  sentence_answer: string;
}

export async function recordVocabPracticed(
  token: string,
  word: string,
  cefrLevel: string,
  pos: string,
): Promise<void> {
  await fetch(`${API_BASE}/api/v1/vocab/practiced`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ word, cefr_level: cefrLevel, pos }),
  });
}

export interface VocabListItem {
  word: string;
  cefr_level: string;
  pos: string;
  practiced_at: string;
}

export async function fetchVocabList(token: string): Promise<VocabListItem[]> {
  const res = await fetch(`${API_BASE}/api/v1/vocab/list`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Vocab list failed: ${res.status}`);
  return res.json() as Promise<VocabListItem[]>;
}

export async function fetchVocabWord(token: string, word?: string): Promise<VocabWordResponse> {
  const url = word
    ? `${API_BASE}/api/v1/vocab/next?word=${encodeURIComponent(word)}`
    : `${API_BASE}/api/v1/vocab/next`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(`${res.status}:${body.detail ?? ''}`);
  }
  return res.json() as Promise<VocabWordResponse>;
}

// ── Assessment ────────────────────────────────────────────────────────────────

export interface AssessmentQuestionResponse {
  sentence: string;
  options: string[];
  correct_index: number;
  cefr_level: string;
  explanation: string;
}

export async function fetchAssessQuestions(
  token: string
): Promise<AssessmentQuestionResponse[]> {
  const res = await fetch(`${API_BASE}/api/v1/assess/questions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Assess fetch failed: ${res.status}`);
  return res.json() as Promise<AssessmentQuestionResponse[]>;
}

export async function submitAssessResult(
  token: string,
  cefrLevel: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/assess/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ cefr_level: cefrLevel }),
  });
  if (!res.ok) throw new Error(`Assess submit failed: ${res.status}`);
}

export async function fetchWordSuggestions(query: string): Promise<string[]> {
  if (query.length < 2) return [];
  try {
    const res = await fetch(
      `https://api.datamuse.com/sug?s=${encodeURIComponent(query)}&max=7`,
    );
    if (!res.ok) return [];
    const data = await res.json() as Array<{ word: string }>;
    return data.map((d) => d.word);
  } catch {
    return [];
  }
}

