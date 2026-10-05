import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Info,
  CircleDot,
  RefreshCw,
  Link as LinkIcon,
} from "lucide-react";
import {
  subscribeToEvents,
  type Assessment,
  type AssessmentEvent,
} from "../../service/api";

const KIND_STYLES: Record<
  AssessmentEvent["kind"],
  { icon: typeof Info; dot: string; text: string }
> = {
  info: {
    icon: Info,
    dot: "bg-slate-400",
    text: "text-slate-300",
  },
  success: {
    icon: CheckCircle2,
    dot: "bg-emerald-400",
    text: "text-emerald-300",
  },
  error: {
    icon: AlertTriangle,
    dot: "bg-red-400",
    text: "text-red-300",
  },
  node: {
    icon: CircleDot,
    dot: "bg-blue-400",
    text: "text-blue-300",
  },
};

export interface ActivityFeedProps {
  assessment: Assessment | null;
}

export function ActivityFeed({ assessment }: ActivityFeedProps) {
  const [events, setEvents] = useState<AssessmentEvent[]>([]);
  const [live, setLive] = useState(false);
  const sub = useRef<{ close: () => void } | null>(null);

  useEffect(() => {
    // Reset for newly selected assessment
    setEvents([]);
    setLive(false);
    sub.current?.close();
    sub.current = null;

    if (!assessment) return;

    setLive(true);
    sub.current = subscribeToEvents(assessment.id, (_evt: AssessmentEvent, snap: AssessmentEvent[]) => {
      setEvents(snap);
    });

    return () => {
      sub.current?.close();
      sub.current = null;
    };
  }, [assessment?.id]);

  const summary = useMemo(() => {
    const total = events.length;
    const successes = events.filter((e) => e.kind === "success").length;
    const errors = events.filter((e) => e.kind === "error").length;
    return { total, successes, errors };
  }, [events]);

  if (!assessment) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={18} className="text-blue-400" />
          <h2 className="font-semibold">Agent activity</h2>
        </div>
        <p className="text-sm text-slate-400">
          Select an assessment to see its live event timeline.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900">
      <header className="flex items-center justify-between p-5 pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity size={18} className="text-blue-400" />
            <h2 className="font-semibold">Agent activity</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <LinkIcon size={12} />
            <span className="font-mono">{assessment.id.slice(0, 12)}…</span>
            <span className="mx-1">·</span>
            <span
              className={[
                "inline-flex items-center gap-1",
                live ? "text-emerald-400" : "text-slate-400",
              ].join(" ")}>
              {live ? (
                <>
                  <RefreshCw size={12} className="animate-spin" />
                  live SSE
                </>
              ) : (
                <>static</>
              )}
            </span>
          </div>
        </div>
        <div className="flex gap-4 text-xs text-slate-400">
          <span>
            <b className="text-slate-200">{summary.total}</b> events
          </span>
          <span className="text-emerald-400">
            {summary.successes} ok
          </span>
          {summary.errors > 0 && (
            <span className="text-red-400">{summary.errors} err</span>
          )}
        </div>
      </header>

      <div className="px-5 pb-5 pt-2">
        {events.length === 0 ? (
          <div
            className="rounded-lg border border-dashed border-slate-700
              p-8 text-center text-sm text-slate-400">
            Waiting for assessment events…
          </div>
        ) : (
          <ol className="relative pl-6 border-l border-slate-800 space-y-3">
            {events.map((ev) => {
              const style = KIND_STYLES[ev.kind] ?? KIND_STYLES.info;
              const Icon = style.icon;
              const ts = new Date(ev.occurred_at).toLocaleTimeString();
              return (
                <li key={`${ev.id}-${ev.order}`} className="relative">
                  <span
                    className={[
                      "absolute -left-[33px] top-1 w-4 h-4 rounded-full",
                      "flex items-center justify-center text-white",
                      style.dot,
                    ].join(" ")}>
                    <Icon size={10} />
                  </span>
                  <div className="text-xs text-slate-500">{ts}</div>
                  <div className={`text-sm font-medium ${style.text}`}>
                    {ev.title}
                  </div>
                  {ev.detail && (
                    <div className="text-xs text-slate-400 mt-0.5
                      whitespace-pre-wrap break-words">
                      {ev.detail}
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </div>
  );
}

export default ActivityFeed;
