import { useEffect, useState } from "react";
import { api, TimetableRun } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../components/ui/Toast";

interface RoomRow {
  room: string;
  room_name: string;
  days: number[];
  total: number;
}

interface RoomData {
  days: string[];
  rooms: RoomRow[];
  max_value: number;
}

interface LecturerRow {
  lecturer_id: string;
  name: string;
  hours: number;
  max_hours: number;
  utilization_pct: number;
  status: string;
}

interface ProgrammeRow {
  programme: string;
  activities: number;
  unique_lecturers: number;
  unique_cohorts: number;
}

interface CohortRow {
  cohort: string;
  days: number[];
  total: number;
}

export default function Analytics() {
  const toast = useToast();
  const [runs, setRuns] = useState<TimetableRun[]>([]);
  const [runId, setRunId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"rooms" | "lecturers" | "programmes" | "cohorts">("rooms");

  const [rooms, setRooms] = useState<RoomData | null>(null);
  const [lecturers, setLecturers] = useState<LecturerRow[]>([]);
  const [programmes, setProgrammes] = useState<ProgrammeRow[]>([]);
  const [cohorts, setCohorts] = useState<{ days: string[]; cohorts: CohortRow[]; max_value: number } | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        const r = await api.get<TimetableRun[]>("/generation/runs");
        const successful = r.data.filter((x) => x.status === "success");
        setRuns(successful);
        if (successful[0]) setRunId(successful[0].id);
      } catch {
        toast.show("err", "Failed to load runs");
      }
    };
    init();
  }, []);

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    const load = async () => {
      try {
        const [rm, lc, pg, ch] = await Promise.all([
          api.get<RoomData>(`/analytics/runs/${runId}/rooms`),
          api.get<{ lecturers: LecturerRow[] }>(`/analytics/runs/${runId}/lecturers`),
          api.get<{ programmes: ProgrammeRow[] }>(`/analytics/runs/${runId}/programmes`),
          api.get(`/analytics/runs/${runId}/cohorts`),
        ]);
        setRooms(rm.data);
        setLecturers(lc.data.lecturers);
        setProgrammes(pg.data.programmes);
        setCohorts(ch.data);
      } catch (e: any) {
        toast.show("err", e.response?.data?.detail || "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [runId]);

  const cellColor = (value: number, max: number) => {
    if (value === 0) return "bg-gray-50";
    if (max === 0) return "bg-aviu-100";
    const pct = value / max;
    if (pct < 0.25) return "bg-aviu-100 text-aviu-900";
    if (pct < 0.5) return "bg-aviu-300 text-aviu-900";
    if (pct < 0.75) return "bg-aviu-500 text-white";
    return "bg-aviu-800 text-white";
  };

  const statusColor = (s: string) => {
    if (s === "overloaded") return "bg-red-100 text-red-700";
    if (s === "full") return "bg-yellow-100 text-yellow-700";
    return "bg-green-100 text-green-700";
  };

  const currentRun = runs.find((r) => r.id === runId);

  return (
    <div>
      <PageHeader title="Analytics & Reports" subtitle="Utilisation, load, and free slot analysis" />

      {/* Run selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex items-center gap-4 flex-wrap">
        <label className="text-sm font-medium text-gray-700">Run:</label>
        <select value={runId ?? ""} onChange={(e) => setRunId(Number(e.target.value))}
          className="border rounded-lg px-3 py-2">
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              Run #{r.id}  {r.run_type} {r.is_published ? "" : ""}
            </option>
          ))}
        </select>
        {currentRun && (
          <span className="text-sm text-gray-500">{currentRun.message}</span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {[
          { id: "rooms", label: " Room Utilisation" },
          { id: "lecturers", label: " Lecturer Load" },
          { id: "programmes", label: " Programmes" },
          { id: "cohorts", label: " Cohort Load" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as any)}
            className={
              "px-4 py-2 font-medium text-sm border-b-2 -mb-px transition " +
              (tab === t.id
                ? "border-aviu-800 text-aviu-800"
                : "border-transparent text-gray-500 hover:text-aviu-700")
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <TableSkeleton rows={8} />
      ) : (
        <>
          {/* ROOMS HEATMAP */}
          {tab === "rooms" && rooms && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-lg mb-4">Room Utilisation Heatmap</h2>
              <p className="text-sm text-gray-500 mb-4">Darker = more classes scheduled that day</p>
              <div className="overflow-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-2 text-sm font-semibold bg-aviu-50">Room</th>
                      {rooms.days.map((d) => (
                        <th key={d} className="p-2 text-sm font-semibold bg-aviu-50 text-center">{d.slice(0, 3)}</th>
                      ))}
                      <th className="p-2 text-sm font-semibold bg-aviu-50 text-center">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rooms.rooms.map((r) => (
                      <tr key={r.room} className="border-b">
                        <td className="p-2 text-sm">
                          <div className="font-medium">{r.room}</div>
                          <div className="text-xs text-gray-500">{r.room_name}</div>
                        </td>
                        {r.days.map((v, i) => (
                          <td key={i} className="p-1 text-center">
                            <div className={"py-3 rounded font-bold " + cellColor(v, rooms.max_value)}>
                              {v || ""}
                            </div>
                          </td>
                        ))}
                        <td className="p-2 text-center font-bold text-aviu-800">{r.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-2 mt-4 text-sm text-gray-500">
                <span>Low</span>
                <div className="w-4 h-4 bg-gray-50 rounded"></div>
                <div className="w-4 h-4 bg-aviu-100 rounded"></div>
                <div className="w-4 h-4 bg-aviu-300 rounded"></div>
                <div className="w-4 h-4 bg-aviu-500 rounded"></div>
                <div className="w-4 h-4 bg-aviu-800 rounded"></div>
                <span>High</span>
              </div>
            </div>
          )}

          {/* LECTURER LOAD */}
          {tab === "lecturers" && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-lg mb-4">Lecturer Load Report</h2>
              <p className="text-sm text-gray-500 mb-4">Hours per week vs maximum allowed</p>
              <table className="w-full">
                <thead>
                  <tr className="bg-aviu-800 text-white">
                    <th className="text-left p-3 text-sm">Lecturer</th>
                    <th className="text-left p-3 text-sm">Name</th>
                    <th className="text-right p-3 text-sm">Hours</th>
                    <th className="text-right p-3 text-sm">Max</th>
                    <th className="p-3 text-sm">Utilisation</th>
                    <th className="text-center p-3 text-sm">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {lecturers.map((l) => (
                    <tr key={l.lecturer_id} className="border-b hover:bg-aviu-50">
                      <td className="p-3 text-sm font-medium">{l.lecturer_id}</td>
                      <td className="p-3 text-sm">{l.name}</td>
                      <td className="p-3 text-sm text-right font-bold">{l.hours}</td>
                      <td className="p-3 text-sm text-right text-gray-600">{l.max_hours}</td>
                      <td className="p-3">
                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={
                              "h-2 rounded-full " +
                              (l.utilization_pct > 100 ? "bg-red-500"
                                : l.utilization_pct >= 75 ? "bg-yellow-500"
                                : "bg-green-500")
                            }
                            style={{ width: Math.min(100, l.utilization_pct) + "%" }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{l.utilization_pct}%</div>
                      </td>
                      <td className="p-3 text-center">
                        <span className={"px-2 py-0.5 rounded text-xs font-medium " + statusColor(l.status)}>
                          {l.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* PROGRAMMES */}
          {tab === "programmes" && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-lg mb-4">Programme Summary</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {programmes.map((p) => (
                  <div key={p.programme} className="border rounded-xl p-5 bg-gradient-to-br from-aviu-50 to-white">
                    <div className="font-bold text-aviu-900 text-xl mb-3">{p.programme}</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Activities</span>
                        <span className="font-bold">{p.activities}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Lecturers</span>
                        <span className="font-bold">{p.unique_lecturers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Cohorts</span>
                        <span className="font-bold">{p.unique_cohorts}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* COHORT LOAD */}
          {tab === "cohorts" && cohorts && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-lg mb-4">Cohort Weekly Load</h2>
              <p className="text-sm text-gray-500 mb-4">Teaching hours per day per cohort</p>
              <div className="overflow-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-2 text-sm font-semibold bg-aviu-50">Cohort</th>
                      {cohorts.days.map((d) => (
                        <th key={d} className="p-2 text-sm font-semibold bg-aviu-50 text-center">{d.slice(0, 3)}</th>
                      ))}
                      <th className="p-2 text-sm font-semibold bg-aviu-50 text-center">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cohorts.cohorts.map((c) => (
                      <tr key={c.cohort} className="border-b">
                        <td className="p-2 text-sm font-medium">{c.cohort}</td>
                        {c.days.map((v, i) => (
                          <td key={i} className="p-1 text-center">
                            <div className={"py-3 rounded font-bold " + cellColor(v, cohorts.max_value)}>
                              {v || ""}
                            </div>
                          </td>
                        ))}
                        <td className="p-2 text-center font-bold text-aviu-800">{c.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
