// AVIU_PORTAL_FILTERED
import { useEffect, useState } from "react";
import { useNotifications } from "../../hooks/useNotifications";
import { api, TimetableCell, downloadFile } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import ClassDetailModal from "../../components/ClassDetailModal";

interface PortalMe {
  id: number;
  email: string;
  full_name: string;
  role: string;
  cohort_id?: string;
  lecturer_id?: string;
  cohort_name?: string;
  programme_name?: string;
  year_level?: number;
  mode?: string;
  intake?: string;
  academic_year?: string;
  semester?: number;
}

interface NextClass {
  day: string;
  is_today: boolean;
  days_until?: number;
  start_time: string;
  end_time: string;
  module_code: string;
  module_name: string;
  room_code: string;
  lecturer_name?: string;
  minutes_until?: number;
  activity_id?: string;
}

export default function MyTimetable() {
  const { markSeen } = useNotifications();
  useEffect(() => { markSeen(); }, [markSeen]);

  const [cells, setCells] = useState<TimetableCell[]>([]);
  const [me, setMe] = useState<PortalMe | null>(null);
  const [next, setNext] = useState<NextClass | null>(null);
  const [nextMsg, setNextMsg] = useState("");
  const [today, setToday] = useState<{ day: string; classes: any[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedActivity, setSelectedActivity] = useState<string | null>(null);
  const [downloading, setDownloading] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [c, m, n, t] = await Promise.all([
          api.get<TimetableCell[]>("/portal/my-timetable"),
          api.get<PortalMe>("/portal/me"),
          api.get("/portal/my-next-class"),
          api.get("/portal/my-today"),
        ]);
        setCells(c.data);
        setMe(m.data);
        setNext(n.data.next);
        setNextMsg(n.data.message);
        setToday(t.data);
      } catch (e: any) {
        setError(e.response?.data?.detail || "Failed to load timetable");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleDownload = async (fmt: "ical" | "pdf" | "excel") => {
    setDownloading(fmt);
    const name = (me?.full_name || "student").replace(/\s+/g, "_").toLowerCase();
    const ext = fmt === "ical" ? "ics" : fmt === "pdf" ? "pdf" : "xlsx";
    const filename = "timetable_" + name + "." + ext;
    const url = "http://localhost:8000/api/v1/portal/my-timetable/" + fmt;
    try {
      await downloadFile(url, filename);
    } finally {
      setDownloading("");
    }
  };

  const slots = Array.from(
    new Set(cells.filter((c) => c.module_code).map((c) => c.start_time + "-" + c.end_time))
  ).sort();

  const findCell = (day: string, slot: string) => {
    const [start, end] = slot.split("-");
    return cells.find((c) => c.day === day && c.start_time === start && c.end_time === end);
  };

  const roleLabel = me?.role === "student" ? "Student" : me?.role === "lecturer" ? "Lecturer" : "";

  if (loading) return <div className="p-8 text-aviu-700">Loading your timetable...</div>;

  return (
    <div>
      <PageHeader
        title={"Welcome, " + (me?.full_name?.split(" ")[0] || "Student")}
        subtitle={
          me?.cohort_name
            ? roleLabel + "  " + me.cohort_name + (me.programme_name ? "  " + me.programme_name : "")
            : "Your personal schedule"
        }
        action={
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => handleDownload("ical")}
              disabled={downloading === "ical"}
              className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-400 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
               Add to Calendar
            </button>
            <button
              onClick={() => handleDownload("pdf")}
              disabled={downloading === "pdf"}
              className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
               PDF
            </button>
            <button
              onClick={() => handleDownload("excel")}
              disabled={downloading === "excel"}
              className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
               Excel
            </button>
          </div>
        }
      />

      {me?.academic_year && (
        <div className="bg-aviu-50 dark:bg-aviu-900/30 border border-aviu-200 rounded-xl p-4 mb-4 text-sm">
          <div className="font-semibold text-aviu-900">
             Semester {me.semester}  {me.academic_year}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
            {me.intake} intake  Year {me.year_level}  {me.mode} mode
          </div>
        </div>
      )}

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 text-yellow-800">
          {error}
        </div>
      )}

      {next && (
        <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white rounded-xl p-6 mb-4 shadow-lg">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="text-aviu-200 text-xs uppercase tracking-wider font-bold mb-1">
                 {next.is_today ? "NEXT CLASS TODAY" : "UPCOMING CLASS"}
              </div>
              <div className="text-2xl font-bold mb-1">{next.module_code}</div>
              <div className="text-sm opacity-90 mb-3">{next.module_name}</div>
              <div className="flex gap-4 text-sm flex-wrap">
                <span> {next.start_time}{next.end_time}</span>
                <span> {next.room_code}</span>
                {next.lecturer_name && <span> {next.lecturer_name}</span>}
              </div>
            </div>
            <div className="text-right">
              {next.is_today && next.minutes_until !== undefined ? (
                <>
                  <div className="text-4xl font-bold">
                    {next.minutes_until < 60
                      ? next.minutes_until + "m"
                      : Math.floor(next.minutes_until / 60) + "h " + (next.minutes_until % 60) + "m"}
                  </div>
                  <div className="text-xs uppercase tracking-wider opacity-80">until</div>
                </>
              ) : (
                <>
                  <div className="text-4xl font-bold">{next.day.slice(0, 3)}</div>
                  <div className="text-xs uppercase tracking-wider opacity-80">next class</div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {!next && nextMsg && (
        <div className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-4 text-center text-gray-600 dark:text-gray-400">
          {nextMsg}
        </div>
      )}

      {today && today.classes.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 mb-6">
          <h2 className="font-bold text-lg mb-3"> Today  {today.day}</h2>
          <div className="space-y-2">
            {today.classes.map((c: any, i: number) => (
              <div
                key={i}
                onClick={() => c.activity_id && setSelectedActivity(c.activity_id)}
                className="flex items-center gap-4 p-3 rounded-lg border border-gray-100 dark:border-gray-800 hover:bg-aviu-50 cursor-pointer"
              >
                <div className="font-mono text-sm font-bold text-aviu-800 w-28">
                  {c.start_time}<br />
                  <span className="text-gray-400 dark:text-gray-500 font-normal">{c.end_time}</span>
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-sm">{c.module_code}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{c.module_name}</div>
                </div>
                <div className="text-right text-xs text-gray-500 dark:text-gray-400">
                  <div> {c.room_code}</div>
                  {c.lecturer_name && <div> {c.lecturer_name}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {cells.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center text-gray-500 dark:text-gray-400">
          <div className="text-5xl mb-3"></div>
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-2">No modules enrolled</h3>
          <p className="mb-4">You have not registered for any modules yet.</p>
          <a
            href="/register"
            className="inline-block bg-aviu-800 hover:bg-aviu-900 text-white font-semibold px-6 py-3 rounded-lg"
          >
             Register Your Modules
          </a>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-auto">
          <div className="p-4 border-b bg-aviu-50 dark:bg-aviu-900/30">
            <h2 className="font-bold text-aviu-900"> Weekly Schedule</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Click any class for details</p>
          </div>
          <table className="w-full">
            <thead>
              <tr className="bg-aviu-800 text-white">
                <th className="p-3 text-left text-sm font-semibold">Time</th>
                {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map((d) => (
                  <th key={d} className="p-3 text-left text-sm font-semibold">{d}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {slots.map((s) => (
                <tr key={s} className="border-b">
                  <td className="p-2 text-xs font-mono bg-aviu-50 dark:bg-aviu-900/30 font-bold whitespace-nowrap">
                    {s.replace("-", "  ")}
                  </td>
                  {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map((day) => {
                    const cell = findCell(day, s);
                    return (
                      <td key={day} className="p-2 align-top">
                        {cell && cell.module_code ? (
                          <div
                            onClick={() => cell.activity_id && setSelectedActivity(cell.activity_id)}
                            className="bg-aviu-100 dark:bg-aviu-900/40 border-l-4 border-aviu-600 p-3 rounded cursor-pointer hover:bg-aviu-200 hover:shadow-md transition"
                          >
                            <div className="font-bold text-aviu-900 text-sm">{cell.module_code}</div>
                            <div className="text-xs text-gray-700 dark:text-gray-300 mt-0.5">{cell.module_name}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1"> {cell.room_code}</div>
                            {cell.lecturer_name && (
                              <div className="text-xs text-gray-500 dark:text-gray-400"> {cell.lecturer_name}</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-300 text-xs"></span>
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

      {selectedActivity && (
        <ClassDetailModal activityId={selectedActivity} onClose={() => setSelectedActivity(null)} />
      )}
    </div>
  );
}
