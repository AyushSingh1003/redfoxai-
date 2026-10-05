// API Service for REDFOX AI
const BASE = "";

export const APPROVED_TARGET = "http://juice-shop:3000";
export const SAFE_PROFILE = "safe_baseline";

export const PERMITTED_CHECKS: string[] = [
  "HTTP/S status / response timing / size limit baseline",
  "Presence of defensive security response headers (CSP, HSTS, X-Content-Type-Options, etc.)",
  "Cookie defensive security attributes (Secure, HttpOnly, SameSite)",
];

export interface Assessment {
  id: string;
  target: string;
  profile: string;
  status: string;
  authorized: boolean;
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
  plan?: string[] | null;
}

export interface AssessmentEvent {
  id: string;
  assessment_id: string;
  occurred_at: string;
  kind: "info" | "success" | "error" | "node";
  title: string;
  detail?: string | null;
  order: number;
}

export interface Finding {
  id: string;
  assessment_id: string;
  title: string;
  category: string;
  severity: "Informational" | "Low" | "Medium" | "High";
  confidence: string;
  description: string;
  evidence_reference?: string | null;
  evidence_snapshot?: Record<string, any> | null;
  why_it_matters?: string | null;
  remediation?: string | null;
  verification_status: string;
  created_at?: string | null;
}

export interface AssessmentReport {
  assessment_id: string;
  target: string;
  profile: string;
  status: string;
  created_at?: string | null;
  completed_at?: string | null;
  executive_summary: string;
  timeline: Array<{
    order: number;
    title: string;
    detail?: string | null;
    kind: string;
    timestamp?: string | null;
  }>;
  checks_executed: Array<{
    tool_name: string;
    status: string;
    duration_ms: number;
    error?: string | null;
  }>;
  findings_distribution: Record<string, number>;
  findings: Finding[];
  remediation_recommendations: Array<{
    title: string;
    severity: string;
    remediation: string;
  }>;
  agent_evaluation_summary: Record<string, any>;
  limitations: string[];
  disclaimer: string;
}

export interface SystemSettings {
  app_name: string;
  app_subtitle: string;
  app_env: string;
  lab_target: string;
  agent_version: string;
  allowed_tools: Array<{
    name: string;
    description: string;
    timeout_seconds: number;
  }>;
  llm_provider: string;
  llm_model: string;
  llm_available: boolean;
}

export interface EvaluationTestCase {
  case_name: string;
  description: string;
  passed: boolean;
  expected: string;
  actual: string;
  latency_ms: number;
  notes?: string | null;
}

export interface EvaluationResult {
  id: string;
  run_at: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  scope_compliance_rate: number;
  plan_validity_rate: number;
  evidence_fidelity_rate: number;
  avg_latency_ms: number;
  cases: EvaluationTestCase[];
}

async function readErrorDetail(res: Response, fallback: string): Promise<string> {
  const statusPrefix = `${fallback} (HTTP ${res.status})`;
  const contentType = res.headers.get("content-type") || "";

  try {
    if (contentType.includes("application/json")) {
      const body = await res.json();
      if (body?.detail) return String(body.detail);
      if (body?.message) return String(body.message);
      return statusPrefix;
    }

    const text = (await res.text()).trim();
    if (text) {
      const firstLine = text.split("\n").find(Boolean) || text;
      return `${statusPrefix}: ${firstLine.slice(0, 240)}`;
    }
  } catch {
    // fall through to fallback
  }

  return statusPrefix;
}

export async function getHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(await readErrorDetail(res, "Backend is unavailable"));
  return res.json();
}

export async function getSettings(): Promise<SystemSettings> {
  const res = await fetch(`${BASE}/api/settings`);
  if (!res.ok) throw new Error("Unable to fetch settings");
  return res.json();
}

export async function getAssessments(): Promise<Assessment[]> {
  const res = await fetch(`${BASE}/api/assessments`);
  if (!res.ok) throw new Error("Unable to load assessments");
  return res.json();
}

