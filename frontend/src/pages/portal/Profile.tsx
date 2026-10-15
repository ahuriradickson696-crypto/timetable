import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../store/auth";
import { useToast } from "../../components/ui/Toast";

interface Profile {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  cohort_id?: string | null;
  lecturer_id?: string | null;
}

export default function Profile() {
  const toast = useToast();
  const user = useAuth((s) => s.user);
  const loadUser = useAuth((s) => s.loadUser);
  const logout = useAuth((s) => s.logout);

  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [savingPw, setSavingPw] = useState(false);

  const [showDelete, setShowDelete] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<Profile>("/account/me");
        setProfile(res.data);
        setFullName(res.data.full_name);
        setEmail(res.data.email);
      } catch (e: any) {
        toast.show("err", e.response?.data?.detail || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const saveProfile = async () => {
    setSavingProfile(true);
    try {
      const res = await api.patch("/account/me", { full_name: fullName, email });
      toast.show("ok", "Profile updated");
      setProfile((p) => (p ? { ...p, full_name: res.data.full_name, email: res.data.email } : p));
      await loadUser();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to save");
    } finally {
      setSavingProfile(false);
    }
  };

  const changePassword = async () => {
    if (newPw !== confirmPw) {
      toast.show("err", "Passwords do not match");
      return;
    }
    if (newPw.length < 8) {
      toast.show("err", "Password must be at least 8 characters");
      return;
    }
    setSavingPw(true);
    try {
      await api.post("/account/change-password", {
        current_password: currentPw,
        new_password: newPw,
      });
      toast.show("ok", "Password changed");
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Failed to change password");
    } finally {
      setSavingPw(false);
    }
  };

  const downloadData = async () => {
    try {
      const res = await api.get("/account/export");
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "aviu-my-data-" + Date.now() + ".json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.show("ok", "Data downloaded");
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Download failed");
    }
  };

  const deleteAccount = async () => {
    if (deleteConfirm !== "DELETE") {
      toast.show("err", 'Type DELETE to confirm');
      return;
    }
    try {
      await api.delete("/account/me");
      toast.show("ok", "Account deleted");
      setTimeout(() => logout(), 800);
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Delete failed");
    }
  };

  if (loading) {
    return <div className="p-8 text-aviu-700 dark:text-aviu-300">Loading profile...</div>;
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">My Profile</h1>
        <p className="text-gray-500 dark:text-gray-400">Manage your account and personal data.</p>
      </div>

      {/* Account info card */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-aviu-800 text-white flex items-center justify-center font-bold text-2xl">
            {(profile?.full_name || "?").charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="font-bold text-lg text-gray-900 dark:text-gray-100">{profile?.full_name}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{profile?.email}</div>
            <div className="text-xs text-aviu-800 dark:text-aviu-300 font-medium capitalize mt-1">
              {profile?.role}
            </div>
          </div>
        </div>

        <h2 className="font-bold text-gray-900 dark:text-gray-100 mb-3">Edit Profile</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full name</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
            />
          </div>
          <button
            onClick={saveProfile}
            disabled={savingProfile}
            className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold px-5 py-2 rounded-lg transition"
          >
            {savingProfile ? "Saving..." : "Save changes"}
          </button>
        </div>

        {profile?.cohort_id && (
          <div className="mt-6 pt-6 border-t border-gray-100 dark:border-gray-800 text-sm">
            <span className="text-gray-500 dark:text-gray-400">Cohort: </span>
            <span className="font-mono text-gray-900 dark:text-gray-100">{profile.cohort_id}</span>
          </div>
        )}
      </div>

      {/* Change password */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 mb-6">
        <h2 className="font-bold text-gray-900 dark:text-gray-100 mb-3">Change Password</h2>
        <div className="space-y-4">
          <input
            type="password"
            placeholder="Current password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
          />
          <input
            type="password"
            placeholder="New password (min 8 chars)"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
          />
          <input
            type="password"
            placeholder="Confirm new password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
          />
          <button
            onClick={changePassword}
            disabled={savingPw || !currentPw || !newPw}
            className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold px-5 py-2 rounded-lg transition"
          >
            {savingPw ? "Changing..." : "Change password"}
          </button>
        </div>
      </div>

      {/* GDPR */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 mb-6">
        <h2 className="font-bold text-gray-900 dark:text-gray-100 mb-2">Your data</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Download a copy of everything AVIU holds about you (GDPR / data portability).
        </p>
        <button
          onClick={downloadData}
          className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold px-5 py-2 rounded-lg transition"
        >
          Download my data (JSON)
        </button>
      </div>

      {/* Danger zone */}
      <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-2xl p-6">
        <h2 className="font-bold text-red-800 dark:text-red-300 mb-2">Danger zone</h2>
        <p className="text-sm text-red-700 dark:text-red-300 mb-4">
          Deleting your account will anonymize your data and sign you out. This cannot be undone.
        </p>
        {!showDelete ? (
          <button
            onClick={() => setShowDelete(true)}
            className="bg-red-600 hover:bg-red-700 text-white font-semibold px-5 py-2 rounded-lg transition"
          >
            Delete my account
          </button>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-red-800 dark:text-red-300">
              Type <code className="bg-red-100 dark:bg-red-900 px-1 rounded">DELETE</code> to confirm:
            </p>
            <input
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="w-full border border-red-300 dark:border-red-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2"
              placeholder="DELETE"
            />
            <div className="flex gap-2">
              <button
                onClick={() => { setShowDelete(false); setDeleteConfirm(""); }}
                className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-100 font-medium px-4 py-2 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={deleteAccount}
                disabled={deleteConfirm !== "DELETE"}
                className="bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-semibold px-4 py-2 rounded-lg"
              >
                Permanently delete
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}