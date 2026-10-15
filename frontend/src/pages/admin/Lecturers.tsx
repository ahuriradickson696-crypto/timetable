import { useEffect, useState } from "react";
import { api, Lecturer, CourseUnit } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  id: "", full_name: "", max_hours_per_week: 16,
  preferred_mode: "Both", email: "", active: true, notes: "",
};

export default function Lecturers() {
  const toast = useToast();
  const [items, setItems] = useState<any[]>([]);
  const [units, setUnits] = useState<CourseUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [canTeach, setCanTeach] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<any>(null);
  const [unitFilter, setUnitFilter] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [l, u] = await Promise.all([
        api.get<any[]>("/lecturers"),
        api.get<CourseUnit[]>("/course-units"),
      ]);
      setItems(l.data);
      setUnits(u.data);
    } catch { toast.show("err", "Failed to load"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => {
    setForm(EMPTY);
    setCanTeach([]);
    setEditingId(null);
    setError("");
    setShowForm(true);
  };

  const startEdit = (l: any) => {
    setForm({ ...l });
    setCanTeach(l.can_teach_modules || []);
    setEditingId(l.id);
    setError("");
    setShowForm(true);
  };

  const toggleModule = (code: string) => {
    setCanTeach((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = { ...form, can_teach_modules: canTeach };
      if (editingId) {
        const { id, ...update } = payload;
        await api.patch(`/lecturers/${editingId}`, update);
        toast.show("ok", "Lecturer updated");
      } else {
        await api.post("/lecturers", payload);
        toast.show("ok", "Lecturer created");
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
      await api.delete(`/lecturers/${toDelete.id}`);
      toast.show("ok", `Deleted ${toDelete.id}`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const filteredUnits = unitFilter
    ? units.filter((u) =>
        u.code.toLowerCase().includes(unitFilter.toLowerCase()) ||
        u.name.toLowerCase().includes(unitFilter.toLowerCase())
      )
    : units;

  const columns: Column<any>[] = [
    { key: "id", label: "ID", sortable: true },
    { key: "full_name", label: "Name", sortable: true },
    { key: "max_hours_per_week", label: "Max hrs/wk", sortable: true },
    { key: "preferred_mode", label: "Mode", sortable: true },
    { key: "email", label: "Email" },
    {
      key: "can_teach_modules", label: "Can Teach",
      render: (l) => {
        const m = l.can_teach_modules || [];
        if (m.length === 0) return <span className="text-gray-400 text-xs">None</span>;
        return (
          <span className="text-xs">
            <span className="font-medium">{m.length}</span> module{m.length !== 1 ? "s" : ""}
          </span>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title="Lecturers"
        subtitle={`${items.length} teaching staff`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Lecturer
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">{editingId ? `Edit ${editingId}` : "New Lecturer"}</h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Lecturer ID (e.g. LECT-022)" value={form.id}
              onChange={(e) => setForm({ ...form, id: e.target.value })}
              disabled={!!editingId}
              className="border rounded-lg px-3 py-2 disabled:bg-gray-100" />
            <input required placeholder="Full name" value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Max hours/week" value={form.max_hours_per_week}
              onChange={(e) => setForm({ ...form, max_hours_per_week: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.preferred_mode}
              onChange={(e) => setForm({ ...form, preferred_mode: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Day</option><option>Weekend</option><option>Both</option>
            </select>
            <input type="email" placeholder="Email" value={form.email || ""}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input placeholder="Unavailable days (comma-separated)" value={form.unavailable_days || ""}
              onChange={(e) => setForm({ ...form, unavailable_days: e.target.value })}
              className="border rounded-lg px-3 py-2" />

            {/* Can teach modules */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Can teach modules {canTeach.length > 0 && `(${canTeach.length} selected)`}
              </label>
              <input
                type="text"
                placeholder="Filter modules by code or name..."
                value={unitFilter}
                onChange={(e) => setUnitFilter(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 mb-2"
              />
              <div className="max-h-60 overflow-y-auto border rounded-lg p-2 bg-gray-50 flex flex-wrap gap-1.5">
                {filteredUnits.slice(0, 200).map((u) => {
                  const selected = canTeach.includes(u.code);
                  return (
                    <button
                      key={u.code}
                      type="button"
                      onClick={() => toggleModule(u.code)}
                      title={u.name}
                      className={
                        "px-2 py-1 rounded text-xs font-medium transition " +
                        (selected
                          ? "bg-aviu-800 text-white"
                          : "bg-white border border-gray-300 text-gray-700 hover:border-aviu-500")
                      }
                    >
                      {u.code}
                    </button>
                  );
                })}
                {filteredUnits.length === 0 && (
                  <p className="text-xs text-gray-500 p-2">No modules match "{unitFilter}"</p>
                )}
              </div>
              {canTeach.length > 0 && (
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-xs text-gray-500">
                    {canTeach.slice(0, 5).join(", ")}
                    {canTeach.length > 5 && ` +${canTeach.length - 5} more`}
                  </p>
                  <button type="button" onClick={() => setCanTeach([])}
                    className="text-xs text-red-600 hover:underline">
                    Clear all
                  </button>
                </div>
              )}
            </div>
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
        emptyMessage="No lecturers yet."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(l) => setToDelete(l)}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete lecturer?"
        message={<p>Delete <strong>{toDelete?.id}</strong>  {toDelete?.full_name}?</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
