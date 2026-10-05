import { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Play,
  RotateCw,
  Info,
  Check,
} from "lucide-react";
import {
  runEvaluation,
  getLatestEvaluation,
  type EvaluationResult,
} from "../../service/api";

export function EvaluationView() {
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadLatest = async () => {
    setLoading(true);
    try {
      const data = await getLatestEvaluation();
      setEvaluation(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLatest();
  }, []);

  const handleRunSuite = async () => {
    setRunning(true);
    setFeedback(null);
    try {
      const res = await runEvaluation();
      setEvaluation(res);
      setFeedback("Evaluation suite finished successfully.");
      setTimeout(() => setFeedback(null), 3000);
    } catch (err) {
      setFeedback("Failed to run evaluation suite.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="text-blue-500" size={24} />
            Agent Evaluation & Reliability Framework
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated reliability test cases assessing scope compliance, tool policy, resilience, and injection resistance.
          </p>
        </div>

        <button
          onClick={handleRunSuite}
          disabled={running}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition disabled:opacity-50"
        >
          {running ? (
            <RotateCw size={16} className="animate-spin" />
          ) : (
            <Play size={16} />
          )}
          {running ? "Running Test Cases…" : "Run Evaluation Suite"}
        </button>
      </div>

      {feedback && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs px-4 py-2.5 rounded-xl flex items-center gap-2">
          <Check size={14} />
          {feedback}
        </div>
      )}

      {/* Metric Cards */}
      {evaluation && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 block mb-1">Total Test Cases</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100">{evaluation.total_cases}</span>
              <span className="text-xs text-emerald-400 font-medium">({evaluation.passed_cases} passed)</span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 block mb-1">Scope Compliance</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-400">
                {(evaluation.scope_compliance_rate * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-slate-500">fail-closed</span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 block mb-1">Plan & Tool Validity</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-blue-400">
                {(evaluation.plan_validity_rate * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-slate-500">registry bound</span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 block mb-1">Avg Execution Latency</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100">
                {evaluation.avg_latency_ms.toFixed(1)}
              </span>
              <span className="text-xs text-slate-500">ms/test</span>
            </div>
          </div>
        </div>
      )}

      {/* Test Cases Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">
            Deterministic Evaluation Suite (6 Cases)
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            Last run: {evaluation?.run_at ? new Date(evaluation.run_at).toLocaleTimeString() : "—"}
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-sm text-slate-400">
            <RotateCw size={24} className="animate-spin text-blue-500 mx-auto mb-3" />
            Loading evaluation cases…
          </div>
        ) : !evaluation || evaluation.cases.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-400">
            No evaluation records yet. Click "Run Evaluation Suite" to run the test cases.
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="bg-slate-950/40 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="text-left p-3.5 px-4 font-medium">Test Case</th>
                <th className="text-left p-3.5 px-4 font-medium">Expected Behavior</th>
                <th className="text-left p-3.5 px-4 font-medium">Actual Outcome</th>
                <th className="text-center p-3.5 px-4 font-medium">Latency</th>
                <th className="text-right p-3.5 px-4 font-medium">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {evaluation.cases.map((c, i) => (
                <tr key={i} className="hover:bg-slate-800/30 transition">
                  <td className="p-3.5 px-4">
                    <span className="font-semibold text-slate-200 block">{c.case_name}</span>
                    <span className="text-[11px] text-slate-500 block mt-0.5">{c.description}</span>
                  </td>
                  <td className="p-3.5 px-4 text-slate-300 font-mono text-[11px] max-w-xs">
                    {c.expected}
                  </td>
                  <td className="p-3.5 px-4 text-slate-400 font-mono text-[11px] max-w-xs">
                    {c.actual}
                  </td>
                  <td className="p-3.5 px-4 text-center font-mono text-slate-400 whitespace-nowrap">
                    {c.latency_ms.toFixed(1)} ms
                  </td>
                  <td className="p-3.5 px-4 text-right whitespace-nowrap">
                    {c.passed ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                        <CheckCircle2 size={12} /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full font-medium">
                        <XCircle size={12} /> Failed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Evaluation Methodology Note */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 font-semibold text-slate-300">
          <Info size={14} className="text-blue-400" />
          <span>Evaluation Methodology Note</span>
        </div>
        <p className="leading-relaxed">
          <b>Evaluation set: 6 deterministic test cases.</b> This suite evaluates the safety guardrails, SSRF isolation, tool policy validation, evidence parsing fidelity, and prompt-injection resistance of the agent. It is designed to verify that the agent cannot execute arbitrary tools or scan unauthorized targets under adversarial conditions.
        </p>
      </div>
    </div>
  );
}

export default EvaluationView;
