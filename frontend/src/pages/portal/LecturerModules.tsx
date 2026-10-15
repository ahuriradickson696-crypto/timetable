import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../components/ui/Toast";
import { TableSkeleton } from "../../components/ui/Skeleton";

interface ModuleRow {
  code: string;
  name: string;
  credit_units: number | null;
  contact_hours_per_week: number | null;
  preferred_room_type: string | null;
  is_cross_cutting: boolean;
  cohorts: string[];
  activity_count: number;
}

export default function LecturerModules() {
  const toast = useToast();
  const [modules, setModules] = useState<ModuleRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ModuleRow[]>("/portal/my-modules")
      .then((res) => setModules(res.data))
      .catch((e: any) => {
        const msg = e.response?.data?.detail || "Failed to load modules";
        toast.show("err", msg);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalCU = modules.reduce((sum, m) => sum + (m.credit_units || 0), 0);
  const totalHours = modules.reduce((sum, m) => sum + (m.contact_hours_per_week || 0), 0);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          My Modules
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Every module you teach this semester.
        </p>
      </div>

      {loading ? (
        <TableSkeleton rows={5} />
      ) : modules.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center text-gray-500 dark:text-gray-400">
          <div className="text-lg font-semibold mb-1">No modules assigned</div>
          <p className="text-sm">
            Once the timetable has been generated, your modules will appear here.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Stat label="Modules" value={modules.length} />
            <Stat label="Credit Units" value={totalCU} />
            <Stat label="Contact Hours" value={totalHours + " / wk"} />
            <Stat label="Cohorts" value={new Set(modules.flatMap((m) => m.cohorts)).size} />
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            <table className="w-full">
              <thead className="bg-aviu-50 dark:bg-aviu-900/30">
                <tr className="text-left text-xs font-semibold uppercase tracking-wider text-aviu-800 dark:text-aviu-300">
                  <th className="px-5 py-3">Module</th>
                  <th className="px-5 py-3">CU</th>
                  <th className="px-5 py-3">Hours/week</th>
                  <th className="px-5 py-3">Room type</th>
                  <th className="px-5 py-3">Cohorts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {modules.map((m) => (
                  <tr key={m.code} className="hover:bg-aviu-50 dark:hover:bg-aviu-900/20">
                    <td className="px-5 py-3">
                      <div className="font-mono text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {m.code}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{m.name}</div>
                    </td>
                    <td className="px-5 py-3 text-sm">{m.credit_units ?? "-"}</td>
                    <td className="px-5 py-3 text-sm">{m.contact_hours_per_week ?? "-"}</td>
                    <td className="px-5 py-3 text-sm">
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800">
                        {m.preferred_room_type || "-"}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs">
                      {m.cohorts.length === 0 ? (
                        <span className="text-gray-400">-</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {m.cohorts.map((c) => (
                            <span
                              key={c}
                              className="inline-block px-2 py-0.5 rounded text-xs bg-aviu-100 dark:bg-aviu-900/40 text-aviu-800 dark:text-aviu-300 font-mono"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
      <div className="text-2xl font-bold text-aviu-800 dark:text-aviu-300">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{label}</div>
    </div>
  );
}