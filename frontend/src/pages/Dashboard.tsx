import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { CardSkeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { useAuth } from "../store/auth";

/* ============================================================
   Student dashboard
   ============================================================ */
interface NextClass {
  day: string;
  start_time: string;
  end_time: string;
  module_code: string;
  module_name: string;
  room_code?: string;
  room_name?: string;
  lecturer_name?: string;
  cohort_id?: string;
}

interface TodayClass {
  period_id: string;
  start_time: string;
  end_time: string;
  module_code: string;
  module_name: string;
  room_code?: string;
  lecturer_name?: string;
}

function StudentDashboard() {
  const user = useAuth((s) => s.user);
  const navigate = useNavigate();
  const toast = useToast();

  const [nextClass, setNextClass] = useState<NextClass | null>(null);
  const [today, setToday] = useState<TodayClass[]>([]);
  const [enrollCount, setEnrollCount] = useState(0);
  const [cohortId, setCohortId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const me = await api.get("/portal/me");
        setCohortId(me.data.cohort_id || "");
        setEnrollCount(me.data.enrollment_count ?? 0);

        if (!me.data.cohort_id) {
          // No cohort yet -- send them to the wizard
          toast.show("ok", "Choose your programme to load your modules");
          setTimeout(() => navigate("/register"), 800);
          return;
        }

        const [n, t] = await Promise.allSettled([
          api.get("/portal/my-next-class"),
          api.get("/portal/my-today"),
        ]);

        if (n.status === "fulfilled" && n.value.data?.module_code) {
          setNextClass(n.value.data);
        }
        if (t.status === "fulfilled") {
          const arr = t.value.data?.classes || t.value.data;
          setToday(Array.isArray(arr) ? arr : []);
        }
      } catch (e: any) {
        const detail = e.response?.data?.detail || "";
        if (typeof detail === "string" && detail.toLowerCase().includes("no cohort")) {
          navigate("/register");
        } else {
          toast.show("err", "Failed to load dashboard");
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [navigate]);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  };

  const timeUntil = (start: string) => {
    try {
      const [h, m] = start.split(":").map(Number);
      const now = new Date();
      const target = new Date();
      target.setHours(h, m, 0, 0);
      const diff = target.getTime() - now.getTime();
      if (diff < 0) return "now";
      const mins = Math.floor(diff / 60000);
      if (mins < 60) return "in " + mins + " min";
      const hrs = Math.floor(mins / 60);
      return "in " + hrs + "h " + (mins % 60) + "m";
    } catch {
      return "";
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-64 animate-pulse" />
        <CardSkeleton />
        <div className="grid md:grid-cols-3 gap-4">
          <CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          {greeting()}, {user?.full_name?.split(" ")[0] || "Student"}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          {cohortId
            ? "Enrolled in " + enrollCount + " modules - Cohort " + cohortId
            : "Here is your day at a glance."}
        </p>
      </div>

      <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white rounded-2xl p-6 md:p-8 mb-6 shadow-sm">
        <div className="text-aviu-200 text-xs uppercase tracking-wider mb-2">
          Next Class
        </div>
        {nextClass ? (
          <>
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <div className="text-3xl font-bold mb-1 font-mono">{nextClass.module_code}</div>
                <div className="text-aviu-100 text-base mb-3">{nextClass.module_name}</div>
                <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-aviu-200">
                  <span>Day: {nextClass.day}</span>
                  <span>Time: {nextClass.start_time} - {nextClass.end_time}</span>
                  {nextClass.room_code && <span>Room: {nextClass.room_name || nextClass.room_code}</span>}
                  {nextClass.lecturer_name && <span>Lecturer: {nextClass.lecturer_name}</span>}
                </div>
              </div>
              <div className="text-right">
                <div className="text-aviu-200 text-xs uppercase tracking-wider">Starts</div>
                <div className="text-2xl font-bold">{timeUntil(nextClass.start_time)}</div>
              </div>
            </div>
            <div className="mt-5 flex gap-3 flex-wrap">
              <Link to="/my-timetable"
                className="bg-white text-aviu-900 font-semibold px-4 py-2 rounded-lg hover:bg-aviu-100 transition text-sm">
                View Full Timetable
              </Link>
            </div>
          </>
        ) : (
          <>
            <div className="text-2xl font-bold mb-1">No upcoming class</div>
            <p className="text-aviu-200 mb-4">Enjoy the break. Nothing on the schedule right now.</p>
            <Link to="/my-timetable"
              className="inline-block bg-white text-aviu-900 font-semibold px-4 py-2 rounded-lg hover:bg-aviu-100 transition text-sm">
              View Full Timetable
            </Link>
          </>
        )}
      </div>

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Today's Classes</h2>
          <span className="text-xs text-gray-500 dark:text-gray-400">{today.length} scheduled</span>
        </div>
        {today.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
            No classes today.
          </div>
        ) : (
          <div className="space-y-2">
            {today.map((c, i) => (
              <div key={i}
                className="flex items-center justify-between p-3 border border-gray-100 dark:border-gray-800 rounded-lg hover:bg-aviu-50 dark:hover:bg-aviu-900/20 transition">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-mono font-semibold text-sm">{c.module_code}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {c.start_time} - {c.end_time}
                    </span>
                  </div>
                  <div className="text-sm text-gray-700 dark:text-gray-300">{c.module_name}</div>
                </div>
                <div className="text-right text-xs text-gray-500 dark:text-gray-400">
                  {c.room_code && <div>Room {c.room_code}</div>}
                  {c.lecturer_name && <div className="mt-0.5">{c.lecturer_name}</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <QuickLink to="/my-timetable" label="My Timetable" />
        <QuickLink to="/my-modules" label="My Modules" />
        <QuickLink to="/my-exams" label="My Exams" />
        <QuickLink to="/my-schedule" label="Weekly View" />
      </div>

      <div className="mt-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3">Sync your timetable</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Add your classes to Google Calendar, Apple Calendar, or download as PDF.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href={(api.defaults.baseURL || "") + "/portal/my-timetable/ical"}
            className="bg-aviu-800 hover:bg-aviu-900 text-white font-semibold px-4 py-2 rounded-lg transition text-sm">
            Add to Calendar (iCal)
          </a>
          <a href={(api.defaults.baseURL || "") + "/portal/my-timetable/pdf"}
            className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold px-4 py-2 rounded-lg transition text-sm">
            Download PDF
          </a>
          <a href={(api.defaults.baseURL || "") + "/portal/my-timetable/excel"}
            className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold px-4 py-2 rounded-lg transition text-sm">
            Download Excel
          </a>
        </div>
      </div>
    </div>
  );
}

function QuickLink({ to, label }: { to: string; label: string }) {
  return (
    <Link to={to}
      className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 hover:border-aviu-400 hover:shadow-md transition group text-center">
      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-aviu-800 dark:group-hover:text-aviu-300">
        {label}
      </div>
    </Link>
  );
}

/* ============================================================
   Lecturer dashboard
   ============================================================ */
function LecturerDashboard() {
  const user = useAuth((s) => s.user);
  const toast = useToast();
  const [nextClass, setNextClass] = useState<NextClass | null>(null);
  const [today, setToday] = useState<TodayClass[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [n, t] = await Promise.allSettled([
          api.get("/portal/my-next-class"),
          api.get("/portal/my-today"),
        ]);
        if (n.status === "fulfilled" && n.value.data?.module_code) setNextClass(n.value.data);
        if (t.status === "fulfilled") {
          const arr = t.value.data?.classes || t.value.data;
          setToday(Array.isArray(arr) ? arr : []);
        }
      } catch {
        toast.show("err", "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <div className="space-y-4"><CardSkeleton /><CardSkeleton /></div>;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          Welcome, {user?.full_name?.split(" ")[0] || "Lecturer"}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">Your teaching schedule at a glance.</p>
      </div>

      <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white rounded-2xl p-6 md:p-8 mb-6">
        <div className="text-aviu-200 text-xs uppercase tracking-wider mb-2">Next Class</div>
        {nextClass ? (
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <div className="text-3xl font-bold mb-1 font-mono">{nextClass.module_code}</div>
              <div className="text-aviu-100 text-base mb-3">{nextClass.module_name}</div>
              <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-aviu-200">
                <span>Day: {nextClass.day}</span>
                <span>Time: {nextClass.start_time} - {nextClass.end_time}</span>
                {nextClass.room_code && <span>Room: {nextClass.room_code}</span>}
                {nextClass.cohort_id && <span>Cohort: {nextClass.cohort_id}</span>}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-xl font-bold">No upcoming class</div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">Today's Teaching</h2>
        {today.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">No classes today.</div>
        ) : (
          <div className="space-y-2">
            {today.map((c, i) => (
              <div key={i} className="flex items-center justify-between p-3 border border-gray-100 dark:border-gray-800 rounded-lg">
                <div>
                  <span className="font-mono font-semibold text-sm mr-2">{c.module_code}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{c.start_time} - {c.end_time}</span>
                  <div className="text-sm text-gray-700 dark:text-gray-300 mt-0.5">{c.module_name}</div>
                </div>
                {c.room_code && <div className="text-xs text-gray-500 dark:text-gray-400">Room {c.room_code}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
        <QuickLink to="/my-schedule" label="My Schedule" />
        <QuickLink to="/my-timetable" label="Full Timetable" />
        <QuickLink to="/my-exams" label="Exams" />
      </div>
    </div>
  );
}

/* ============================================================
   Admin dashboard
   ============================================================ */
interface Stats {
  programmes: number;
  cohorts: number;
  course_units: number;
  lecturers: number;
  rooms: number;
  activities: number;
  exam_activities: number;
  runs: number;
}

function AdminDashboard() {
  const user = useAuth((s) => s.user);
  const toast = useToast();
  const [stats, setStats] = useState<Stats>({
    programmes: 0, cohorts: 0, course_units: 0,
    lecturers: 0, rooms: 0, activities: 0, exam_activities: 0, runs: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [p, c, cu, l, r, a, exam, runs] = await Promise.all([
          api.get("/programmes"),
          api.get("/cohorts"),
          api.get("/course-units"),
          api.get("/lecturers"),
          api.get("/rooms"),
          api.get("/activities?activity_type=teaching"),
          api.get("/activities?activity_type=exam"),
          api.get("/generation/runs"),
        ]);
        setStats({
          programmes: p.data.length,
          cohorts: c.data.length,
          course_units: cu.data.length,
          lecturers: l.data.length,
          rooms: r.data.length,
          activities: a.data.length,
          exam_activities: exam.data.length,
          runs: runs.data.length,
        });
      } catch {
        toast.show("err", "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cards = [
    { label: "Programmes", value: stats.programmes, path: "/programmes" },
    { label: "Cohorts", value: stats.cohorts, path: "/cohorts" },
    { label: "Course Units", value: stats.course_units, path: "/course-units" },
    { label: "Lecturers", value: stats.lecturers, path: "/lecturers" },
    { label: "Rooms", value: stats.rooms, path: "/rooms" },
    { label: "Teaching", value: stats.activities, path: "/activities" },
    { label: "Exams", value: stats.exam_activities, path: "/activities" },
    { label: "Runs", value: stats.runs, path: "/generate" },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          Welcome back, {user?.full_name?.split(" ")[0] || "Admin"}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">Here is what is happening at AVIU today.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.label} to={c.path}
              className="bg-white dark:bg-gray-900 rounded-xl p-5 border border-gray-200 dark:border-gray-800 hover:border-aviu-400 hover:shadow-md transition group">
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">{c.value}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400 group-hover:text-aviu-800 dark:group-hover:text-aviu-300">
                {c.label}
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white rounded-xl p-6">
          <h2 className="text-xl font-bold mb-2">Generate New Timetable</h2>
          <p className="text-aviu-200 text-sm mb-4">
            Run the OR-Tools solver to create a clash-free timetable for teaching, tests, or exams.
          </p>
          <Link to="/generate"
            className="inline-block bg-white text-aviu-900 font-semibold px-4 py-2 rounded-lg hover:bg-aviu-100 transition">
            Go to Generate
          </Link>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">View Latest Timetable</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
            Browse, publish, or manually adjust a generated timetable.
          </p>
          <Link to="/timetable"
            className="inline-block bg-aviu-800 text-white font-semibold px-4 py-2 rounded-lg hover:bg-aviu-900 transition">
            View Timetable
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const user = useAuth((s) => s.user);
  if (user?.role === "student") return <StudentDashboard />;
  if (user?.role === "lecturer") return <LecturerDashboard />;
  return <AdminDashboard />;
}