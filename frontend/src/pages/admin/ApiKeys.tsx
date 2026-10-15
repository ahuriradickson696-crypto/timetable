import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../components/ui/Toast";
import { TableSkeleton } from "../../components/ui/Skeleton";

interface ApiKey {
  id: number;
  name: string;
  key: string;         // masked, e.g. aviu_abc123...xyz
  active: boolean;
  call_count: number;
  last_used_at: string | null;
  created_at: string | null;
  notes: string | null;
}

export default function ApiKeys() {
  const toast = useToast();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [justCreatedKey, setJustCreatedKey] = useState<{ name: string; key: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<ApiKey[]>("/admin/api-keys");
      setKeys(res.data);
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createKey = async () => {
    if (!newName.trim()) {
      toast.show("err", "Name is required");
      return;
    }
    setCreating(true);
    try {
      const res = await api.post("/admin/api-keys", { name: newName.trim(), notes: newNotes.trim() || null });
      setJustCreatedKey({ name: res.data.name, key: res.data.key });
      setNewName("");
      setNewNotes("");
      setShowCreate(false);
      await load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to create key");
    } finally {
      setCreating(false);
    }
  };

  const revokeKey = async (id: number, name: string) => {
    if (!confirm('Revoke "' + name + '"? Applications using this key will stop working immediately.')) return;
    try {
      await api.post("/admin/api-keys/" + id + "/revoke");
      toast.show("ok", "Key revoked");
      await load();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to revoke");
    }
  };

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.show("ok", label + " copied to clipboard");
  };

  return (
    <div>
      <div className="mb-8 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
            API Keys
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Generate keys to give external apps read access to your data.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-aviu-800 hover:bg-aviu-900 text-white font-semibold px-5 py-2.5 rounded-lg transition"
        >
          + Create API Key
        </button>
      </div>

      {/* Just-created key callout — shown once */}
      {justCreatedKey && (
        <div className="mb-6 bg-green-50 dark:bg-green-950/30 border border-green-300 dark:border-green-900/50 rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="font-semibold text-green-900 dark:text-green-300 mb-1">
                ✓ Key "{justCreatedKey.name}" created
              </div>
              <p className="text-xs text-green-800 dark:text-green-400 mb-3">
                Copy it now. For security, this key will not be shown in full again.
              </p>
              <div className="flex items-center gap-2 flex-wrap">
                <code className="bg-white dark:bg-gray-950 border border-green-300 dark:border-green-800 px-3 py-2 rounded font-mono text-xs break-all">
                  {justCreatedKey.key}
                </code>
                <button
                  onClick={() => copyText(justCreatedKey.key, "Key")}
                  className="bg-green-700 hover:bg-green-800 text-white font-semibold px-4 py-2 rounded-lg text-sm transition whitespace-nowrap"
                >
                  Copy Key
                </button>
              </div>
            </div>
            <button
              onClick={() => setJustCreatedKey(null)}
              className="text-green-700 hover:text-green-900 text-2xl leading-none"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <TableSkeleton rows={4} />
      ) : keys.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-12 text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
            No API keys yet
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Create your first key to give an external app access to your data.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-aviu-800 hover:bg-aviu-900 text-white font-semibold px-5 py-2.5 rounded-lg transition"
          >
            + Create API Key
          </button>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full">
            <thead className="bg-aviu-50 dark:bg-aviu-900/30">
              <tr className="text-left text-xs font-semibold uppercase tracking-wider text-aviu-800 dark:text-aviu-300">
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Key</th>
                <th className="px-5 py-3">Calls</th>
                <th className="px-5 py-3">Last used</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {keys.map((k) => (
                <tr key={k.id} className="hover:bg-aviu-50 dark:hover:bg-aviu-900/20">
                  <td className="px-5 py-3">
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
                      {k.name}
                    </div>
                    {k.notes && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {k.notes}
                      </div>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <code className="text-xs font-mono text-gray-600 dark:text-gray-400">
                      {k.key}
                    </code>
                  </td>
                  <td className="px-5 py-3 text-sm">{k.call_count}</td>
                  <td className="px-5 py-3 text-xs text-gray-500 dark:text-gray-400">
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                  </td>
                  <td className="px-5 py-3">
                    {k.active ? (
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                        Revoked
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {k.active && (
                      <button
                        onClick={() => revokeKey(k.id, k.name)}
                        className="text-xs px-3 py-1.5 rounded-lg bg-red-100 dark:bg-red-950/40 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-800 dark:text-red-300 font-medium"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* How to use */}
      <div className="mt-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
        <h2 className="font-bold text-gray-900 dark:text-gray-100 mb-3">How to use a key</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Send the key in the <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono text-xs">X-API-Key</code> header on every request.
        </p>
        <pre className="bg-gray-950 text-gray-100 rounded-lg p-4 overflow-auto text-xs font-mono">
{`curl -H "X-API-Key: aviu_YOUR_KEY_HERE" \\
     http://127.0.0.1:8000/api/admin/v1/dump`}
        </pre>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div
          className="fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4"
          onClick={() => setShowCreate(false)}
        >
          <div
            className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Create API Key
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Mobile App, Analytics Bot"
                  className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  rows={2}
                  className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={createKey}
                disabled={creating || !newName.trim()}
                className="px-5 py-2 rounded-lg bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold"
              >
                {creating ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}