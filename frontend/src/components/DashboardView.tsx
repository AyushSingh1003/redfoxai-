import { useMemo } from "react";
import {
  Scan,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Plus,
  Sparkles,
  BarChart3,
  Loader2,
  Lock,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { Assessment, Finding } from "../../service/api";
import { AssessmentList } from "./AssessmentList";
import { ActivityFeed } from "./ActivityFeed";

const SEVERITY_COLORS: Record<string, string> = {
  High: "#f87171", // red-400
  Medium: "#fbbf24", // amber-400
  Low: "#60a5fa", // blue-400
  Informational: "#94a3b8", // slate-400
};

export interface DashboardViewProps {
  assessments: Assessment[];
  findings: Finding[];
  selectedAssessmentId: string | null;
  onSelectAssessment: (id: string) => void;
  onOpenNewModal: () => void;
  onSeedDemo: () => void;
  onNavigateToReport: (id: string) => void;
  loading: boolean;
  seeding: boolean;
}

export function DashboardView({
  assessments,
  findings,
  selectedAssessmentId,
  onSelectAssessment,
  onOpenNewModal,
  onSeedDemo,
  onNavigateToReport,
  loading,
  seeding,
}: DashboardViewProps) {
  const selectedAssessment = useMemo(
    () => assessments.find((a) => a.id === selectedAssessmentId) ?? null,
    [assessments, selectedAssessmentId]
  );

  // Compute stats from real backend data
  const stats = useMemo(() => {
    const total = assessments.length;
    const completed = assessments.filter((a) => a.status === "completed").length;
    const verifiedFindings = findings.filter(
      (f) => f.verification_status === "verified"
    ).length;
    const highRisk = findings.filter(
      (f) => f.severity === "High" || f.severity === "Medium"
    ).length;

    return [
      { label: "Total Assessments", value: total, icon: Scan, color: "text-blue-400" },
      { label: "Completed Runs", value: completed, icon: ShieldCheck, color: "text-emerald-400" },
      { label: "Verified Findings", value: verifiedFindings, icon: ShieldAlert, color: "text-indigo-400" },
      { label: "High / Medium Risks", value: highRisk, icon: AlertTriangle, color: "text-amber-400" },
    ];
  }, [assessments, findings]);

  // Compute chart data for findings distribution
  const chartData = useMemo(() => {
    const counts: Record<string, number> = {
      High: 0,
      Medium: 0,
      Low: 0,
      Informational: 0,
    };
    for (const f of findings) {
      if (counts[f.severity] !== undefined) {
        counts[f.severity]++;
      } else {
        counts["Informational"]++;
      }
    }
    return [
      { name: "High", count: counts.High, fill: SEVERITY_COLORS.High },
      { name: "Medium", count: counts.Medium, fill: SEVERITY_COLORS.Medium },
      { name: "Low", count: counts.Low, fill: SEVERITY_COLORS.Low },
      { name: "Info", count: counts.Informational, fill: SEVERITY_COLORS.Informational },
    ];
  }, [findings]);

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Security Assessment Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">
            Local-lab security automation for OWASP Juice Shop. External website scanning is disabled by policy.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onSeedDemo}
            disabled={seeding}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg px-3.5 py-2.5 text-xs font-medium transition disabled:opacity-50 border border-slate-700"
            title="Seeds clearly labeled [DEMO DATA] records to demonstrate reporting"
          >
            {seeding ? (
              <Loader2 size={14} className="animate-spin text-blue-400" />
            ) : (
              <Sparkles size={14} className="text-amber-400" />
            )}
            {seeding ? "Seeding…" : "Seed Demo Data"}
          </button>

          <button
            type="button"
            onClick={onOpenNewModal}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2.5 text-xs font-semibold shadow-sm transition"
          >
            <Plus size={16} />
            New Assessment
          </button>
        </div>
      </div>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Lock size={16} className="text-emerald-400" />
            <span>What This Platform Does Today</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            REDFOX AI runs a safe, authorized assessment against the configured local training target only:
            <span className="font-mono text-emerald-300"> http://juice-shop:3000</span>. It demonstrates how an
            AI-assisted security workflow can plan, execute deterministic checks, collect evidence, and produce a
            report without letting the AI choose arbitrary targets or tools.
          </p>
        </div>

        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 space-y-2">
          <h2 className="text-sm font-semibold text-amber-300">Why 0 Findings Can Happen</h2>
          <p className="text-sm text-amber-100/80 leading-relaxed">
            Zero means none of the current passive checks produced findings. It is not a full vulnerability scan,
            authenticated pentest, or proof that the target has no security issues.
          </p>
        </div>
      </section>

      {/* Summary KPI Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm"
            >
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium text-slate-400">{stat.label}</span>
                <Icon size={18} className={stat.color} />
              </div>
              <p className="text-3xl font-bold mt-3 text-slate-100">{stat.value}</p>
            </div>
          );
        })}
      </section>

      {/* Mid Section: Findings Distribution Chart + Recent Assessment Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <BarChart3 size={16} className="text-blue-400" />
              <span>Findings Distribution</span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Total: {findings.length}
            </span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#020617",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  cursor={{ fill: "rgba(51, 65, 85, 0.2)" }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-4 gap-1 text-[11px] text-center pt-2 border-t border-slate-800">
            {chartData.map((d) => (
              <span key={d.name} className="text-slate-400">
                {d.name}: <b className="text-slate-200">{d.count}</b>
              </span>
            ))}
          </div>
        </div>

        {/* Live Activity Column */}
        <div className="lg:col-span-2">
          <ActivityFeed assessment={selectedAssessment} />
        </div>
      </div>

      {/* Recent Assessments Table */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Recent Security Assessments
          </h2>
          {selectedAssessment && (
            <button
              onClick={() => onNavigateToReport(selectedAssessment.id)}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              Inspect Selected Report →
            </button>
          )}
        </div>
        <AssessmentList
          assessments={assessments}
          selectedId={selectedAssessmentId}
          onSelect={onSelectAssessment}
          loading={loading}
        />
      </section>
    </div>
  );
}

export default DashboardView;
