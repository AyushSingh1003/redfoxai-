import { Scan, ShieldCheck, AlertCircle, Loader2 } from "lucide-react";
import type { Assessment } from "../../service/api";

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-slate-500/10 text-slate-300 border-slate-500/30",
  running: "bg-blue-500/10 text-blue-300 border-blue-500/30",
  completed: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  rejected: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  failed: "bg-red-500/10 text-red-300 border-red-500/30",
};

function StatusPill({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] ?? STATUS_STYLES.queued;
  const Icon =
    status === "completed"
      ? ShieldCheck
      : status === "failed" || status === "rejected"
        ? AlertCircle
        : status === "queued" || status === "running"
          ? Loader2
          : Scan;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
        border text-xs font-medium ${cls}`}>
      <Icon
        size={12}
        className={status === "running" ? "animate-spin" : ""}
      />
      <span className="capitalize">{status}</span>
    </span>
  );
}

export interface AssessmentListProps {
  assessments: Assessment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading: boolean;
}

export function AssessmentList({
  assessments,
  selectedId,
  onSelect,
  loading,
}: AssessmentListProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-dashed border-slate-700
        p-10 text-center text-sm text-slate-400">
        Loading assessments…
      </div>
    );
  }

  if (assessments.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-700
        p-10 text-center text-sm text-slate-400">
        No assessments yet. Create your first assessment to get started.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800">
      <table className="w-full text-sm">
        <thead className="bg-slate-950/50 text-slate-400">
          <tr>
            <th className="text-left font-medium p-3 px-4">ID</th>
            <th className="text-left font-medium p-3 px-4">Target</th>
            <th className="text-left font-medium p-3 px-4">Profile</th>
            <th className="text-left font-medium p-3 px-4">Created</th>
            <th className="text-left font-medium p-3 px-4">Status</th>
          </tr>
        </thead>
        <tbody>
          {assessments.map((a) => {
            const active = a.id === selectedId;
            return (
              <tr
                key={a.id}
                onClick={() => onSelect(a.id)}
                className={[
                  "border-t border-slate-800 cursor-pointer transition",
                  active
                    ? "bg-blue-600/10 hover:bg-blue-600/15"
                    : "hover:bg-slate-900/80",
                ].join(" ")}>
                <td className="p-3 px-4 font-mono text-xs text-slate-300">
                  {a.id.slice(0, 8)}…
                </td>
                <td className="p-3 px-4 font-mono text-xs text-slate-400
                  max-w-[240px] truncate">
                  {a.target}
                </td>
                <td className="p-3 px-4 text-slate-300">{a.profile}</td>
                <td className="p-3 px-4 text-slate-400 whitespace-nowrap">
                  {a.created_at
                    ? new Date(a.created_at).toLocaleString()
                    : "—"}
                </td>
                <td className="p-3 px-4">
                  <StatusPill status={a.status} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default AssessmentList;
