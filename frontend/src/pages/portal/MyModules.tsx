import { useEffect, useState } from "react";
import { api, CourseUnit } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

interface Enrollment {
  id: number;
  module_code: string;
  module_name?: string;
  credit_units?: number;
  preferred_room_type?: string;
  academic_year: string;
  semester: number;
  status: string;
  is_locked: boolean;
  enrolled_at: string;
}

interface PortalMe {
  id: number;
  full_name: string;
  role: string;
  cohort_id?: string;
  cohort_name?: string;
  programme_name?: string;
  academic_year?: string;
  semester?: number;
  enrollment_count?: number;
  enrollment_credits?: number;
}

export default function MyModules() {
  const toast = useToast();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [me, setMe] = useState<PortalMe | null>(null);
  const [allModules, setAllModules] = useState<CourseUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [filter, setFilter] = useState("");
  const [toDrop, setToDrop] = useState<Enrollment | null>(null);
  const [working, setWorking] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [e, m, u] = await Promise.all([
        api.get<Enrollment[]>("/enrollments/me"),
        api.get<PortalMe>("/portal/me"),
        api.get<CourseUnit[]>("/course-units"),
      ]);
      setEnrollments(e.data);
      setMe(m.data);
      setAllModules(u.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const autoEnroll = async () => {
    setWorking(true);
    try {
      const res = await api.post("/enrollments/me/auto-enroll");
      toast.show("ok", "Enrolled in " + res.data.added + " new modules");
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Auto-enroll failed");
    } finally {
      setWorking(false);
    }
  };

  const enrollOne = async (moduleCode: string) => {
    try {
      await api.post("/enrollments/me", {
        module_code: moduleCode,
        academic_year: me?.academic_year || "2026/2027",
        semester: me?.semester || 1,
      });
      toast.show("ok", "Enrolled in " + moduleCode);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Enroll failed");
    }
  };

  const confirmDrop = async () => {
    if (!toDrop) return;
    try {
      await api.delete(`/enrollments/me/${encodeURIComponent(toDrop.module_code)}?academic_year=${toDrop.academic_year}&semester=${toDrop.semester}`);
      toast.show("ok", "Dropped " + toDrop.module_code);
      setToDrop(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Drop failed");
    }
  };

  const enrolledCodes = new Set(enrollments.map((e) => e.module_code));
  const filteredModules = allModules
    .filter((u) => !enrolledCodes.has(u.code))
    .filter((u) =>
      filter
        ? u.code.toLowerCase().includes(filter.toLowerCase()) ||
          u.name.toLowerCase().includes(filter.toLowerCase())
        : true
    )
    .slice(0, 100);

  const totalCredits = enrollments.reduce((sum, e) => sum + (e.credit_units || 0), 0);

  if (loading) return <div className="p-8 text-aviu-700">Loading modules...</div>;

  return (
    <div>
      <PageHeader
        title="My Modules"
        subtitle={`${enrollments.length} modules enrolled - ${totalCredits} credits`}
        action={
          <div className="flex gap-2">
            <button
              onClick={autoEnroll}
              disabled={working}
              className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-400 text-white px-4 py-2 rounded-lg font-medium"
            >
              {working ? "Working..." : "Auto-Enroll from Cohort"}
            </button>
            <a
              href="/register"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium inline-flex items-center"
            >
              Update Registration
            </a>
            <button
              onClick={() => setShowPicker(!showPicker)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
            >
              Add Module
            </button>
          </div>
        }
      />

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 text-yellow-800">
          {error}
        </div>
      )}

      {me?.academic_year && (
        <div className="bg-aviu-50 border border-aviu-200 rounded-xl p-4 mb-6 text-sm">
          <div className="font-semibold text-aviu-900">
            {me.cohort_name} - {me.programme_name}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            Semester {me.semester} - {me.academic_year}
          </div>
        </div>
      )}

      {showPicker && (
        <div className="bg-white rounded-xl border-2 border-green-300 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg">Add a Module</h2>
            <button onClick={() => setShowPicker(false)} className="text-gray-500 hover:text-gray-800 text-2xl">x</button>
          </div>
          <input
            type="text"
            placeholder="Filter by code or name..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 mb-4"
          />
          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredModules.length === 0 && (
              <p className="text-sm text-gray-500 italic">No modules available to add.</p>
            )}
            {filteredModules.map((u) => (
              <div key={u.code} className="flex items-center justify-between p-3 border rounded-lg hover:bg-aviu-50">
                <div className="flex-1">
                  <div className="font-semibold text-sm">{u.code}</div>
                  <div className="text-xs text-gray-600">{u.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {u.credit_units} credits - {u.preferred_room_type}
                  </div>
                </div>
                <button
                  onClick={() => enrollOne(u.code)}
                  className="bg-aviu-800 hover:bg-aviu-900 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
                >
                  Enroll
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-4 bg-aviu-50 border-b flex items-center justify-between">
          <h2 className="font-bold text-aviu-900">My Enrolled Modules</h2>
          <span className="text-sm text-gray-600">
            {enrollments.length} modules - {totalCredits} credits
          </span>
        </div>

        {enrollments.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <p className="mb-4">You have not enrolled in any modules yet.</p>
            <button
              onClick={autoEnroll}
              disabled={working}
              className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-400 text-white px-6 py-2 rounded-lg font-medium"
            >
              {working ? "Working..." : "Auto-Enroll from Cohort"}
            </button>
            <p className="text-xs text-gray-400 mt-3">
              This will enroll you in all modules from your cohort's curriculum.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left p-3 text-sm font-semibold">Code</th>
                <th className="text-left p-3 text-sm font-semibold">Module Name</th>
                <th className="text-right p-3 text-sm font-semibold">Credits</th>
                <th className="text-left p-3 text-sm font-semibold">Room Type</th>
                <th className="text-center p-3 text-sm font-semibold">Status</th>
                <th className="text-right p-3 text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {enrollments.map((e) => (
                <tr key={e.id} className="border-b hover:bg-aviu-50">
                  <td className="p-3 text-sm font-mono font-medium">{e.module_code}</td>
                  <td className="p-3 text-sm">{e.module_name || "-"}</td>
                  <td className="p-3 text-sm text-right">{e.credit_units || 0}</td>
                  <td className="p-3 text-sm text-gray-600">{e.preferred_room_type || "-"}</td>
                  <td className="p-3 text-center">
                    {e.is_locked ? (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                        Locked
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                        Enrolled
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    {!e.is_locked && (
                      <button
                        onClick={() => setToDrop(e)}
                        className="text-red-600 hover:underline text-sm font-medium"
                      >
                        Drop
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmDialog
        open={!!toDrop}
        title="Drop module?"
        message={
          <p>
            Are you sure you want to drop <strong>{toDrop?.module_code}</strong> - {toDrop?.module_name}?
            <br />
            <span className="text-sm text-gray-500">
              You can re-enroll later if needed.
            </span>
          </p>
        }
        confirmLabel="Drop"
        danger
        onConfirm={confirmDrop}
        onCancel={() => setToDrop(null)}
      />
    </div>
  );
}