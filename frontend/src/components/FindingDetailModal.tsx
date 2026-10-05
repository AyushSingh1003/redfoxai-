import { useState } from "react";
import {
  ShieldCheck,
  Cpu,
  FileCode,
  Copy,
  Check,
  X,
  AlertTriangle,
} from "lucide-react";
import type { Finding } from "../../service/api";

const SEVERITY_COLORS = {
  High: "bg-red-500/10 text-red-400 border-red-500/30",
  Medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  Low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  Informational: "bg-slate-500/10 text-slate-400 border-slate-500/30",
};

export interface FindingDetailModalProps {
  finding: Finding | null;
  onClose: () => void;
}

export function FindingDetailModal({ finding, onClose }: FindingDetailModalProps) {
  const [copied, setCopied] = useState(false);

  if (!finding) return null;

  const copyEvidence = () => {
    if (finding.evidence_snapshot) {
      navigator.clipboard.writeText(JSON.stringify(finding.evidence_snapshot, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 text-slate-100">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span
                className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold ${
                  SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.Informational
                }`}
              >
                {finding.severity}
              </span>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-mono">
                {finding.category}
              </span>
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                <ShieldCheck size={12} /> {finding.verification_status}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-50">{finding.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 p-1.5 rounded-lg hover:bg-slate-800 transition"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Verified Observation */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>Verified Observation (Deterministic Fact)</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed font-mono text-xs bg-slate-900/80 p-3 rounded-lg border border-slate-800/80">
            {finding.description}
          </p>
        </div>

        {/* Structured Raw Evidence */}
        {finding.evidence_snapshot && (
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <FileCode size={14} className="text-blue-400" />
                <span>Supporting Structured Evidence (JSON)</span>
              </div>
              <button
                onClick={copyEvidence}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 px-2.5 py-1 rounded-md transition"
              >
                {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                {copied ? "Copied" : "Copy JSON"}
              </button>
            </div>
            <pre className="text-xs font-mono text-slate-300 bg-slate-900/90 p-3 rounded-lg border border-slate-800/80 overflow-x-auto max-h-48">
              {JSON.stringify(finding.evidence_snapshot, null, 2)}
            </pre>
          </div>
        )}

        {/* AI-Generated Analysis (Why It Matters) */}
        {finding.why_it_matters && (
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400">
              <Cpu size={14} />
              <span>Analysis & Risk Context (Grounded in Evidence)</span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {finding.why_it_matters}
            </p>
          </div>
        )}

        {/* Remediation Guidance */}
        {finding.remediation && (
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
              <AlertTriangle size={14} />
              <span>Remediation Guidance</span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {finding.remediation}
            </p>
          </div>
        )}

        {/* Footer info */}
        <div className="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800">
          <span>Assessment: <span className="font-mono text-slate-400">{finding.assessment_id.slice(0, 8)}…</span></span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default FindingDetailModal;
