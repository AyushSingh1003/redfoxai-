import { useCallback, useEffect, useState } from "react";
import {
  LayoutDashboard,
  Scan,
  ShieldAlert,
  FileText,
  Activity,
  Settings,
  ShieldCheck,
  Plus,
} from "lucide-react";
import {
  getAssessments,
  getFindings,
  seedDemoData,
  type Assessment,
  type Finding,
} from "../service/api";
import { DashboardView } from "./components/DashboardView";
import { AssessmentDetailsView } from "./components/AssessmentDetailsView";
import { FindingsView } from "./components/FindingsView";
import { ReportView } from "./components/ReportView";
import { EvaluationView } from "./components/EvaluationView";
import { SettingsView } from "./components/SettingsView";
import { NewAssessment } from "./components/NewAssessment";

type NavTab = "overview" | "assessments" | "findings" | "reports" | "evaluation" | "settings";

const NAV_ITEMS = [
  { id: "overview" as const, label: "Overview", icon: LayoutDashboard },
  { id: "assessments" as const, label: "Assessments", icon: Scan },
  { id: "findings" as const, label: "Findings", icon: ShieldAlert },
  { id: "reports" as const, label: "Reports", icon: FileText },
  { id: "evaluation" as const, label: "Agent Evaluation", icon: Activity },
  { id: "settings" as const, label: "Settings", icon: Settings },
];

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>("overview");
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const refreshAll = useCallback(async () => {
    try {
      const [asmList, findingList] = await Promise.all([
        getAssessments(),
        getFindings(),
      ]);
      setAssessments(asmList);
      setFindings(findingList);
      if (!selectedId && asmList.length > 0) {
        setSelectedId(asmList[0].id);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 5000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      const seeded = await seedDemoData();
      await refreshAll();
      setSelectedId(seeded.id);
    } catch (err) {
      console.error(err);
    } finally {
      setSeeding(false);
    }
  };

  const handleAssessmentCreated = (newAsm: Assessment) => {
    setShowModal(false);
    setSelectedId(newAsm.id);
    setCurrentTab("assessments");
    refreshAll();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800 p-5 hidden md:flex flex-col justify-between shrink-0 bg-slate-950/80">
        <div className="space-y-8">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-xl shadow-sm text-white">
              <ShieldCheck size={22} />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-slate-50 block leading-tight">
                REDFOX AI
              </span>
              <span className="text-[10px] text-slate-400 font-mono tracking-wider block">
                SECURITY PLATFORM
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="space-y-1">
            <p className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider px-3 mb-2">
              WORKSPACE
            </p>
            <nav className="space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium text-left transition ${
                      active
                        ? "bg-blue-600 text-white font-semibold shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                    }`}
                  >
                    <Icon size={17} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Sidebar Footer info */}
          <div className="pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Local Lab Only</span>
            </div>
          <p className="text-[10px] text-slate-600 font-mono">
            http://juice-shop:3000
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-800/90 bg-slate-950/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-sm capitalize text-slate-200">
              {NAV_ITEMS.find((n) => n.id === currentTab)?.label || "Overview"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-emerald-400 border border-emerald-800/60 bg-emerald-950/30 rounded-full px-3 py-1 font-medium hidden sm:inline-block">
              External scanning disabled
            </span>

            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-3.5 py-1.5 text-xs font-semibold shadow-sm transition"
            >
              <Plus size={14} />
              New Run
            </button>
          </div>
        </header>

        {/* Scrollable View Container */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto overflow-y-auto">
          {currentTab === "overview" && (
            <DashboardView
              assessments={assessments}
              findings={findings}
              selectedAssessmentId={selectedId}
              onSelectAssessment={(id) => {
                setSelectedId(id);
                setCurrentTab("assessments");
              }}
              onOpenNewModal={() => setShowModal(true)}
              onSeedDemo={handleSeedDemo}
              onNavigateToReport={(id) => {
                setSelectedId(id);
                setCurrentTab("reports");
              }}
              loading={loading}
              seeding={seeding}
            />
          )}

          {currentTab === "assessments" && (
            selectedId ? (
              <AssessmentDetailsView
                assessmentId={selectedId}
                onNavigateToReport={(id) => {
                  setSelectedId(id);
                  setCurrentTab("reports");
                }}
                onNavigateToFindings={() => setCurrentTab("findings")}
              />
            ) : (
              <div className="p-16 text-center text-slate-400 bg-slate-900 border border-dashed border-slate-800 rounded-2xl">
                No assessment selected. Start a new assessment or seed demo data from the dashboard.
              </div>
            )
          )}

          {currentTab === "findings" && <FindingsView />}

          {currentTab === "reports" && (
            <ReportView
              initialAssessmentId={selectedId}
              onSelectAssessment={(id) => setSelectedId(id)}
            />
          )}

          {currentTab === "evaluation" && <EvaluationView />}

          {currentTab === "settings" && <SettingsView />}
        </main>
      </div>

      {/* New Assessment Modal */}
      {showModal && (
        <NewAssessment
          onCancel={() => setShowModal(false)}
          onCreated={handleAssessmentCreated}
        />
      )}
    </div>
  );
}

export default App;
