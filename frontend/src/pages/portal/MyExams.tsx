import { useEffect, useState } from "react";
import { api } from "../../api/client";
import PageHeader from "../../components/PageHeader";

interface Session {
  start_time: string;
  end_time: string;
  module_code: string;
  module_name: string;
  room_code: string;
  lecturer_name?: string;
}

interface DayGroup {
  day: string;
  sessions: Session[];
}

interface ExamRun {
  run_id: number;
  message: string;
  days: DayGroup[];
  total: number;
}

interface MyExamsResponse {
  exam?: ExamRun;
  test?: ExamRun;
}

export default function MyExams() {
  const [data, setData] = useState<MyExamsResponse>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"exam" | "test">("exam");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<MyExamsResponse>("/portal/my-exams");
        setData(res.data);
        // Auto-select tab with data
        if (!res.data.exam?.total && res.data.test?.total) {
          setTab("test");
        }
      } catch (e: any) {
        setError(e.response?.data?.detail || "Failed to load exams");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const token = localStorage.getItem("aviu_token");
  const downloadUrl = (fmt: string) =>
    `http://localhost:8000/api/v1/portal/my-timetable/${fmt}?token=${token}`;

  if (loading) return <div className="p-8 text-aviu-700">Loading exams...</div>;

  const current = data[tab];
  const tabs = [
    { id: "exam" as const, label: " Final Exams", total: data.exam?.total || 0 },
    { id: "test" as const, label: " Tests", total: data.test?.total || 0 },
  ];

  return (
    <div>
      <PageHeader
        title="My Exams & Tests"
        subtitle="Your exam and test schedule for the semester"
        action={
          <div className="flex gap-2">
            <a href={downloadUrl("ical")} target="_blank" rel="noreferrer"
              className="bg-aviu-800 hover:bg-aviu-900 text-white px-3 py-2 rounded-lg text-sm font-medium">
               iCal
            </a>
            <a href={downloadUrl("pdf")} target="_blank" rel="noreferrer"
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm font-medium">
               PDF
            </a>
            <a href={downloadUrl("excel")} target="_blank" rel="noreferrer"
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-medium">
               Excel
            </a>
          </div>
        }
      />

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 text-yellow-800">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={
              "px-4 py-2 font-medium text-sm border-b-2 -mb-px transition " +
              (tab === t.id
                ? "border-aviu-800 text-aviu-800"
                : "border-transparent text-gray-500 hover:text-aviu-700")
            }
          >
            {t.label} <span className="opacity-60">({t.total})</span>
          </button>
        ))}
      </div>

      {!current || current.total === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-500">
          <div className="text-5xl mb-3">{tab === "exam" ? "" : ""}</div>
          <p>No {tab === "exam" ? "exams" : "tests"} scheduled yet.</p>
          <p className="text-sm text-gray-400 mt-2">
            Check back after the registrar publishes the {tab === "exam" ? "exam" : "test"} timetable.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {current.days.map((d) => (
            <div key={d.day} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-aviu-50 px-5 py-3 border-b flex items-center justify-between">
                <h2 className="font-bold text-aviu-900"> {d.day}</h2>
                <span className="text-xs text-gray-500">
                  {d.sessions.length} {d.sessions.length === 1 ? "session" : "sessions"}
                </span>
              </div>
              <div className="divide-y">
                {d.sessions.map((s, i) => (
                  <div key={i} className="p-4 hover:bg-aviu-50 flex items-center gap-4">
                    <div className="bg-aviu-800 text-white rounded-lg px-3 py-2 text-center min-w-[90px]">
                      <div className="font-bold text-lg">{s.start_time}</div>
                      <div className="text-xs opacity-80">to {s.end_time}</div>
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-aviu-900">{s.module_code}</div>
                      <div className="text-sm text-gray-600">{s.module_name}</div>
                    </div>
                    <div className="text-right text-sm">
                      <div className="text-gray-700"> {s.room_code}</div>
                      {s.lecturer_name && <div className="text-gray-500 text-xs"> {s.lecturer_name}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
