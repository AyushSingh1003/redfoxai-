import { useEffect, useState } from "react";
import {
  Settings,
  Shield,
  Cpu,
  Lock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { getSettings, type SystemSettings } from "../../service/api";

export function SettingsView() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings()
      .then((data) => setSettings(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings className="text-blue-500" size={24} />
          System Settings & Guardrails
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Review environment parameters, lab target isolation boundaries, and registered security tools.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-sm text-slate-400">
          <RefreshCw size={24} className="animate-spin text-blue-500 mx-auto mb-3" />
          Loading settings…
        </div>
      ) : !settings ? (
        <div className="p-12 text-center text-sm text-slate-400">
          Failed to load settings.
        </div>
      ) : (
        <div className="space-y-5">
          {/* Target Boundary Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Shield size={18} className="text-emerald-400" />
              <span>Target Boundary & Scope Policy</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">Authorized Lab Target:</span>
                <span className="font-mono text-emerald-300 font-medium">{settings.lab_target}</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">Environment:</span>
                <span className="uppercase text-slate-200 font-mono">{settings.app_env}</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">Arbitrary External Scanning:</span>
                <span className="text-red-400 font-medium">Disabled (Fail-Closed)</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">Current Product Mode:</span>
                <span className="text-blue-400 font-medium">Local Lab / Portfolio Demo</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">SSRF & Cloud Metadata Protection:</span>
                <span className="text-emerald-400 font-medium">Active (169.254.169.254 blocked)</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Shield size={18} className="text-blue-400" />
              <span>How a Company Would Use This</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              In a real company deployment, REDFOX AI would not simply accept any URL. Security teams would register
              approved assets, confirm ownership, select allowed assessment profiles, and keep an audit trail of every
              run. This prototype demonstrates that control model using one intentionally safe local target.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
                <span className="block text-slate-200 font-semibold mb-1">1. Approve Scope</span>
                <span className="text-slate-500">Only owned systems enter the allowlist.</span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
                <span className="block text-slate-200 font-semibold mb-1">2. Run Safe Checks</span>
                <span className="text-slate-500">Tools execute from a fixed registry.</span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
                <span className="block text-slate-200 font-semibold mb-1">3. Review Evidence</span>
                <span className="text-slate-500">Reports explain findings and limitations.</span>
              </div>
            </div>
          </div>

          {/* Registered Tools Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Terminal size={18} className="text-blue-400" />
              <span>Registered Security Tools ({settings.allowed_tools.length})</span>
            </div>
            <div className="space-y-3">
              {settings.allowed_tools.map((tool) => (
                <div
                  key={tool.name}
                  className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex items-start justify-between gap-4 text-xs"
                >
                  <div className="space-y-1">
                    <span className="font-mono text-blue-400 font-semibold">{tool.name}</span>
                    <p className="text-slate-400 leading-relaxed">{tool.description}</p>
                  </div>
                  <span className="shrink-0 text-slate-500 font-mono">
                    timeout: {tool.timeout_seconds}s
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* LLM Engine Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Cpu size={18} className="text-indigo-400" />
              <span>AI Reasoning Engine (Ollama / Local LLM)</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">LLM Provider:</span>
                <span className="text-slate-200">{settings.llm_provider}</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-slate-400">Configured Model:</span>
                <span className="font-mono text-slate-200">{settings.llm_model}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">LLM Server Status:</span>
                {settings.llm_available ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                    <CheckCircle size={12} /> Connected & Online
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full font-medium">
                    <AlertCircle size={12} /> Offline (Safe Deterministic Fallback Active)
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Platform Version & Privacy Notice */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-2 text-xs text-slate-500">
            <div className="flex items-center gap-1.5 text-slate-400 font-semibold">
              <Lock size={14} className="text-slate-400" />
              <span>Zero Credential Leakage Architecture</span>
            </div>
            <p className="leading-relaxed">
              Redfox AI never exposes secret environment variables, tokens, or raw credentials over API responses or client-facing views. All tool outputs are sanitized to exclude private cookie values and internal auth headers.
            </p>
            <div className="pt-2 text-[11px] text-slate-600 font-mono">
              Redfox AI Agent Engine v{settings.agent_version} • Isolated Docker Security Lab
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SettingsView;
