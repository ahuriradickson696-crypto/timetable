import { useEffect, useState } from "react";
import { api, TimetableCell } from "../../api/client";
import PageHeader from "../../components/PageHeader";

export default function MySchedule() {
  const [cells, setCells] = useState<TimetableCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<TimetableCell[]>("/portal/my-timetable");
        setCells(res.data);
      } catch (e: any) {
        setError(e.response?.data?.detail || "Failed to load schedule");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const downloadIcal = () => {
    const token = localStorage.getItem("aviu_token");
    window.open(
      `http://localhost:8000/api/v1/portal/my-timetable/ical?token=${token}`,
      "_blank"
    );
  };

  const sorted = [...cells].sort((a, b) =>
    a.day.localeCompare(b.day) || a.start_time.localeCompare(b.start_time)
  );

  if (loading) return <div className="text-aviu-700">Loading schedule...</div>;

  return (
    <div>
      <PageHeader
        title="My Teaching Schedule"
        subtitle="All your classes this week"
        action={
          <button
            onClick={downloadIcal}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
             Add to Calendar (iCal)
          </button>
        }
      />

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 text-yellow-800">
          {error}
        </div>
      )}

      {cells.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-500">
          You have no classes scheduled yet.
        </div>
      ) : (
        <div className="grid gap-4">
          {sorted.map((c, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="bg-aviu-800 text-white text-xs font-bold px-2 py-1 rounded">
                      {c.day}
                    </span>
                    <span className="text-sm font-medium text-gray-700">
                      {c.start_time} - {c.end_time}
                    </span>
                  </div>
                  <div className="font-bold text-aviu-900 text-lg">{c.module_code}</div>
                  <div className="text-gray-600">{c.module_name}</div>
                  <div className="flex gap-4 mt-3 text-sm text-gray-500">
                    <span> {c.room_code}</span>
                    <span> {c.cohort_id}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
