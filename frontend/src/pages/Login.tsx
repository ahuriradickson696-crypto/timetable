import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { api } from "../api/client";

type Tab = "signin" | "signup" | "lecturer";
type SignupRole = "STUDENT" | "LECTURER";

interface LecturerOption {
  id: number;
  email: string;
  full_name: string;
  faculty: string;
}

export default function Login() {
  const [tab, setTab] = useState<Tab>("signin");
  const navigate = useNavigate();
  const login = useAuth((s) => s.login);

  // Sign in state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Sign up state
  const [suName, setSuName] = useState("");
  const [suEmail, setSuEmail] = useState("");
  const [suPassword, setSuPassword] = useState("");
  const [suConfirm, setSuConfirm] = useState("");
  const [suRole] = useState<SignupRole>("STUDENT");
  const [suError, setSuError] = useState("");
  const [suLoading, setSuLoading] = useState(false);

  // Lecturer kiosk state
  const [lecturers, setLecturers] = useState<LecturerOption[]>([]);
  const [selectedLecturer, setSelectedLecturer] = useState<number | "">("");
  const [lecturerError, setLecturerError] = useState("");
  const [lecturerLoading, setLecturerLoading] = useState(false);
  const [search, setSearch] = useState("");

  // Load lecturer list when tab is opened
  useEffect(() => {
    if (tab !== "lecturer" || lecturers.length > 0) return;
    api.get<LecturerOption[]>("/auth/lecturers-public")
      .then((res) => setLecturers(res.data))
      .catch(() => setLecturerError("Could not load lecturer list"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuError("");
    if (suPassword !== suConfirm) {
      setSuError("Passwords do not match");
      return;
    }
    if (suPassword.length < 8) {
      setSuError("Password must be at least 8 characters");
      return;
    }
    setSuLoading(true);
    try {
      const res = await api.post("/auth/signup", {
        full_name: suName.trim(),
        email: suEmail.trim().toLowerCase(),
        password: suPassword,
        role: suRole,
      });
      localStorage.setItem("aviu_token", res.data.access_token);
      await useAuth.getState().loadUser();
      navigate("/");
    } catch (err: any) {
      setSuError(err.response?.data?.detail || "Could not create account");
    } finally {
      setSuLoading(false);
    }
  };

  const handleLecturerSignIn = async () => {
    if (!selectedLecturer) {
      setLecturerError("Please select your name");
      return;
    }
    setLecturerError("");
    setLecturerLoading(true);
    try {
      const res = await api.post("/auth/login-as-lecturer", { user_id: selectedLecturer });
      localStorage.setItem("aviu_token", res.data.access_token);
      await useAuth.getState().loadUser();
      navigate("/");
    } catch (err: any) {
      setLecturerError(err.response?.data?.detail || "Could not sign in");
    } finally {
      setLecturerLoading(false);
    }
  };

  // Filter the lecturer dropdown by search term
  const filteredLecturers = lecturers.filter((l) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      l.full_name.toLowerCase().includes(q) ||
      (l.faculty || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen flex">
      {/* Left brand panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-aviu-800 via-aviu-700 to-aviu-900 text-white p-12 flex-col justify-between">
        <div>
          <div className="w-16 h-16 rounded-xl bg-white/20 flex items-center justify-center mb-6">
            <span className="text-3xl font-bold">A</span>
          </div>
          <h1 className="text-4xl font-bold mb-2">AVIU Timetable</h1>
          <p className="text-aviu-200 text-lg">Avance International University</p>
        </div>
        <div>
          <p className="text-aviu-200 italic mb-2">
            "Automated, clash-free timetabling for every programme, every cohort, every semester."
          </p>
          <p className="text-aviu-300 text-sm">Powered by Google OR-Tools CP-SAT</p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white dark:bg-gray-900">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8">
            <div className="w-14 h-14 rounded-xl bg-aviu-800 flex items-center justify-center mb-4">
              <span className="text-2xl font-bold text-white">A</span>
            </div>
            <h1 className="text-2xl font-bold text-aviu-900 dark:text-aviu-100">AVIU Timetable</h1>
            <p className="text-gray-500 dark:text-gray-400">Avance International University</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-8 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => { setTab("signin"); setError(""); setSuError(""); setLecturerError(""); }}
              className={
                "flex-1 py-2.5 rounded-md text-xs font-semibold transition " +
                (tab === "signin"
                  ? "bg-white dark:bg-gray-900 text-aviu-900 dark:text-aviu-100 shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900")
              }
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setTab("signup"); setError(""); setSuError(""); setLecturerError(""); }}
              className={
                "flex-1 py-2.5 rounded-md text-xs font-semibold transition " +
                (tab === "signup"
                  ? "bg-white dark:bg-gray-900 text-aviu-900 dark:text-aviu-100 shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900")
              }
            >
              Create Account
            </button>
            <button
              type="button"
              onClick={() => { setTab("lecturer"); setError(""); setSuError(""); setLecturerError(""); }}
              className={
                "flex-1 py-2.5 rounded-md text-xs font-semibold transition " +
                (tab === "lecturer"
                  ? "bg-white dark:bg-gray-900 text-aviu-900 dark:text-aviu-100 shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900")
              }
            >
              Lecturer
            </button>
          </div>

          {/* ─── SIGN IN ─────────────────────────────────────── */}
          {tab === "signin" && (
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Welcome back</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-8">Enter your credentials to continue</p>

              <form onSubmit={handleSignIn} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="you@aviu.ac.ug"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="Enter your password"
                  />
                </div>
                {error && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-red-700 dark:text-red-300 text-sm">
                    {error}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold py-3 rounded-lg transition-colors"
                >
                  {loading ? "Signing in..." : "Sign in"}
                </button>
              </form>
            </div>
          )}

          {/* ─── CREATE ACCOUNT ─────────────────────────────── */}
          {tab === "signup" && (
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Create your account</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-8">Students join in seconds</p>

              <form onSubmit={handleSignUp} className="space-y-5">

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full name</label>
                  <input
                    type="text"
                    value={suName}
                    onChange={(e) => setSuName(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="e.g. Jane Nakato"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={suEmail}
                    onChange={(e) => setSuEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="you@aviu.ac.ug"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                  <input
                    type="password"
                    value={suPassword}
                    onChange={(e) => setSuPassword(e.target.value)}
                    required
                    minLength={8}
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="At least 8 characters"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm password</label>
                  <input
                    type="password"
                    value={suConfirm}
                    onChange={(e) => setSuConfirm(e.target.value)}
                    required
                    minLength={8}
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="Repeat your password"
                  />
                </div>
                {suError && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-red-700 dark:text-red-300 text-sm">
                    {suError}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={suLoading}
                  className="w-full bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold py-3 rounded-lg transition-colors"
                >
                  {suLoading ? "Creating account..." : "Create Account"}
                </button>
              </form>
            </div>
          )}

          {/* ─── LECTURER KIOSK ────────────────────────────── */}
          {tab === "lecturer" && (
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Lecturer Sign In</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-8">
                Pick your name to see your schedule.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Search name or faculty
                  </label>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                    placeholder="e.g. Baron, or School of Health"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Your name
                  </label>
                  <select
                    value={selectedLecturer}
                    onChange={(e) => setSelectedLecturer(e.target.value ? Number(e.target.value) : "")}
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-aviu-500 outline-none"
                  >
                    <option value="">
                      {lecturers.length === 0 ? "Loading..." : "-- Select your name --"}
                    </option>
                    {filteredLecturers.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.full_name} — {l.faculty}
                      </option>
                    ))}
                  </select>
                  <div className="text-xs text-gray-400 mt-1">
                    {filteredLecturers.length} lecturer{filteredLecturers.length !== 1 ? "s" : ""} available
                  </div>
                </div>

                {lecturerError && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-red-700 dark:text-red-300 text-sm">
                    {lecturerError}
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleLecturerSignIn}
                  disabled={lecturerLoading || !selectedLecturer}
                  className="w-full bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white font-semibold py-3 rounded-lg transition-colors"
                >
                  {lecturerLoading ? "Signing in..." : "Continue"}
                </button>

                <p className="text-xs text-gray-400 text-center mt-2">
                  This kiosk is for lecturer use only.
                </p>
              </div>
            </div>
          )}

          {/* Demo logins */}
          <div className="mt-8 p-4 bg-aviu-50 dark:bg-aviu-900/30 border border-aviu-100 dark:border-aviu-900/50 rounded-lg">
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2">Demo logins</p>
              <p>Admin: <code>admin@aviu.ac.ug</code> / <code>admin123</code></p>
              <p>Student: <code>student1@aviu.ac.ug</code> / <code>student123</code></p>
              <p>Lecturer: use the <strong>Lecturer</strong> tab above</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}