import { useState } from "react";
import {
  APPROVED_TARGET,
  PERMITTED_CHECKS,
  SAFE_PROFILE,
  createAssessment,
  getHealth,
  type Assessment,
} from "../../service/api";

export interface NewAssessmentProps {
  onCreated: (assessment: Assessment) => void;
  onCancel: () => void;
}

export function NewAssessment({ onCreated, onCancel }: NewAssessmentProps) {
  const [authorized, setAuthorized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    kind: "info" | "success" | "error";
    text: string;
  } | null>(null);

  async function startAssessment() {
    if (!authorized) {
      setMessage({
        kind: "error",
        text: "Please confirm authorization.",
      });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      try {
        await getHealth();
      } catch (error) {
        const detail = error instanceof Error ? error.message : "Backend is unavailable";
        throw new Error(
          `${detail}. Start the FastAPI backend on http://127.0.0.1:8000, then try again.`
        );
      }

      const assessment = await createAssessment(
        APPROVED_TARGET,
        authorized,
        SAFE_PROFILE,
      );

      setMessage({
        kind: "success",
        text: `Assessment created: ${assessment.id}`,
      });

      // Give the user a beat to see the success banner, then hand off
      // to the parent (which will navigate / open the live activity view).
      window.setTimeout(() => onCreated(assessment), 700);
    } catch (error) {
      setMessage({
        kind: "error",
        text:
          error instanceof Error
            ? error.message
            : "Something went wrong",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm
      flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 text-slate-100
        border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold">New security assessment</h2>
            <p className="text-sm text-slate-400 mt-1">
              Launch a scoped, authorized run against the local Juice Shop lab.
            </p>
          </div>
          <button
            onClick={onCancel}
            disabled={loading}
            className="text-slate-400 hover:text-slate-200 text-sm
              px-2 py-1 rounded-md disabled:opacity-50"
            aria-label="Close">
            ✕
          </button>
        </div>

        {/* Target (readonly, approved scope) */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4
          space-y-1">
          <p className="text-xs uppercase tracking-wide text-slate-500
            font-semibold">Target</p>
          <p className="font-mono text-sm text-emerald-300 break-all">
            {APPROVED_TARGET}
          </p>
          <p className="text-sm text-slate-500">
            Local authorized training lab only. Public website scanning is disabled in this prototype.
          </p>
        </div>

        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4
          space-y-1">
          <p className="text-xs uppercase tracking-wide text-amber-300
            font-semibold">Can I test any website?</p>
          <p className="text-sm text-amber-100/80 leading-relaxed">
            Not in the current app. The backend rejects external domains on purpose so the AI cannot scan targets
            outside the approved lab. A company version would add an allowlist, approvals, audit logs, and legal
            ownership checks before enabling real assets.
          </p>
        </div>

        {/* Permitted safe checks */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4
          space-y-2">
          <p className="text-xs uppercase tracking-wide text-slate-500
            font-semibold">Permitted safe checks ({SAFE_PROFILE})</p>
          <ul className="text-sm text-slate-300 space-y-1.5">
            {PERMITTED_CHECKS.map((c: string) => (
              <li key={c} className="flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-500 leading-relaxed pt-1">
            If these checks produce 0 findings, it only means these three passive checks did not flag anything.
            It does not mean Juice Shop or any real app has no vulnerabilities.
          </p>
        </div>

        {/* Authorization checkbox */}
        <label className="flex items-start gap-3 cursor-pointer select-none
          p-3 rounded-lg hover:bg-slate-800/50 transition">
          <input
            type="checkbox"
            checked={authorized}
            onChange={(e) => setAuthorized(e.target.checked)}
            className="mt-1 h-4 w-4 accent-blue-600"
          />
          <span className="text-sm">
            I confirm that this assessment is <b>authorized</b> and
            within the configured lab scope.
          </span>
        </label>

        {/* Action row */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2.5 rounded-lg text-sm text-slate-300
              border border-slate-700 hover:bg-slate-800 disabled:opacity-50">
            Cancel
          </button>
          <button
            type="button"
            disabled={!authorized || loading}
            onClick={startAssessment}
            className="rounded-lg bg-blue-600 hover:bg-blue-500 px-5 py-2.5
              text-sm font-medium text-white disabled:opacity-50
              disabled:cursor-not-allowed transition min-w-[160px]">
            {loading ? "Creating…" : "Start assessment"}
          </button>
        </div>

        {/* Status message */}
        {message && (
          <p
            role="status"
            className={[
              "text-sm rounded-lg p-3 border",
              message.kind === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : message.kind === "error"
                  ? "bg-red-500/10 border-red-500/30 text-red-300"
                  : "bg-slate-500/10 border-slate-500/30 text-slate-300",
            ].join(" ")}>
            {message.text}
          </p>
        )}
      </div>
    </div>
  );
}

export default NewAssessment;
