import { useEffect, useState } from "react";
import { api, Activity, Cohort, CourseUnit, Lecturer } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  id: "", cohort_id: "", module_code: "", lecturer_id: "",
  duration_periods: 2, preferred_room_type: "Lecture",
  students: 30, split_allowed: false, joint_cohort_ids: "",
  semester: 1, intake: "Aug", academic_year: "2026/2027",
  activity_type: "teaching", notes: "",
};

export default function Activities() {
  const toast = useToast();
  const [items, setItems] = useState<Activity[]>([]);
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [units, setUnits] = useState<CourseUnit[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<Activity | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [a, c, u, l] = await Promise.all([
        api.get("/activities"), api.get("/cohorts"),
        api.get("/course-units"), api.get("/lecturers"),
      ]);
      setItems(a.data); setCohorts(c.data);
      setUnits(u.data); setLecturers(l.data);
    } catch { toast.show("err", "Failed to load"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => { setForm(EMPTY); setEditingId(null); setError(""); setShowForm(true); };
  const startEdit = (a: Activity) => {
    setForm({ ...a, joint_cohort_ids: a.joint_cohort_ids || "", notes: a.notes || "" });
    setEditingId(a.id);
    setError("");
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = { ...form, joint_cohort_ids: form.joint_cohort_ids || undefined };
      if (editingId) {
        const { id, ...update } = payload;
        await api.patch(`/activities/${editingId}`, update);
        toast.show("ok", "Activity updated");
      } else {
        await api.post("/activities", payload);
        toast.show("ok", "Activity created");
      }
      setShowForm(false);
      load();
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Save failed";
      setError(msg);
      toast.show("err", msg);
    }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    try {
      await api.delete(`/activities/${toDelete.id}`);
      toast.show("ok", `Deleted ${toDelete.id}`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const columns: Column<Activity>[] = [
    { key: "id", label: "ID", sortable: true },
    { key: "activity_type", label: "Type", sortable: true,
      render: (a) => {
        const colors: any = { teaching: "bg-blue-100 text-blue-700", test: "bg-yellow-100 text-yellow-700", exam: "bg-purple-100 text-purple-700" };
        return <span className={"px-2 py-0.5 rounded text-xs font-medium " + (colors[a.activity_type] || "")}>{a.activity_type}</span>;
      }},
    { key: "cohort_id", label: "Cohort", sortable: true },
    { key: "module_code", label: "Module", sortable: true },
    { key: "lecturer_id", label: "Lecturer", sortable: true },
    { key: "duration_periods", label: "Duration", sortable: true },
    { key: "preferred_room_type", label: "Room Type", sortable: true },
    { key: "students", label: "Students", sortable: true },
  ];

  return (
    <div>
      <PageHeader
        title="Activities"
        subtitle={`${items.length} scheduled activities`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Activity
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">{editingId ? `Edit ${editingId}` : "New Activity"}</h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Activity ID (e.g. ACT-027)" value={form.id}
              onChange={(e) => setForm({ ...form, id: e.target.value })}
              disabled={!!editingId}
              className="border rounded-lg px-3 py-2 disabled:bg-gray-100" />
            <select value={form.activity_type}
              onChange={(e) => setForm({ ...form, activity_type: e.target.value })}
              className="border rounded-lg px-3 py-2 font-medium">
              <option value="teaching"> Teaching</option>
              <option value="test"> Test</option>
              <option value="exam"> Exam</option>
            </select>
            <select required value={form.cohort_id}
              onChange={(e) => setForm({ ...form, cohort_id: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option value="">Primary cohort</option>
              {cohorts.map((c) => <option key={c.id} value={c.id}>{c.id}</option>)}
            </select>
            <select required value={form.module_code}
              onChange={(e) => setForm({ ...form, module_code: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option value="">Module</option>
              {units.slice(0, 200).map((u) => <option key={u.code} value={u.code}>{u.code}  {u.name}</option>)}
            </select>
            <select required value={form.lecturer_id}
              onChange={(e) => setForm({ ...form, lecturer_id: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option value="">Lecturer</option>
              {lecturers.map((l) => <option key={l.id} value={l.id}>{l.id}  {l.full_name}</option>)}
            </select>
            <input type="number" placeholder="Duration (periods)" value={form.duration_periods}
              onChange={(e) => setForm({ ...form, duration_periods: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Students" value={form.students}
              onChange={(e) => setForm({ ...form, students: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.preferred_room_type}
              onChange={(e) => setForm({ ...form, preferred_room_type: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Lecture</option><option>Computer Lab</option><option>Science Lab</option>
              <option>Clinical Lab</option><option>Seminar</option><option>Any</option>
            </select>
            <input placeholder="Joint cohorts (comma-separated)" value={form.joint_cohort_ids}
              onChange={(e) => setForm({ ...form, joint_cohort_ids: e.target.value })}
              className="border rounded-lg px-3 py-2 col-span-2" />
          </div>
          {error && <p className="text-red-600 text-sm mt-3">{error}</p>}
          <div className="flex gap-2 mt-4">
            <button type="submit" className="bg-aviu-800 text-white px-4 py-2 rounded-lg">
              {editingId ? "Save Changes" : "Create"}
            </button>
            <button type="button" onClick={() => setShowForm(false)}
              className="bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      )}

      <DataTable
        columns={columns}
        data={items}
        loading={loading}
        emptyMessage="No activities yet."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(a) => setToDelete(a)}
        pageSize={20}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete activity?"
        message={<p>Delete <strong>{toDelete?.id}</strong>  {toDelete?.module_code}?</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
