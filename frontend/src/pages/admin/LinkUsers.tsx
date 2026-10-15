import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../components/ui/Toast";

interface UnlinkedUser {
  id: number;
  email: string;
  full_name: string;
}

interface Unlinked {
  students: UnlinkedUser[];
  lecturers: UnlinkedUser[];
}

interface Cohort {
  id: string;
  programme_code: string;
  year_level: number;
  mode: string;
  intake: string;
  academic_year: string;
}

interface Lecturer {
  id: string;
  full_name: string;
}

export default function LinkUsers() {
  const toast = useToast();
  const [data, setData] = useState<Unlinked>({ students: [], lecturers: [] });
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [u, c, l] = await Promise.all([
        api.get<Unlinked>("/admin/link/unlinked"),
        api.get<Cohort[]>("/cohorts"),
        api.get<Lecturer[]>("/lecturers"),
      ]);
      setData(u.data);
      setCohorts(c.data);
      setLecturers(l.data);
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const linkStudent = async (userId: number, cohortId: string) => {
    if (!cohortId) return;
    setBusyId(userId);
    try {
      await api.post("/admin/link/student", { user_id: userId, cohort_id: cohortId });
      toast.show("ok", "Student linked to " + cohortId);
      await load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Link failed");
    } finally {
      setBusyId(null);
    }
  };

  const linkLecturer = async (userId: number, lecturerId: string) => {
    if (!lecturerId) return;
    setBusyId(userId);
    try {
      await api.post("/admin/link/lecturer", { user_id: userId, lecturer_id: lecturerId });
      toast.show("ok", "Lecturer linked to " + lecturerId);
      await load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Link failed");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">
          Link User Accounts
        </h1>
        <p className="text-gray-500">
          Assign cohorts to new students and match lecturers to their records.
        </p>
      </div>

      {loading ? (
        <div className="text-aviu-700">Loading...</div>
      ) : (
        <>
          {/* Students */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                Students Awaiting Cohort
              </h2>
              <span className="text-sm text-gray-500">
                {data.students.length}
              </span>
            </div>
            {data.students.length === 0 ? (
              <div className="text-center py-6 text-gray-500 text-sm">
                All students have a cohort.
              </div>
            ) : (
              <div className="space-y-2">
                {data.students.map((u) => (
                  <div key={u.id}
                    className="flex flex-col md:flex-row md:items-center gap-3 p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{u.full_name}</div>
                      <div className="text-xs text-gray-500">{u.email}</div>
                    </div>
                    <select
                      onChange={(e) => linkStudent(u.id, e.target.value)}
                      disabled={busyId === u.id}
                      defaultValue=""
                      className="border rounded-lg px-3 py-2 text-sm bg-white min-w-[220px]"
                    >
                      <option value="" disabled>-- assign cohort --</option>
                      {cohorts.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.id} ({c.programme_code} Y{c.year_level})
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Lecturers */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                Lecturers Awaiting Record Link
              </h2>
              <span className="text-sm text-gray-500">
                {data.lecturers.length}
              </span>
            </div>
            {data.lecturers.length === 0 ? (
              <div className="text-center py-6 text-gray-500 text-sm">
                All lecturers are linked.
              </div>
            ) : (
              <div className="space-y-2">
                {data.lecturers.map((u) => (
                  <div key={u.id}
                    className="flex flex-col md:flex-row md:items-center gap-3 p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{u.full_name}</div>
                      <div className="text-xs text-gray-500">{u.email}</div>
                    </div>
                    <select
                      onChange={(e) => linkLecturer(u.id, e.target.value)}
                      disabled={busyId === u.id}
                      defaultValue=""
                      className="border rounded-lg px-3 py-2 text-sm bg-white min-w-[220px]"
                    >
                      <option value="" disabled>-- match lecturer --</option>
                      {lecturers.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.id} - {l.full_name}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}