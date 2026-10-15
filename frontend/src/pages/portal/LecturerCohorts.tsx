import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../components/ui/Toast";
import { TableSkeleton } from "../../components/ui/Skeleton";

interface CohortRow {
  id: string;
  programme_code: string | null;
  programme_name: string | null;
  year_level: number | null;
  mode: string | null;
  intake: string | null;
  academic_year: string | null;
  semester: number | null;
  estimated_students: number | null;
  modules: string[];
  student_count: number;
}

export default function LecturerCohorts() {
  const toast = useToast();
  const [cohorts, setCohorts] = useState<CohortRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<CohortRow[]>("/portal/my-cohorts")
      .then((res) => setCohorts(res.data))
      .catch((e: any) => {
        const msg = e.response?.data?.detail || "Failed to load cohorts";
        toast.show("err", msg);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          My Cohorts
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Student groups you teach this semester.
        </p>
      </div>

      {loading ? (
        <TableSkeleton rows={3} />
      ) : cohorts.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center text-gray-500 dark:text-gray-400">
          <div className="text-lg font-semibold mb-1">No cohorts assigned</div>
          <p className="text-sm">
            Once the timetable has been generated, your cohorts will appear here.
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {cohorts.map((c) => (
            <div
              key={c.id}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-mono font-bold text-aviu-800 dark:text-aviu-300 text-sm">
                    {c.id}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {c.programme_name || c.programme_code}
                  </div>
                </div>
                <span className="px-2 py-1 rounded-full bg-aviu-100 dark:bg-aviu-900/40 text-aviu-800 dark:text-aviu-300 text-xs font-semibold">
                  {c.student_count} students
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400 mb-4">
                <div>Year {c.year_level}</div>
                <div>Semester {c.semester}</div>
                <div>{c.mode}</div>
                <div>{c.intake} {c.academic_year}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                  Modules ({c.modules.length})
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.modules.map((m) => (
                    <span
                      key={m}
                      className="inline-block px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}