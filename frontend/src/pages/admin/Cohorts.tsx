import { useEffect, useState } from "react";
import { api, Cohort, Programme } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  id: "", programme_code: "", year_level: 1, mode: "Day",
  intake: "Aug", academic_year: "2026/2027", semester: 1,
  estimated_students: 30, status: "Active",
};

export default function Cohorts() {
  const toast = useToast();
  const [items, setItems] = useState<Cohort[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<Cohort | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [c, p] = await Promise.all([api.get("/cohorts"), api.get("/programmes")]);
      setItems(c.data);
      setProgrammes(p.data);
    } catch (e: any) {
      toast.show("err", "Failed to load cohorts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => {
    setForm(EMPTY);
    setEditingId(null);
    setError("");
    setShowForm(true);
  };

  const startEdit = (c: Cohort) => {
    setForm({ ...c });
    setEditingId(c.id);
    setError("");
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        const { id, programme_code, ...update } = form;
        await api.patch(`/cohorts/${editingId}`, update);
        toast.show("ok", "Cohort updated");
      } else {
        await api.post("/cohorts", form);
        toast.show("ok", "Cohort created");
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
      await api.delete(`/cohorts/${toDelete.id}`);
      toast.show("ok", `Cohort ${toDelete.id} deleted`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const columns: Column<Cohort>[] = [
    { key: "id", label: "Cohort ID", sortable: true },
    { key: "programme_code", label: "Programme", sortable: true },
    { key: "mode", label: "Mode", sortable: true },
    { key: "intake", label: "Intake", sortable: true },
    { key: "academic_year", label: "Year", sortable: true },
    { key: "semester", label: "Sem", sortable: true },
    { key: "estimated_students", label: "Students", sortable: true },
  ];

  return (
    <div>
      <PageHeader
        title="Cohorts"
        subtitle={`${items.length} student groups`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Cohort
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">
            {editingId ? `Edit ${editingId}` : "New Cohort"}
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Cohort ID (e.g. BSE-BC-Y1-Day-Aug2026)" value={form.id}
              onChange={(e) => setForm({ ...form, id: e.target.value })}
              disabled={!!editingId}
              className="border rounded-lg px-3 py-2 col-span-2 disabled:bg-gray-100" />
            <select required value={form.programme_code}
              onChange={(e) => setForm({ ...form, programme_code: e.target.value })}
              disabled={!!editingId}
              className="border rounded-lg px-3 py-2 disabled:bg-gray-100">
              <option value="">Select programme</option>
              {programmes.map((p) => <option key={p.code} value={p.code}>{p.code}  {p.name}</option>)}
            </select>
            <input type="number" placeholder="Year" value={form.year_level}
              onChange={(e) => setForm({ ...form, year_level: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Day</option><option>Weekend</option>
            </select>
            <select value={form.intake} onChange={(e) => setForm({ ...form, intake: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Jan</option><option>May</option><option>Aug</option>
            </select>
            <input placeholder="Academic year" value={form.academic_year}
              onChange={(e) => setForm({ ...form, academic_year: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Semester" value={form.semester}
              onChange={(e) => setForm({ ...form, semester: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Students" value={form.estimated_students}
              onChange={(e) => setForm({ ...form, estimated_students: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
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
        emptyMessage="No cohorts yet. Add the first one."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(c) => setToDelete(c)}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete cohort?"
        message={<p>Delete cohort <strong>{toDelete?.id}</strong>? This cannot be undone.</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
