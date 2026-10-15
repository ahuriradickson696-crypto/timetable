import { useEffect, useState } from "react";
import { api, Programme } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  code: "", name: "", level: "Bachelor", school_faculty: "", duration_years: 3,
};

export default function Programmes() {
  const toast = useToast();
  const [items, setItems] = useState<Programme[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<Programme | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Programme[]>("/programmes");
      setItems(res.data);
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to load programmes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => {
    setForm(EMPTY);
    setEditingCode(null);
    setError("");
    setShowForm(true);
  };

  const startEdit = (p: Programme) => {
    setForm({ ...p });
    setEditingCode(p.code);
    setError("");
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (editingCode) {
        const { code, ...update } = form;
        await api.patch(`/programmes/${editingCode}`, update);
        toast.show("ok", "Programme updated");
      } else {
        await api.post("/programmes", form);
        toast.show("ok", "Programme created");
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
      await api.delete(`/programmes/${toDelete.code}`);
      toast.show("ok", `Programme ${toDelete.code} deleted`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const columns: Column<Programme>[] = [
    { key: "code", label: "Code", sortable: true },
    { key: "name", label: "Name", sortable: true },
    { key: "level", label: "Level", sortable: true },
    { key: "school_faculty", label: "School/Faculty", sortable: true },
    { key: "duration_years", label: "Years", sortable: true },
    {
      key: "active",
      label: "Active",
      render: (p) => p.active ? "" : "",
    },
  ];

  return (
    <div>
      <PageHeader
        title="Programmes"
        subtitle={`${items.length} NCHE-accredited programmes`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Programme
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">
            {editingCode ? `Edit ${editingCode}` : "New Programme"}
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Code (e.g. BSE)" value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              disabled={!!editingCode}
              className="border rounded-lg px-3 py-2 disabled:bg-gray-100" />
            <input required placeholder="Name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Certificate</option><option>Diploma</option><option>Bachelor</option>
              <option>PG Diploma</option><option>Masters</option>
            </select>
            <input required placeholder="School/Faculty" value={form.school_faculty}
              onChange={(e) => setForm({ ...form, school_faculty: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Duration (years)" value={form.duration_years}
              onChange={(e) => setForm({ ...form, duration_years: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
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
        emptyMessage="No programmes yet. Add your first one to get started."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(p) => setToDelete(p)}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete programme?"
        message={
          <p>
            This will permanently delete <strong>{toDelete?.code}</strong> 
            <span className="text-aviu-800 font-medium"> {toDelete?.name}</span>.
            <br />
            <span className="text-red-600 text-sm">Cohorts and activities using this programme may fail.</span>
          </p>
        }
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
