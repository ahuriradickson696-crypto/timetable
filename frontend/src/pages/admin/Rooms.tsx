import { useEffect, useState } from "react";
import { api, Room } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

const EMPTY = {
  code: "", name: "", capacity: 40, room_type: "Lecture",
  building: "", available_modes: "Both", active: true,
};

export default function Rooms() {
  const toast = useToast();
  const [items, setItems] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<Room | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Room[]>("/rooms");
      setItems(res.data);
    } catch {
      toast.show("err", "Failed to load rooms");
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => { setForm(EMPTY); setEditingCode(null); setError(""); setShowForm(true); };
  const startEdit = (r: Room) => { setForm({ ...r }); setEditingCode(r.code); setError(""); setShowForm(true); };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (editingCode) {
        const { code, ...update } = form;
        await api.patch(`/rooms/${editingCode}`, update);
        toast.show("ok", "Room updated");
      } else {
        await api.post("/rooms", form);
        toast.show("ok", "Room created");
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
      await api.delete(`/rooms/${toDelete.code}`);
      toast.show("ok", `Room ${toDelete.code} deleted`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const columns: Column<Room>[] = [
    { key: "code", label: "Code", sortable: true },
    { key: "name", label: "Name", sortable: true },
    { key: "capacity", label: "Capacity", sortable: true },
    { key: "room_type", label: "Type", sortable: true },
    { key: "building", label: "Building", sortable: true },
    { key: "available_modes", label: "Modes", sortable: true },
  ];

  return (
    <div>
      <PageHeader
        title="Rooms & Laboratories"
        subtitle={`${items.length} physical teaching spaces`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add Room
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">{editingCode ? `Edit ${editingCode}` : "New Room"}</h2>
          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="Room code (e.g. MH-01)" value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              disabled={!!editingCode}
              className="border rounded-lg px-3 py-2 disabled:bg-gray-100" />
            <input required placeholder="Room name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input type="number" placeholder="Capacity" value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.room_type}
              onChange={(e) => setForm({ ...form, room_type: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Lecture</option><option>Computer Lab</option><option>Science Lab</option>
              <option>Clinical Lab</option><option>Seminar</option>
            </select>
            <input placeholder="Building" value={form.building}
              onChange={(e) => setForm({ ...form, building: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.available_modes}
              onChange={(e) => setForm({ ...form, available_modes: e.target.value })}
              className="border rounded-lg px-3 py-2">
              <option>Day</option><option>Weekend</option><option>Both</option>
            </select>
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
        emptyMessage="No rooms yet."
        emptyIcon=""
        onEdit={startEdit}
        onDelete={(r) => setToDelete(r)}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete room?"
        message={<p>Delete room <strong>{toDelete?.code}</strong>  {toDelete?.name}?</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
