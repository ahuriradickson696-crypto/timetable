import { useEffect, useState } from "react";
import { api, Cohort, Lecturer, Room, TimetableRun, TimetableCell, TimePeriod, Programme, CourseUnit } from "../../api/client";
import PageHeader from "../../components/PageHeader";

const DAYS_TEACHING = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const DAYS_EXAM = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function TimetableView() {
  const [runs, setRuns] = useState<TimetableRun[]>([]);
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [units, setUnits] = useState<CourseUnit[]>([]);
  const [periods, setPeriods] = useState<TimePeriod[]>([]);

  const [runId, setRunId] = useState<number | null>(null);
  const [viewType, setViewType] = useState("cohort");
  const [viewKey, setViewKey] = useState("");
  const [cells, setCells] = useState<TimetableCell[]>([]);

  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);
  const [dragged, setDragged] = useState<TimetableCell | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [log, setLog] = useState<any[]>([]);

  useEffect(() => {
    const init = async () => {
      const [r, c, l, rm, t, p, u] = await Promise.all([
        api.get<TimetableRun[]>("/generation/runs"),
        api.get<Cohort[]>("/cohorts"),
        api.get<Lecturer[]>("/lecturers"),
        api.get<Room[]>("/rooms"),
        api.get<TimePeriod[]>("/time-periods"),
        api.get<Programme[]>("/programmes"),
        api.get<CourseUnit[]>("/course-units"),
      ]);
      setRuns(r.data);
      setCohorts(c.data);
      setLecturers(l.data);
      setRooms(rm.data);
      setPeriods(t.data);
      setProgrammes(p.data);
      setUnits(u.data);
      if (r.data[0]) setRunId(r.data[0].id);
    };
    init();
  }, []);

  const loadView = async () => {
    if (!runId || !viewKey) return;
    const res = await api.get<TimetableCell[]>(
      `/generation/runs/${runId}/by-${viewType}/${encodeURIComponent(viewKey)}`
    );
    setCells(res.data);
  };

  useEffect(() => { loadView(); }, [runId, viewType, viewKey]);

  const currentRun = runs.find((r) => r.id === runId);
  const isExamMode = currentRun?.run_type === "exam" || currentRun?.run_type === "test";
  const DAYS = isExamMode ? DAYS_EXAM : DAYS_TEACHING;
  const dayPeriods = periods.filter((p) => p.mode === (isExamMode ? (currentRun?.run_type === "exam" ? "Exam" : "Test") : "Day") && !p.is_break);
  const daySlots = Array.from(new Set(dayPeriods.map((p) => `${p.start_time}-${p.end_time}`))).sort();

  const findCell = (day: string, slot: string) => {
    const [start, end] = slot.split("-");
    return cells.find((c) => c.day === day && c.start_time === start && c.end_time === end);
  };

  const showToast = (type: "ok" | "err", msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const publishRun = async () => {
    if (!runId) return;
    try {
      await api.post(`/publishing/runs/${runId}/publish`);
      showToast("ok", `Run #${runId} published`);
      const r = await api.get<TimetableRun[]>("/generation/runs");
      setRuns(r.data);
    } catch (e: any) {
      showToast("err", e.response?.data?.detail || "Publish failed");
    }
  };

  const unpublishRun = async () => {
    if (!runId) return;
    try {
      await api.post(`/publishing/runs/${runId}/unpublish`);
      showToast("ok", `Run #${runId} unpublished`);
      const r = await api.get<TimetableRun[]>("/generation/runs");
      setRuns(r.data);
    } catch (e: any) {
      showToast("err", e.response?.data?.detail || "Unpublish failed");
    }
  };

  const unlockRun = async () => {
    if (!runId) return;
    try {
      await api.post(`/publishing/runs/${runId}/unlock`);
      showToast("ok", "Run unlocked");
      const r = await api.get<TimetableRun[]>("/generation/runs");
      setRuns(r.data);
    } catch (e: any) {
      showToast("err", e.response?.data?.detail || "Unlock failed");
    }
  };

  const loadLog = async () => {
    const res = await api.get<any[]>("/changelog?limit=50");
    setLog(res.data);
    setShowLog(true);
  };

  const onDragStart = (cell: TimetableCell) => {
    if (!cell.assignment_id || cell.is_locked) return;
    setDragged(cell);
  };

  const onDrop = async (day: string, slot: string) => {
    if (!dragged || !dragged.assignment_id || !runId) return;
    if (currentRun?.is_locked) {
      showToast("err", "Run is locked. Unlock before editing.");
      setDragged(null);
      return;
    }
    const [start, end] = slot.split("-");
    const targetPeriod = dayPeriods.find((p) => p.day === day && p.start_time === start && p.end_time === end);
    if (!targetPeriod) { setDragged(null); return; }
    const targetRoom = dragged.room_code || "CR-01";
    try {
      const res = await api.post(
        `/manual-edit/runs/${runId}/assignments/${dragged.assignment_id}/move?force=false`,
        { period_id: targetPeriod.id, room_code: targetRoom }
      );
      if (res.data.status === "ok") {
        showToast("ok", "Moved successfully");
        loadView();
      } else {
        showToast("err", res.data.message + "  " + (res.data.conflicts[0]?.message || ""));
      }
    } catch (e: any) {
      showToast("err", e.response?.data?.detail || "Move failed");
    } finally {
      setDragged(null);
    }
  };

  const downloadUrl = (fmt: string) =>
    `http://localhost:8000/api/v1/generation/runs/${runId}/export/${fmt}?view=${viewType}&key=${encodeURIComponent(viewKey)}`;

  const runTypeBadge = (rt: string) => {
    const colors: Record<string, string> = {
      teaching: "bg-blue-100 text-blue-700",
      test: "bg-yellow-100 text-yellow-700",
      exam: "bg-purple-100 text-purple-700",
    };
    return (
      <span className={"px-2 py-0.5 rounded text-xs font-medium " + (colors[rt] || "bg-gray-100")}>
        {rt}
      </span>
    );
  };

  const keyOptions = () => {
    if (viewType === "cohort") return cohorts.map((c) => ({ v: c.id, l: c.id }));
    if (viewType === "lecturer") return lecturers.map((l) => ({ v: l.id, l: `${l.id} - ${l.full_name}` }));
    if (viewType === "room") return rooms.map((r) => ({ v: r.code, l: `${r.code} - ${r.name}` }));
    if (viewType === "programme") return programmes.map((p) => ({ v: p.code, l: `${p.code} - ${p.name}` }));
    if (viewType === "module") return units.map((u) => ({ v: u.code, l: `${u.code} - ${u.name}` }));
    return [];
  };

  return (
    <div>
      <PageHeader title="Timetable View" subtitle="View by Cohort, Lecturer, Room, Programme, or Module" />

      {toast && (
        <div className={"fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white font-medium " +
          (toast.type === "ok" ? "bg-green-600" : "bg-red-600")}>
          {toast.msg}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Run</label>
            <select value={runId ?? ""} onChange={(e) => setRunId(Number(e.target.value))}
              className="w-full border rounded-lg px-3 py-2">
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  Run #{r.id}  {r.run_type} {r.is_published ? "" : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">View</label>
            <select value={viewType} onChange={(e) => { setViewType(e.target.value); setViewKey(""); }}
              className="w-full border rounded-lg px-3 py-2">
              <option value="cohort">By Cohort</option>
              <option value="lecturer">By Lecturer</option>
              <option value="room">By Room</option>
              <option value="programme">By Programme</option>
              <option value="module">By Module</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-600 mb-1">Select</label>
            <select value={viewKey} onChange={(e) => setViewKey(e.target.value)}
              className="w-full border rounded-lg px-3 py-2">
              <option value="">Choose...</option>
              {keyOptions().map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
          </div>
          <div className="flex items-end gap-2">
            <a href={downloadUrl("pdf")} target="_blank" rel="noreferrer"
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm"> PDF</a>
            <a href={downloadUrl("excel")} target="_blank" rel="noreferrer"
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm"> Excel</a>
          </div>
        </div>

        {currentRun && (
          <div className="flex items-center gap-3 pt-3 border-t flex-wrap">
            <span className="font-medium text-sm">Current:</span>
            {runTypeBadge(currentRun.run_type)}
            {currentRun.is_published && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                 PUBLISHED
              </span>
            )}
            {currentRun.is_locked && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                 LOCKED
              </span>
            )}
            <span className="text-sm text-gray-600">{currentRun.message}</span>

            <div className="ml-auto flex gap-2">
              {!currentRun.is_published ? (
                <button onClick={publishRun}
                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-sm">
                   Publish
                </button>
              ) : (
                <button onClick={unpublishRun}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1.5 rounded-lg text-sm">
                  Unpublish
                </button>
              )}
              {currentRun.is_locked && (
                <button onClick={unlockRun}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1.5 rounded-lg text-sm">
                   Unlock
                </button>
              )}
              <button onClick={loadLog}
                className="bg-aviu-800 hover:bg-aviu-900 text-white px-3 py-1.5 rounded-lg text-sm">
                 History
              </button>
            </div>
          </div>
        )}
      </div>

      {cells.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-500">
          {viewKey ? "No timetable entries for this selection" : "Select a view and key above"}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-aviu-800 text-white">
                <th className="p-2 text-left text-sm font-semibold">Time</th>
                {DAYS.map((d) => <th key={d} className="p-2 text-left text-sm font-semibold">{d}</th>)}
              </tr>
            </thead>
            <tbody>
              {daySlots.map((s) => (
                <tr key={s} className="border-b">
                  <td className="p-2 text-xs font-mono bg-aviu-50 font-bold whitespace-nowrap">
                    {s.replace("-", " - ")}
                  </td>
                  {DAYS.map((day) => {
                    const cell = findCell(day, s);
                    const editable = cell && cell.assignment_id && !cell.is_locked && !currentRun?.is_locked;
                    return (
                      <td key={day} className="p-2 align-top"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={() => onDrop(day, s)}>
                        {cell && cell.module_code ? (
                          <div
                            draggable={!!editable}
                            onDragStart={() => onDragStart(cell)}
                            className={
                              "border-l-4 p-2 rounded text-xs " +
                              (cell.is_manual ? "bg-yellow-100 border-yellow-600" : "bg-aviu-100 border-aviu-600") +
                              (editable ? " cursor-move hover:shadow-md" : "")
                            }
                          >
                            <div className="font-bold text-aviu-900">{cell.module_code}</div>
                            <div className="text-gray-700">{cell.module_name}</div>
                            <div className="text-gray-500 mt-1"> {cell.room_code}</div>
                            {cell.lecturer_name && <div className="text-gray-500"> {cell.lecturer_name}</div>}
                            {cell.is_manual && <div className="mt-1 text-xs font-bold text-yellow-800"> manual</div>}
                            {cell.is_locked && <div className="mt-1 text-xs font-bold text-red-700"> locked</div>}
                          </div>
                        ) : (
                          <span className="text-gray-200"></span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showLog && (
        <div className="fixed inset-0 bg-black/50 z-40 flex items-center justify-center p-4" onClick={() => setShowLog(false)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-white">
              <h3 className="font-bold text-lg"> Change History</h3>
              <button onClick={() => setShowLog(false)} className="text-gray-500 hover:text-gray-800 text-2xl leading-none"></button>
            </div>
            <div className="p-4">
              {log.length === 0 ? <p className="text-gray-400">No changes yet.</p> : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">When</th>
                      <th className="text-left p-2">Action</th>
                      <th className="text-left p-2">Entity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {log.map((e) => (
                      <tr key={e.id} className="border-b hover:bg-aviu-50">
                        <td className="p-2 text-xs text-gray-500">{new Date(e.timestamp).toLocaleString()}</td>
                        <td className="p-2 font-medium">{e.action}</td>
                        <td className="p-2 text-gray-600">{e.entity_type} #{e.entity_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
