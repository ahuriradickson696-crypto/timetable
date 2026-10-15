import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./store/auth";
import { api } from "./api/client";
import Login from "./pages/Login";
import Splash from "./pages/Splash";
import Dashboard from "./pages/Dashboard";
import Layout from "./components/Layout";
import Programmes from "./pages/admin/Programmes";
import Cohorts from "./pages/admin/Cohorts";
import CourseUnits from "./pages/admin/CourseUnits";
import Lecturers from "./pages/admin/Lecturers";
import Rooms from "./pages/admin/Rooms";
import TimePeriods from "./pages/admin/TimePeriods";
import Activities from "./pages/admin/Activities";
import Generate from "./pages/admin/Generate";
import TimetableView from "./pages/admin/TimetableView";
import Users from "./pages/admin/Users";
import Analytics from "./pages/admin/Analytics";
import ImportData from "./pages/admin/ImportData";
import LinkUsers from "./pages/admin/LinkUsers";
import ApiExplorer from "./pages/admin/ApiExplorer";
import ApiKeys from "./pages/admin/ApiKeys";
import Profile from "./pages/portal/Profile";
import MyTimetable from "./pages/portal/MyTimetable";
import MyExams from "./pages/portal/MyExams";
import MyModules from "./pages/portal/MyModules";
import MySchedule from "./pages/portal/MySchedule";
import LecturerCohorts from "./pages/portal/LecturerCohorts";
import LecturerModules from "./pages/portal/LecturerModules";
import RegisterWizard from "./pages/portal/RegisterWizard";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuth((s) => s.token);
  const user = useAuth((s) => s.user);
  if (!token) return <Navigate to="/login" replace />;
  if (!user) return <div className="p-8 text-aviu-700">Loading...</div>;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const user = useAuth((s) => s.user);
  const ok = user && ["admin", "officer", "viewer"].includes(user.role);
  if (!ok) return <Navigate to="/" replace />;
  return <>{children}</>;
}

/**
 * Smart root redirect:
 *   - Student with 0 enrollments  /register
 *   - Student with enrollments  /my-timetable
 *   - Lecturer  /my-schedule
 *   - Admin/officer  /dashboard
 */
function RootRedirect() {
  const user = useAuth((s) => s.user);
  const [checking, setChecking] = useState(true);
  const [enrollCount, setEnrollCount] = useState<number>(-1);

  useEffect(() => {
    const check = async () => {
      if (!user || user.role !== "student") {
        setChecking(false);
        return;
      }
      try {
        const res = await api.get("/portal/me");
        setEnrollCount(res.data.enrollment_count ?? 0);
      } catch {
        setEnrollCount(0);
      } finally {
        setChecking(false);
      }
    };
    check();
  }, [user]);

  if (!user) return null;

  if (user.role === "lecturer") return <Navigate to="/my-schedule" replace />;

  if (user.role === "student") {
    if (checking) {
      return (
        <div className="p-12 text-center text-aviu-700">
          <div className="text-4xl mb-3"></div>
          Loading your dashboard...
        </div>
      );
    }
    if (enrollCount === 0) return <Navigate to="/register" replace />;
    return <Navigate to="/my-timetable" replace />;
  }

  return <Dashboard />;
}

export default function App() {
  const loadUser = useAuth((s) => s.loadUser);
  const token = useAuth((s) => s.token);
  const user = useAuth((s) => s.user);

  const [showSplash, setShowSplash] = useState(() => {
    return sessionStorage.getItem("aviu_splash_shown") !== "yes";
  });

  useEffect(() => {
    if (token) loadUser();
  }, [token, loadUser]);

  const splashActive = showSplash && !!user;

  const handleSplashComplete = () => {
    sessionStorage.setItem("aviu_splash_shown", "yes");
    setShowSplash(false);
  };

  return (
    <>
      {splashActive && <Splash onComplete={handleSplashComplete} />}

      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Routes>
                {/* Standalone wizard -- no sidebar */}
                <Route path="/register" element={<RegisterWizard />} />

                {/* Everything else inside the Layout */}
                <Route
                  path="*"
                  element={
                    <Layout>
                      <Routes>
                        <Route path="/" element={<RootRedirect />} />
                        <Route path="/my-timetable" element={<MyTimetable />} />
                        <Route path="/my-exams" element={<MyExams />} />
                        <Route path="/my-modules" element={<MyModules />} />
                        <Route path="/my-schedule" element={<MySchedule />} />
                        <Route path="/lecturer/cohorts" element={<LecturerCohorts />} />
                        <Route path="/lecturer/modules" element={<LecturerModules />} />
                        <Route path="/profile" element={<Profile />} />
                        <Route path="/import" element={<AdminRoute><ImportData /></AdminRoute>} />
                        <Route path="/link-users" element={<AdminRoute><LinkUsers /></AdminRoute>} />
                        <Route path="/api-explorer" element={<AdminRoute><ApiExplorer /></AdminRoute>} />
                        <Route path="/api-keys" element={<AdminRoute><ApiKeys /></AdminRoute>} />
                        <Route path="/programmes" element={<AdminRoute><Programmes /></AdminRoute>} />
                        <Route path="/cohorts" element={<AdminRoute><Cohorts /></AdminRoute>} />
                        <Route path="/course-units" element={<AdminRoute><CourseUnits /></AdminRoute>} />
                        <Route path="/lecturers" element={<AdminRoute><Lecturers /></AdminRoute>} />
                        <Route path="/rooms" element={<AdminRoute><Rooms /></AdminRoute>} />
                        <Route path="/time-periods" element={<AdminRoute><TimePeriods /></AdminRoute>} />
                        <Route path="/activities" element={<AdminRoute><Activities /></AdminRoute>} />
                        <Route path="/generate" element={<AdminRoute><Generate /></AdminRoute>} />
                        <Route path="/timetable" element={<AdminRoute><TimetableView /></AdminRoute>} />
                        <Route path="/analytics" element={<AdminRoute><Analytics /></AdminRoute>} />
                        <Route path="/users" element={<AdminRoute><Users /></AdminRoute>} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                      </Routes>
                    </Layout>
                  }
                />
              </Routes>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
