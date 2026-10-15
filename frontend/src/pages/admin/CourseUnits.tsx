import { useEffect, useState } from "react";
import { api, CourseUnit, Programme } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  code: "", name: "", credit_units: 3, contact_hours_per_week: 3,
  normal_year: 1, is_cross_cutting: false, preferred_room_type: "Lecture",
  owning_school: "", active: true, notes: "",
};

export default function CourseUnits() {
  const toast = useToast();
  const [items, setItems] = useState<any[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [sharedProgs, setSharedProgs] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [c, p] = await Promise.all([
        api.get<any[]>("/course-units"),
        api.get<Programme[]>("/programmes"),
      ]);
      setItems(c.data);
      setProgrammes(p.data);
    } catch { toast.show("err", "Failed to load"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => {
    setForm(EMPTY);
    setSharedProgs([]);
    setEditingCode(null);
    setError("");
    setShowForm(true);
  };

  const startEdit = (c: any) => {
    setForm({ ...c });
    setSharedProgs(c.shared_across_programmes || []);
    setEditingCode(c.code);
    setError("");
    setShowForm(true);
  };

  const toggleProg = (code: string) => {
    setSharedProgs((prev) =>
      prev.includes(code) ? prev.filter((p) => p !== code) : [...prev, code]
    );
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = { ...form, shared_across_programmes: sharedProgs };
      if (editingCode) {
        const { code, ...update } = payload;
        await api.patch(`/course-units/${editingCode}`, update);
        toast.show("ok", "Course unit updated");
      } else {
        await api.post("/course-units", payload);
        toast.show("ok", "Course unit created");
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
      await api.delete(`/course-units/${toDelete.code}`);
      toast.show("ok", `Deleted ${toDelete.code}`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const columns: Column<any>[] = [
    { key: "code", label: "Code", sortable: true },
    { key: "name", label: "Name", sortable: true },
    { key: "credit_units", label: "Credits", sortable: true },
    { key: "contact_hours_per_week", label: "Hrs/Wk", sortable: true },
    { key: "preferred_room_type", label: "Room Type", sortable: true },
    {
      key: "is_cross_cutting", label: "Cross",
      render: (c) => c.is_cross_cutting ? "" : ""
    },
    {
      key: "shared_across_programmes", label: "Shared With",
      render: (c) => {
        const p = c.shared_across_programmes || [];
        if (p.length === 0) return <span className="text-gray-300"></span>;
        return (
          <div className="flex gap-1 flex-wrap">
            {p.slice(0, 4).map((code: string) => (
              <span key={code} className="px-1.5 py-0.5 rounded text-xs bg-aviu-100 text-aviu-900 font-medium">
                {code}
              </span>
            ))}
            {p.length > 4 && <span className="text-xs text-gray-500">+{p.length - 4}</span>}
          </div>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title="Course Units"
        subtitle={`${items.length} modules across all programmes`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Course Unit
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">{editingCode ? `Edit ${editingCode}` : "New Course Unit"}</h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Code (e.g. BSE ED 71101)" value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              disabled={!!editingCode}
              className="border rounded-lg px-3 py-2 col-span-2 disabled:bg-gray-100" />
            <input required placeholder="Module name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border rounded-lg px-3 py-2 col-span-2" />
            <input type="number" placeholder="Credits" value={form.credit_units}
              onChange={(e) => setForm({ ...form, credit_units: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Contact hours/week" value={form.contact_hours_per_week}
              onChange={(e) => setForm({ ...form, contact_hours_per_week: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Normal year" value={form.normal_year}
              onChange={(e) => setForm({ ...form, normal_year: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.preferred_room_type}
              onChange={(e) => setForm({ ...form, preferred_room_type: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Lecture</option><option>Computer Lab</option><option>Science Lab</option>
              <option>Clinical Lab</option><option>Seminar</option><option>Any</option>
            </select>
            <input placeholder="Owning school" value={form.owning_school}
              onChange={(e) => setForm({ ...form, owning_school: e.target.value })}
              className="border rounded-lg px-3 py-2 col-span-2" />
            <label className="flex items-center gap-2 col-span-2">
              <input type="checkbox" checked={form.is_cross_cutting}
                onChange={(e) => setForm({ ...form, is_cross_cutting: e.target.checked })} />
              Cross-cutting module (shared across programmes)
            </label>

            {/* Shared programmes editor */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Shared across programmes {sharedProgs.length > 0 && `(${sharedProgs.length})`}
              </label>
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto border rounded-lg p-3 bg-gray-50">
                {programmes.map((p) => {
                  const selected = sharedProgs.includes(p.code);
                  return (
                    <button
                      key={p.code}
                      type="button"
                      onClick={() => toggleProg(p.code)}
                      className={
                        "px-3 py-1.5 rounded-lg text-xs font-medium transition " +
                        (selected
                          ? "bg-aviu-800 text-white"
                          : "bg-white border border-gray-300 text-gray-700 hover:border-aviu-500")
                      }
                    >
                      {selected && " "}{p.code}
                    </button>
                  );
                })}
              </div>
              {sharedProgs.length > 0 && (
                <p className="text-xs text-gray-500 mt-2">
                  {sharedProgs.join(", ")}
                </p>
              )}
            </div>
          </div>
          {error && <p className="text-red-600 text-sm mt-3">{error}</p>}
          <div className="flex gap-2 mt-4">
            <button type="submit" className="bg-aviu-800 text-white px-4 py-2 rounded-lg">
              {editingCode ? "Save Changes" : "Create"}
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
        emptyMessage="No course units yet."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(c) => setToDelete(c)}
        pageSize={20}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete course unit?"
        message={<p>Delete <strong>{toDelete?.code}</strong>  {toDelete?.name}?</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
