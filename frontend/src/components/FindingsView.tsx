import { useEffect, useState, useMemo } from "react";
import {
  ShieldAlert,
  Search,
  Eye,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { getFindings, type Finding } from "../../service/api";
import { FindingDetailModal } from "./FindingDetailModal";

const SEVERITY_BADGES = {
  High: "bg-red-500/10 text-red-400 border-red-500/30",
  Medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  Low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  Informational: "bg-slate-500/10 text-slate-400 border-slate-500/30",
};

export function FindingsView() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const data = await getFindings();
      setFindings(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      const matchesSeverity =
        severityFilter === "All" || f.severity.toLowerCase() === severityFilter.toLowerCase();
      const matchesSearch =
        f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSeverity && matchesSearch;
    });
  }, [findings, severityFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldAlert className="text-blue-500" size={24} />
            Security Findings
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Grounded observations from the current approved checks. Empty results are possible and expected.
          </p>
        </div>
        <button
          onClick={fetchFindings}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-sm transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-900 border border-slate-800 p-3 rounded-xl">
        <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800 px-3 py-1.5 rounded-lg flex-1 min-w-[200px]">
          <Search size={16} className="text-slate-500" />
          <input
            type="text"
            placeholder="Search findings by keyword, header, category..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none outline-none text-sm text-slate-200 placeholder-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto">
          {["All", "High", "Medium", "Low", "Informational"].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                severityFilter === sev
                  ? "bg-blue-600 text-white font-semibold"
                  : "bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Findings Table */}
      {loading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-12 text-center text-sm text-slate-400">
          <RefreshCw size={24} className="animate-spin text-blue-500 mx-auto mb-3" />
          Loading findings catalog…
        </div>
      ) : filteredFindings.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center text-sm text-slate-400">
          <ShieldCheck size={28} className="text-emerald-400 mx-auto mb-3" />
          <p className="text-slate-200 font-semibold mb-1">No findings shown for this view.</p>
          <p className="max-w-xl mx-auto leading-relaxed">
            This can mean your filters are hiding results, or the latest safe-baseline run did not produce findings.
            It does not mean the target has no vulnerabilities; only the current passive checks are represented here.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="text-left font-medium p-3.5 px-4">Severity</th>
                <th className="text-left font-medium p-3.5 px-4">Title</th>
                <th className="text-left font-medium p-3.5 px-4">Category</th>
                <th className="text-left font-medium p-3.5 px-4">Verification</th>
                <th className="text-left font-medium p-3.5 px-4">Assessment</th>
                <th className="text-right font-medium p-3.5 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredFindings.map((finding) => (
                <tr
                  key={finding.id}
                  onClick={() => setSelectedFinding(finding)}
                  className="hover:bg-slate-800/40 cursor-pointer transition"
                >
                  <td className="p-3.5 px-4 whitespace-nowrap">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full border text-xs font-semibold ${
                        SEVERITY_BADGES[finding.severity] || SEVERITY_BADGES.Informational
                      }`}
                    >
                      {finding.severity}
                    </span>
                  </td>
                  <td className="p-3.5 px-4 font-medium text-slate-200 max-w-md truncate">
                    {finding.title}
                  </td>
                  <td className="p-3.5 px-4 font-mono text-xs text-slate-400 uppercase">
                    {finding.category}
                  </td>
                  <td className="p-3.5 px-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-medium">
                      <ShieldCheck size={12} />
                      {finding.verification_status}
                    </span>
                  </td>
                  <td className="p-3.5 px-4 font-mono text-xs text-slate-400 whitespace-nowrap">
                    {finding.assessment_id.slice(0, 8)}…
                  </td>
                  <td className="p-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFinding(finding);
                      }}
                      className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 px-2.5 py-1 rounded-md transition"
                    >
                      <Eye size={12} />
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Inspection Modal */}
      {selectedFinding && (
        <FindingDetailModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
        />
      )}
    </div>
  );
}

export default FindingsView;
