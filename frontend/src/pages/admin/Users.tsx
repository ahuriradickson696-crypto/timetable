import { useEffect, useState } from "react";
import { api, Cohort, Lecturer } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import DataTable, { Column } from "../../components/DataTable";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { useToast } from "../../components/ui/Toast";

interface UserRow {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  cohort_id?: string | null;
  lecturer_id?: string | null;
}

const EMPTY = {
  email: "", full_name: "", password: "",
  role: "student", cohort_id: "", lecturer_id: "",
};

export default function Users() {
  const toast = useToast();
  const [items, setItems] = useState<UserRow[]>([]);
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<any>(EMPTY);
  const [error, setError] = useState("");
  const [toDelete, setToDelete] = useState<UserRow | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [u, c, l] = await Promise.all([
        api.get("/auth/users"), api.get("/cohorts"), api.get("/lecturers"),
      ]);
      setItems(u.data); setCohorts(c.data); setLecturers(l.data);
    } catch { toast.show("err", "Failed to load"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const startCreate = () => { setForm(EMPTY); setError(""); setShowForm(true); };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload: any = {
        email: form.email,
        full_name: form.full_name,
        password: form.password,
        role: form.role,
      };
      if (form.role === "student" && form.cohort_id) payload.cohort_id = form.cohort_id;
      if (form.role === "lecturer" && form.lecturer_id) payload.lecturer_id = form.lecturer_id;
      await api.post("/auth/users", payload);
      toast.show("ok", "User created");
      setShowForm(false);
      load();
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Failed to create";
      setError(msg);
      toast.show("err", msg);
    }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    try {
      await api.delete(`/auth/users/${toDelete.id}`);
      toast.show("ok", `Deleted user #${toDelete.id}`);
      setToDelete(null);
      load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  const roleBadge = (r: string) => {
    const colors: any = {
      admin: "bg-red-100 text-red-700",
      officer: "bg-orange-100 text-orange-700",
      viewer: "bg-gray-100 text-gray-700",
      student: "bg-blue-100 text-blue-700",
      lecturer: "bg-green-100 text-green-700",
    };
    return <span className={"px-2 py-0.5 rounded text-xs font-medium capitalize " + (colors[r] || "")}>{r}</span>;
  };

  const columns: Column<UserRow>[] = [
    { key: "id", label: "ID", sortable: true },
    { key: "email", label: "Email", sortable: true },
    { key: "full_name", label: "Name", sortable: true },
    { key: "role", label: "Role", sortable: true, render: (u) => roleBadge(u.role) },
    { key: "cohort_id", label: "Cohort" },
    { key: "lecturer_id", label: "Lecturer ID" },
    { key: "is_active", label: "Active", render: (u) => u.is_active ? "" : "" },
  ];

  return (
    <div>
      <PageHeader
        title="Users"
        subtitle={`${items.length} system users  admins, officers, students, lecturers`}
        action={
          <button onClick={startCreate}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-4 py-2 rounded-lg font-medium">
            + Add User
          </button>
        }
      />

      {showForm && (
        <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold mb-4">New User</h2>
          <div className="grid grid-cols-2 gap-4">
            <input required type="email" placeholder="Email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input required placeholder="Full name" value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <input required type="password" placeholder="Password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="border rounded-lg px-3 py-2" />
            <select value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value, cohort_id: "", lecturer_id: "" })}
              className="border rounded-lg px-3 py-2">
              <option value="student"> Student</option>
              <option value="lecturer"> Lecturer</option>
              <option value="viewer"> Viewer</option>
              <option value="officer"> Timetable Officer</option>
              <option value="admin"> Admin</option>
            </select>

            {form.role === "student" && (
              <select required value={form.cohort_id}
                onChange={(e) => setForm({ ...form, cohort_id: e.target.value })}
                className="border rounded-lg px-3 py-2 col-span-2">
                <option value="">Select cohort</option>
                {cohorts.map((c) => <option key={c.id} value={c.id}>{c.id}</option>)}
              </select>
            )}
            {form.role === "lecturer" && (
              <select required value={form.lecturer_id}
                onChange={(e) => setForm({ ...form, lecturer_id: e.target.value })}
                className="border rounded-lg px-3 py-2 col-span-2">
                <option value="">Select lecturer</option>
                {lecturers.map((l) => <option key={l.id} value={l.id}>{l.id}  {l.full_name}</option>)}
              </select>
            )}
          </div>
          {error && <p className="text-red-600 text-sm mt-3">{error}</p>}
          <div className="flex gap-2 mt-4">
            <button type="submit" className="bg-aviu-800 text-white px-4 py-2 rounded-lg">Create</button>
            <button type="button" onClick={() => setShowForm(false)}
              className="bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      )}

      <DataTable
        columns={columns}
        data={items}
        loading={loading}
        emptyMessage="No users yet."
        emptyIcon=""
        onDelete={(u) => setToDelete(u)}
      />

      <ConfirmDialog
        open={!!toDelete}
        title="Delete user?"
        message={<p>Delete user <strong>{toDelete?.email}</strong>? This cannot be undone.</p>}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
