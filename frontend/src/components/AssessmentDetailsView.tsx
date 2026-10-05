import { useEffect, useState, useMemo } from "react";
import {
  Scan,
  ShieldCheck,
  Clock,
  FileText,
  ShieldAlert,
  Loader2,
  CheckCircle2,
  XCircle,
  Calendar,
} from "lucide-react";
import {
  getAssessment,
  subscribeToEvents,
  type Assessment,
  type AssessmentEvent,
} from "../../service/api";
import { ActivityFeed } from "./ActivityFeed";

const WORKFLOW_STEPS = [
  { id: "created", label: "Assessment Created" },
  { id: "scope", label: "Scope Validated" },
  { id: "planning", label: "Agent Planning" },
  { id: "plan_validated", label: "Plan Approved" },
  { id: "checks", label: "Security Checks" },
  { id: "evidence", label: "Evidence Collected" },
  { id: "analysis", label: "Findings Analyzed" },
  { id: "report", label: "Report Generated" },
  { id: "completed", label: "Assessment Completed" },
];

export interface AssessmentDetailsViewProps {
  assessmentId: string;
  onNavigateToReport: (id: string) => void;
  onNavigateToFindings: () => void;
}

export function AssessmentDetailsView({
  assessmentId,
  onNavigateToReport,
  onNavigateToFindings,
}: AssessmentDetailsViewProps) {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [events, setEvents] = useState<AssessmentEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Poll assessment metadata
  useEffect(() => {
    let active = true;
    const fetchMeta = async () => {
      try {
        const data = await getAssessment(assessmentId);
        if (active) setAssessment(data);
      } catch {
        // ignore
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchMeta();
    const interval = setInterval(fetchMeta, 3000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [assessmentId]);

  // Subscribe to live SSE events
  useEffect(() => {
    const sub = subscribeToEvents(assessmentId, (_evt, snapshot) => {
      setEvents(snapshot);
    });
    return () => sub.close();
  }, [assessmentId]);

  // Calculate workflow stage completion based on events and status
  const stepStates = useMemo(() => {
    const titles = events.map((e) => e.title.toLowerCase());
    const isFailed = assessment?.status === "failed";
    const isRejected = assessment?.status === "rejected";
    const isCompleted = assessment?.status === "completed";

    return WORKFLOW_STEPS.map((step, idx) => {
      let state: "pending" | "running" | "completed" | "failed" | "rejected" = "pending";

      if (isRejected && step.id === "scope") {
        return { ...step, state: "rejected" as const };
      }
      if (isFailed && idx === Math.min(events.length, WORKFLOW_STEPS.length - 1)) {
        return { ...step, state: "failed" as const };
      }

      if (isCompleted) {
        state = "completed";
      } else {
        if (step.id === "created" && titles.some((t) => t.includes("queued") || t.includes("started") || t.includes("created"))) {
          state = "completed";
        } else if (step.id === "scope" && titles.some((t) => t.includes("scope"))) {
          state = "completed";
        } else if (step.id === "planning" && titles.some((t) => t.includes("plan"))) {
          state = "completed";
        } else if (step.id === "plan_validated" && titles.some((t) => t.includes("approved"))) {
          state = "completed";
        } else if (step.id === "checks" && titles.some((t) => t.includes("check:"))) {
          state = titles.some((t) => t.includes("evidence")) ? "completed" : "running";
        } else if (step.id === "evidence" && titles.some((t) => t.includes("evidence"))) {
          state = "completed";
        } else if (step.id === "analysis" && titles.some((t) => t.includes("findings"))) {
          state = "completed";
        } else if (step.id === "report" && titles.some((t) => t.includes("report"))) {
          state = "completed";
        } else if (step.id === "completed" && isCompleted) {
          state = "completed";
        }
      }

      return { ...step, state };
    });
  }, [events, assessment?.status]);

  const durationStr = useMemo(() => {
    if (assessment?.started_at && assessment?.completed_at) {
      const s = new Date(assessment.started_at).getTime();
      const c = new Date(assessment.completed_at).getTime();
      const diffMs = Math.max(0, c - s);
      return `${(diffMs / 1000).toFixed(2)}s`;
    }
    return assessment?.status === "running" ? "In progress…" : "—";
  }, [assessment]);

  if (loading && !assessment) {
    return (
      <div className="p-12 text-center text-slate-400">
        <Loader2 size={24} className="animate-spin text-blue-500 mx-auto mb-3" />
        Loading assessment {assessmentId}…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded-full">
                ID: {assessment?.id}
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-xs font-semibold capitalize ${
                  assessment?.status === "completed"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : assessment?.status === "failed" || assessment?.status === "rejected"
                    ? "bg-red-500/10 text-red-400 border-red-500/30"
                    : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                }`}
              >
                {assessment?.status === "running" && (
                  <Loader2 size={12} className="animate-spin" />
                )}
                {assessment?.status}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-50 flex items-center gap-2">
              <Scan size={22} className="text-blue-500" />
              Target: <span className="font-mono text-emerald-300">{assessment?.target}</span>
            </h1>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={onNavigateToFindings}
              className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-lg font-medium transition"
            >
              <ShieldAlert size={14} className="text-amber-400" />
              View Findings
            </button>
            <button
              onClick={() => onNavigateToReport(assessmentId)}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition"
            >
              <FileText size={14} />
              Open Report
            </button>
          </div>
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          <div>
            <span className="block text-slate-500">Profile</span>
            <span className="font-medium text-slate-200 uppercase">{assessment?.profile}</span>
          </div>
          <div>
            <span className="block text-slate-500">Duration</span>
            <span className="font-medium text-slate-200 flex items-center gap-1 mt-0.5">
              <Clock size={12} /> {durationStr}
            </span>
          </div>
          <div>
            <span className="block text-slate-500">Created At</span>
            <span className="font-medium text-slate-200 flex items-center gap-1 mt-0.5">
              <Calendar size={12} />
              {assessment?.created_at ? new Date(assessment.created_at).toLocaleTimeString() : "—"}
            </span>
          </div>
          <div>
            <span className="block text-slate-500">Authorization</span>
            <span className="font-medium text-emerald-400 flex items-center gap-1 mt-0.5">
              <ShieldCheck size={12} /> Confirmed Scope
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-xs text-slate-400 leading-relaxed">
          This run is limited to the safe baseline profile: HTTP response baseline, selected defensive headers,
          and cookie attribute checks. A completed run with no findings is not a full vulnerability assessment.
        </div>
      </div>

      {/* Visual Workflow Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          LangGraph Agent Workflow Execution
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-2">
          {stepStates.map((step, idx) => {
            const isDone = step.state === "completed";
            const isCurrent = step.state === "running";
            const isErr = step.state === "failed" || step.state === "rejected";

            return (
              <div
                key={step.id}
                className={`p-3 rounded-xl border flex flex-col justify-between text-xs transition ${
                  isDone
                    ? "bg-emerald-500/5 border-emerald-500/30 text-emerald-300"
                    : isCurrent
                    ? "bg-blue-500/10 border-blue-500/50 text-blue-300 shadow-sm"
                    : isErr
                    ? "bg-red-500/10 border-red-500/30 text-red-300"
                    : "bg-slate-950/40 border-slate-800 text-slate-500"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] opacity-75">{idx + 1}</span>
                  {isDone ? (
                    <CheckCircle2 size={14} className="text-emerald-400" />
                  ) : isCurrent ? (
                    <Loader2 size={14} className="animate-spin text-blue-400" />
                  ) : isErr ? (
                    <XCircle size={14} className="text-red-400" />
                  ) : (
                    <div className="w-2.5 h-2.5 rounded-full border border-slate-700" />
                  )}
                </div>
                <span className="font-medium leading-tight">{step.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live SSE Activity Stream */}
      <section>
        <ActivityFeed assessment={assessment} />
      </section>
    </div>
  );
}

export default AssessmentDetailsView;
