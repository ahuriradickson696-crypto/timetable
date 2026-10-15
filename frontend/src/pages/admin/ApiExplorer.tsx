import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../components/ui/Toast";

interface Endpoint {
  method: string;
  path: string;
  description: string;
  category: string;
}

const ENDPOINTS: Endpoint[] = [
  // Users
  { method: "GET", path: "/api/admin/v1/users",                    description: "Every user account (students, lecturers, admins)", category: "Users" },
  { method: "GET", path: "/api/admin/v1/users/by-role/student",    description: "Only students", category: "Users" },
  { method: "GET", path: "/api/admin/v1/users/by-role/lecturer",   description: "Only lecturers", category: "Users" },
  { method: "GET", path: "/api/admin/v1/users/by-role/admin",      description: "Only admins", category: "Users" },
  { method: "GET", path: "/api/admin/v1/students",                 description: "Students with cohort + programme", category: "Users" },
  { method: "GET", path: "/api/admin/v1/employees",                description: "Non-students: lecturers, admins", category: "Users" },
  { method: "GET", path: "/api/admin/v1/admins",                   description: "Admins + officers", category: "Users" },

  // Academic structure
  { method: "GET", path: "/api/admin/v1/programmes",               description: "All programmes (BSE, DCM, DMLT)", category: "Academic" },
  { method: "GET", path: "/api/admin/v1/cohorts",                  description: "All cohorts", category: "Academic" },
  { method: "GET", path: "/api/admin/v1/course-units",             description: "Every module in the curriculum", category: "Academic" },

  // People
  { method: "GET", path: "/api/admin/v1/lecturers",                description: "Every lecturer", category: "People" },
  { method: "GET", path: "/api/admin/v1/lecturer-modules",         description: "Teaching assignments", category: "People" },

  // Facilities
  { method: "GET", path: "/api/admin/v1/rooms",                    description: "All rooms", category: "Facilities" },
  { method: "GET", path: "/api/admin/v1/time-periods",             description: "All time slots", category: "Facilities" },

  // Timetabling
  { method: "GET", path: "/api/admin/v1/activities",               description: "Teaching activities", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/enrollments",              description: "Student enrollments", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/timetable-runs",           description: "Every generation run", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/timetable-assignments",    description: "Raw slot assignments", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/timetable/by-cohort/DCM-Y1-Day-Aug2026",   description: "Full timetable for one cohort", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/timetable/by-lecturer/LECT-002",           description: "Full schedule for one lecturer", category: "Timetable" },
  { method: "GET", path: "/api/admin/v1/timetable/by-room/CR-01",                  description: "Full schedule for one room", category: "Timetable" },

  // Everything
  { method: "GET", path: "/api/admin/v1/dump",                     description: "EVERYTHING in a single JSON export", category: "Full Data" },
];

export default function ApiExplorer() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [preview, setPreview] = useState<{ path: string; data: any; status: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [baseUrl] = useState(() => {
    const base = api.defaults.baseURL || "http://127.0.0.1:8000/api/v1";
    return base.replace(/\/api\/v1$/, "");
  });

  const categories = ["All", ...Array.from(new Set(ENDPOINTS.map((e) => e.category)))];

  const filtered = ENDPOINTS.filter((e) => {
    if (selectedCategory !== "All" && e.category !== selectedCategory) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return e.path.toLowerCase().includes(q) || e.description.toLowerCase().includes(q);
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.show("ok", "Copied");
  };

  const tryEndpoint = async (path: string) => {
    setLoading(true);
    setPreview(null);
    try {
      // strip the /api/admin/v1 part — the axios client already has /api/v1 base,
      // so we need to call the raw URL. Use fetch instead.
      const token = localStorage.getItem("aviu_token");
      const res = await fetch(baseUrl + path, {
        headers: token ? { Authorization: "Bearer " + token } : {},
      });
      const data = await res.json();
      setPreview({ path, data, status: res.status });
    } catch (e: any) {
      setPreview({ path, data: { error: String(e) }, status: 0 });
    } finally {
      setLoading(false);
    }
  };

  const downloadDump = async () => {
    try {
      const token = localStorage.getItem("aviu_token");
      const res = await fetch(baseUrl + "/api/admin/v1/dump", {
        headers: token ? { Authorization: "Bearer " + token } : {},
      });
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "aviu-full-dump-" + Date.now() + ".json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.show("ok", "Downloaded full system dump");
    } catch (e: any) {
      toast.show("err", "Download failed");
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          Admin Data API
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Programmatic access to your full system data. Admin-only.
        </p>
      </div>

      {/* Base URL card */}
      <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white rounded-2xl p-6 mb-6">
        <div className="text-aviu-200 text-xs uppercase tracking-wider mb-2">Base URL</div>
        <div className="flex items-center gap-3 flex-wrap">
          <code className="bg-black/20 px-3 py-1.5 rounded font-mono text-sm">
            {baseUrl}/api/admin/v1
          </code>
          <button
            onClick={() => copyToClipboard(baseUrl + "/api/admin/v1")}
            className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded transition"
          >
            Copy
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={downloadDump}
            className="bg-white text-aviu-900 font-semibold px-4 py-2 rounded-lg hover:bg-aviu-100 transition text-sm"
          >
            Download Full System Dump (JSON)
          </button>
          <a
            href={baseUrl + "/docs#/admin-api"}
            target="_blank"
            rel="noreferrer"
            className="bg-aviu-700/50 hover:bg-aviu-700 text-white font-semibold px-4 py-2 rounded-lg transition text-sm border border-aviu-600"
          >
            Open Swagger Docs
          </a>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search endpoints..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
        />
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Endpoint list */}
      <div className="space-y-2 mb-8">
        {filtered.map((e) => (
          <div
            key={e.path}
            className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 hover:border-aviu-400 transition"
          >
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex-1 min-w-[300px]">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
                    {e.method}
                  </span>
                  <code className="font-mono text-sm text-aviu-800 dark:text-aviu-300 font-semibold">
                    {e.path}
                  </code>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">{e.description}</div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(baseUrl + e.path)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium"
                >
                  Copy URL
                </button>
                <button
                  onClick={() => tryEndpoint(e.path)}
                  disabled={loading}
                  className="text-xs px-3 py-1.5 rounded-lg bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-medium"
                >
                  Try
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Preview panel */}
      {preview && (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden">
          <div className="bg-gray-50 dark:bg-gray-950 px-5 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Response
              </div>
              <code className="text-sm font-mono text-aviu-800 dark:text-aviu-300">
                {preview.path}
              </code>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={
                  "px-2 py-0.5 rounded text-xs font-bold " +
                  (preview.status === 200
                    ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300"
                    : "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300")
                }
              >
                {preview.status || "ERR"}
              </span>
              <button
                onClick={() => setPreview(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl leading-none"
              >
                ×
              </button>
            </div>
          </div>
          <pre className="p-5 max-h-[500px] overflow-auto text-xs font-mono bg-gray-50 dark:bg-gray-950 text-gray-800 dark:text-gray-200">
            {JSON.stringify(preview.data, null, 2).slice(0, 5000)}
            {JSON.stringify(preview.data).length > 5000 && "\n\n... (truncated)"}
          </pre>
        </div>
      )}
    </div>
  );
}