export async function getAssessment(id: string): Promise<Assessment> {
  const res = await fetch(`${BASE}/api/assessments/${id}`);
  if (!res.ok) throw new Error(`Unable to load assessment ${id}`);
  return res.json();
}

export async function createAssessment(
  target: string,
  authorized: boolean,
  profile: string = SAFE_PROFILE,
): Promise<Assessment> {
  const res = await fetch(`${BASE}/api/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, profile, authorized }),
  });

  if (!res.ok) {
    throw new Error(await readErrorDetail(res, "Assessment creation failed"));
  }

  return res.json();
}

export async function getEvents(assessmentId: string): Promise<AssessmentEvent[]> {
  const res = await fetch(`${BASE}/api/assessments/${assessmentId}/events`);
  if (!res.ok) throw new Error(`Unable to load events for ${assessmentId}`);
  return res.json();
}

export async function getFindings(filters?: {
  severity?: string;
  assessment_id?: string;
  category?: string;
}): Promise<Finding[]> {
  const params = new URLSearchParams();
  if (filters?.severity) params.append("severity", filters.severity);
  if (filters?.assessment_id) params.append("assessment_id", filters.assessment_id);
  if (filters?.category) params.append("category", filters.category);

  const query = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${BASE}/api/findings${query}`);
  if (!res.ok) throw new Error("Unable to load findings");
  return res.json();
}

export async function getFinding(id: string): Promise<Finding> {
  const res = await fetch(`${BASE}/api/findings/${id}`);
  if (!res.ok) throw new Error(`Unable to load finding ${id}`);
  return res.json();
}

export async function getReport(assessmentId: string): Promise<AssessmentReport> {
  const res = await fetch(`${BASE}/api/reports/${assessmentId}`);
  if (!res.ok) throw new Error(`Unable to load report for ${assessmentId}`);
  return res.json();
}

export async function runEvaluation(): Promise<EvaluationResult> {
  const res = await fetch(`${BASE}/api/evaluation/run`, { method: "POST" });
  if (!res.ok) throw new Error("Evaluation suite run failed");
  return res.json();
}

export async function getLatestEvaluation(): Promise<EvaluationResult> {
  const res = await fetch(`${BASE}/api/evaluation/latest`);
  if (!res.ok) throw new Error("Unable to load evaluation metrics");
  return res.json();
}

export async function seedDemoData(): Promise<Assessment> {
  const res = await fetch(`${BASE}/api/demo/seed`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to seed demo data");
  return res.json();
}

export type EventsListener = (
  event: AssessmentEvent,
  snapshot: AssessmentEvent[],
) => void;

export interface EventsSubscription {
  close: () => void;
}

export function subscribeToEvents(
  assessmentId: string,
  listener: EventsListener,
): EventsSubscription {
  const snapshot: AssessmentEvent[] = [];
  let closed = false;
  let es: EventSource | null = null;

  const push = (evt: AssessmentEvent) => {
    snapshot.push(evt);
    snapshot.sort((a, b) => a.order - b.order);
    listener(evt, [...snapshot]);
  };

  // 1. Replay historical events
  getEvents(assessmentId)
    .then((existing) => {
      if (closed) return;
      existing.forEach(push);
      if (closed) return;

      // 2. Stream live SSE events
      es = new EventSource(`${BASE}/api/assessments/${assessmentId}/stream`);

      es.addEventListener("event", (ev: MessageEvent<string>) => {
        try {
          const parsed = JSON.parse(ev.data) as AssessmentEvent;
          push(parsed);
        } catch {
          // ignore
        }
      });

      es.addEventListener("done", () => {
        es?.close();
      });

      es.onerror = () => {
        // SSE reconnects automatically
      };
    })
    .catch(() => {
      // ignore initial hydrate error
    });

  return {
    close() {
      closed = true;
      es?.close();
      es = null;
    },
  };
}
