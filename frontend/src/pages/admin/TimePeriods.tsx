import { useEffect, useState } from "react";
import { api, TimePeriod } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  period_id: "", day: "Monday", start_time: "08:00",
  end_time: "09:00", mode: "Day", is_break: false, order_index: 0,
};

export default function TimePeriods() {
  const toast = useToast();
  const [items, setItems] = useState<TimePeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterMode, setFilterMode] = useState<string>("Day");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<TimePeriod | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<TimePeriod[]>("/time-periods");
      setItems(res.data);
    } catch { toast.show("err", "Failed to load"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => { setForm(EMPTY); setEditingId(null); setError(""); setShowForm(true); };
  const startEdit = (p: TimePeriod) => {
    setForm({ ...p });
    setEditingId(p.id);
    setError("");
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        const { id, ...update } = form;
        await api.patch(`/time-periods/${editingId}`, update);
        toast.show("ok", "Time period updated");
      } else {
        await api.post("/time-periods", form);
        toast.show("ok", "Time period created");
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
      await api.delete(`/time-periods/${toDelete.id}`);
      toast.show("ok", "Time period deleted");
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const modes = ["Day", "Weekend", "Exam", "Test"];
  const filtered = filterMode ? items.filter((p) => p.mode === filterMode) : items;

  const modeBadge = (mode: string) => {
    const colors: any = {
      Day: "bg-blue-100 text-blue-700",
      Weekend: "bg-green-100 text-green-700",
      Exam: "bg-purple-100 text-purple-700",
      Test: "bg-yellow-100 text-yellow-700",
    };
    return <span className={"px-2 py-0.5 rounded text-xs font-medium " + (colors[mode] || "")}>{mode}</span>;
  };

  const columns: Column<TimePeriod>[] = [
    { key: "mode", label: "Mode", sortable: true, render: (p) => modeBadge(p.mode) },
    { key: "period_id", label: "Period ID", sortable: true },
    { key: "day", label: "Day", sortable: true },
    { key: "start_time", label: "Start", sortable: true },
    { key: "end_time", label: "End", sortable: true },
    {
      key: "is_break", label: "Break",
      render: (p) => p.is_break ? " Yes" : "",
    },
    { key: "order_index", label: "Order", sortable: true },
  ];

  const counts: Record<string, number> = {};
  modes.forEach((m) => { counts[m] = items.filter((i) => i.mode === m).length; });

  return (
    <div>
      <PageHeader
        title="Time Structure"
        subtitle={`${items.length} periods across ${Object.keys(counts).filter((k) => counts[k] > 0).length} modes`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Period
          </button>
        }
      />

      <div className="flex gap-2 mb-4 flex-wrap">
        {modes.map((m) => (
          <button
            key={m}
            onClick={() => setFilterMode(m)}
            className={
              "px-4 py-2 rounded-lg text-sm font-medium transition " +
              (filterMode === m
                ? "bg-aviu-800 text-white"
                : "bg-white border border-gray-200 text-gray-700 hover:bg-aviu-50")
            }
          >
            {m} <span className="opacity-60">({counts[m]})</span>
          </button>
        ))}
        <button
          onClick={() => setFilterMode("")}
          className={
            "px-4 py-2 rounded-lg text-sm font-medium transition " +
            (filterMode === "" ? "bg-aviu-800 text-white" : "bg-white border border-gray-200 text-gray-700 hover:bg-aviu-50")
          }
        >
          All <span className="opacity-60">({items.length})</span>
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">
            {editingId ? `Edit Period #${editingId}` : "New Time Period"}
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <input required placeholder="Period ID (e.g. D-P1)" value={form.period_id}
              onChange={(e) => setForm({ ...form, period_id: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.day} onChange={(e) => setForm({ ...form, day: e.target.value })}
              className="border rounded-lg px-3 py-2">
              {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map((d) =>
                <option key={d}>{d}</option>
              )}
            </select>
            <select value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })}
              className="border rounded-lg px-3 py-2">
              {modes.map((m) => <option key={m}>{m}</option>)}
            </select>
            <input required placeholder="Start (HH:MM)" value={form.start_time}
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input required placeholder="End (HH:MM)" value={form.end_time}
              onChange={(e) => setForm({ ...form, end_time: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Order" value={form.order_index}
              onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <label className="flex items-center gap-2 col-span-3">
              <input type="checkbox" checked={form.is_break}
                onChange={(e) => setForm({ ...form, is_break: e.target.checked })} />
              Mark as break period (never used for teaching)
            </label>
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
        data={filtered}
        loading={loading}
        emptyMessage={"No " + filterMode + " periods defined yet."}
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(p) => setToDelete(p)}
        pageSize={20}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete time period?"
        message={<p>Delete <strong>{toDelete?.period_id}</strong> on {toDelete?.day}?</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
