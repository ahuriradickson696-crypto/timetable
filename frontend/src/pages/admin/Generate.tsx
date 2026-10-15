import { useEffect, useState } from "react";
import { api, TimetableRun } from "../../api/client";
import PageHeader from "../../components/PageHeader";

export default function Generate() {
  const [runs, setRuns] = useState<TimetableRun[]>([]);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    intake: "Aug",
    academic_year: "2026/2027",
    semester: 1,
    run_type: "teaching",
  });

  const loadRuns = async () => {
    const res = await api.get<TimetableRun[]>("/generation/runs");
    setRuns(res.data);
  };

  useEffect(() => { loadRuns(); }, []);

  const run = async () => {
    setRunning(true);
    setError("");
    setMessage("");
    try {
      const res = await api.post("/generation/generate", form);
      setMessage(`Run #${res.data.id} (${res.data.run_type}): ${res.data.message}`);
      loadRuns();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Generation failed");
    } finally {
      setRunning(false);
    }
  };

  const runTypeBadge = (rt: string) => {
    const colors: Record<string, string> = {
      teaching: "bg-blue-100 text-blue-700",
      test: "bg-yellow-100 text-yellow-700",
      exam: "bg-purple-100 text-purple-700",
    };
    return (
      <span className={"px-2 py-0.5 rounded text-xs font-medium " + (colors[rt] || "bg-gray-100 text-gray-700")}>
        {rt}
      </span>
    );
  };

  const statusBadge = (s: string) => {
    const colors: Record<string, string> = {
      success: "bg-green-100 text-green-700",
      failed: "bg-red-100 text-red-700",
      running: "bg-yellow-100 text-yellow-700",
    };
    return (
      <span className={"px-2 py-0.5 rounded text-xs font-medium " + (colors[s] || "bg-gray-100 text-gray-700")}>
        {s}
      </span>
    );
  };

  return (
    <div>
      <PageHeader
        title="Generate Timetable"
        subtitle="Teaching, tests, or final exams  powered by OR-Tools CP-SAT"
      />

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-1 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Parameters</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Type</label>
              <select value={form.run_type}
                onChange={(e) => setForm({ ...form, run_type: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 font-medium">
                <option value="teaching"> Teaching (Lectures)</option>
                <option value="test"> Tests (Mid-semester)</option>
                <option value="exam"> Final Exams</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Intake</label>
              <select value={form.intake} onChange={(e) => setForm({ ...form, intake: e.target.value })}
                className="w-full border rounded-lg px-3 py-2">
                <option>Jan</option><option>May</option><option>Aug</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Academic Year</label>
              <input value={form.academic_year}
                onChange={(e) => setForm({ ...form, academic_year: e.target.value })}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Semester</label>
              <select value={form.semester}
                onChange={(e) => setForm({ ...form, semester: Number(e.target.value) })}
                className="w-full border rounded-lg px-3 py-2">
                <option value={1}>1</option>
                <option value={2}>2</option>
              </select>
            </div>
            <button onClick={run} disabled={running}
              className="w-full bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-400 text-white font-semibold py-3 rounded-lg mt-2">
              {running ? " Solving..." : " Run Solver"}
            </button>
            {message && <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{message}</div>}
            {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
          </div>
        </div>

        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Generation History</h2>
          {runs.length === 0 ? (
            <p className="text-gray-400 text-sm">No runs yet. Run the solver to generate one.</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {runs.map((r) => (
                <div key={r.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">Run #{r.id}</span>
                      {runTypeBadge(r.run_type)}
                    </div>
                    <p className="text-xs text-gray-500">{r.intake} {r.academic_year}  Sem {r.semester}</p>
                    <p className="text-xs text-gray-400">{new Date(r.created_at).toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    {statusBadge(r.status)}
                    <p className="text-xs text-gray-500 mt-1">{r.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
