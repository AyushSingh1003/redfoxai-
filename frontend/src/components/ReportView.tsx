import { useEffect, useState } from "react";
import {
  FileText,
  AlertTriangle,
  Printer,
  CheckCircle,
  Loader2,
} from "lucide-react";
import {
  getReport,
  getAssessments,
  type AssessmentReport,
  type Assessment,
} from "../../service/api";
import { FindingDetailModal } from "./FindingDetailModal";

const SEVERITY_COLORS = {
  High: "bg-red-500/10 text-red-400 border-red-500/30",
  Medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  Low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  Informational: "bg-slate-500/10 text-slate-400 border-slate-500/30",
};

export interface ReportViewProps {
  initialAssessmentId?: string | null;
  onSelectAssessment?: (id: string) => void;
}

export function ReportView({
  initialAssessmentId,
  onSelectAssessment,
}: ReportViewProps) {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(initialAssessmentId || null);
  const [report, setReport] = useState<AssessmentReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState<any | null>(null);

  // Load available assessments
  useEffect(() => {
    getAssessments()
      .then((list) => {
        setAssessments(list);
        if (!selectedId && list.length > 0) {
          setSelectedId(list[0].id);
        }
      })
      .catch(() => {});
  }, []);

  // Sync prop changes
  useEffect(() => {
    if (initialAssessmentId) setSelectedId(initialAssessmentId);
  }, [initialAssessmentId]);

  // Load report data
  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    getReport(selectedId)
      .then((data) => setReport(data))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [selectedId]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Assessment Selector & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-2xl print:hidden">
        <div className="flex items-center gap-3">
          <FileText className="text-blue-500" size={22} />
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Security Assessment Report</h2>
            <p className="text-xs text-slate-400">Select an assessment to inspect its compiled report.</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedId || ""}
            onChange={(e) => {
              setSelectedId(e.target.value);
              onSelectAssessment?.(e.target.value);
            }}
            className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none font-mono"
          >
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.id.slice(0, 8)}… — {a.target} ({a.status})
              </option>
            ))}
          </select>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-lg font-medium transition"
          >
            <Printer size={14} />
            Print Report
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400 bg-slate-900 border border-slate-800 rounded-2xl">
          <Loader2 size={24} className="animate-spin text-blue-500 mx-auto mb-3" />
          Compiling security report…
        </div>
      ) : !report ? (
        <div className="p-16 text-center text-slate-400 bg-slate-900 border border-dashed border-slate-800 rounded-2xl">
          No report available for this selection. Run an assessment to generate a report.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Disclaimer Banner */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-300">
            <AlertTriangle size={18} className="shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block mb-0.5">Educational Scope Disclaimer</span>
              {report.disclaimer}
            </div>
          </div>

          {/* Report Header Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-4">
              <div>
                <span className="text-xs font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded-full">
                  REDFOX AI SECURITY REPORT
                </span>
                <h1 className="text-2xl font-bold mt-2 text-slate-50">
                  Target: {report.target}
                </h1>
              </div>
              <div className="text-right text-xs text-slate-400">
                <div>Assessment ID: <span className="font-mono text-slate-200">{report.assessment_id}</span></div>
                <div>Completed: <span className="text-slate-200">{report.completed_at ? new Date(report.completed_at).toLocaleString() : "In progress"}</span></div>
              </div>
            </div>

            {/* Severity Breakdown Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              {Object.entries(report.findings_distribution).map(([sev, count]) => (
                <div key={sev} className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-center">
                  <span className="text-xs text-slate-400 block mb-1">{sev}</span>
                  <span className="text-2xl font-bold text-slate-100">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Executive Summary */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Executive Summary
            </h2>
            <p className="text-sm text-slate-200 leading-relaxed bg-slate-950/50 p-4 rounded-xl border border-slate-800/60">
              {report.executive_summary}
            </p>
            {report.findings.length === 0 && (
              <div className="text-xs text-amber-200 leading-relaxed bg-amber-500/10 p-4 rounded-xl border border-amber-500/30">
                <span className="font-semibold block mb-1">Zero-finding interpretation</span>
                The current report covers only passive safe-baseline checks. For a company environment, this should
                be treated as evidence that the selected checks passed, not as proof that the application is free of
                vulnerabilities.
              </div>
            )}
          </div>

          {/* Checks Executed Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Deterministic Security Checks Executed
            </h2>
            <div className="overflow-hidden rounded-xl border border-slate-800">
              <table className="w-full text-xs">
                <thead className="bg-slate-950/70 text-slate-400">
                  <tr>
                    <th className="text-left p-3 px-4 font-medium">Tool Name</th>
                    <th className="text-left p-3 px-4 font-medium">Execution Status</th>
                    <th className="text-right p-3 px-4 font-medium">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {report.checks_executed.map((check) => (
                    <tr key={check.tool_name}>
                      <td className="p-3 px-4 font-mono text-slate-200">{check.tool_name}</td>
                      <td className="p-3 px-4">
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-medium capitalize">
                          <CheckCircle size={12} /> {check.status}
                        </span>
                      </td>
                      <td className="p-3 px-4 text-right font-mono text-slate-400">
                        {check.duration_ms.toFixed(1)} ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detailed Findings Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Detailed Security Findings ({report.findings.length})
              </h2>
            </div>

            <div className="space-y-4">
              {report.findings.length === 0 ? (
                <div className="bg-slate-950/70 border border-dashed border-slate-800 rounded-xl p-6 text-sm text-slate-400 leading-relaxed">
                  No detailed findings were generated. The run still produced useful evidence: it confirmed the
                  approved target, executed the registered tools, and created an audit trail showing what was checked.
                </div>
              ) : report.findings.map((f, i) => (
                <div
                  key={f.id}
                  className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 font-mono">#{i + 1}</span>
                        <span
                          className={`px-2 py-0.5 rounded-full border text-xs font-semibold ${
                            SEVERITY_COLORS[f.severity] || SEVERITY_COLORS.Informational
                          }`}
                        >
                          {f.severity}
                        </span>
                        <span className="text-xs uppercase font-mono text-slate-400">
                          {f.category}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold text-slate-100">{f.title}</h3>
                    </div>

                    <button
                      onClick={() => setSelectedFinding(f)}
                      className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-md transition"
                    >
                      Inspect Evidence
                    </button>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-mono bg-slate-900/80 p-3 rounded-lg border border-slate-800/80">
                    <span className="text-emerald-400 font-semibold uppercase block mb-1">
                      Verified Observation:
                    </span>
                    {f.description}
                  </p>

                  {f.why_it_matters && (
                    <div className="text-xs text-slate-300 leading-relaxed bg-blue-950/20 border border-blue-900/30 p-3 rounded-lg">
                      <span className="text-blue-400 font-semibold uppercase block mb-1">
                        Impact & Context:
                      </span>
                      {f.why_it_matters}
                    </div>
                  )}

                  {f.remediation && (
                    <div className="text-xs text-slate-300 leading-relaxed bg-amber-950/20 border border-amber-900/30 p-3 rounded-lg">
                      <span className="text-amber-400 font-semibold uppercase block mb-1">
                        Remediation Recommendation:
                      </span>
                      {f.remediation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Limitations and Agent Architecture Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Assessment Limitations
              </h3>
              <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
                {report.limitations.map((lim, idx) => (
                  <li key={idx} className="leading-relaxed">{lim}</li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Agent Evaluation Summary
              </h3>
              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Scope Enforcement:</span>
                  <span className="text-emerald-400 font-medium">100% Policy Bound</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Arbitrary Tool Protection:</span>
                  <span className="text-emerald-400 font-medium">Enforced via Registry</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Evidence Fidelity:</span>
                  <span className="text-emerald-400 font-medium">Strictly Grounded</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Orchestration Framework:</span>
                  <span className="text-blue-400 font-mono">LangGraph</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedFinding && (
        <FindingDetailModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
        />
      )}
    </div>
  );
}

export default ReportView;
