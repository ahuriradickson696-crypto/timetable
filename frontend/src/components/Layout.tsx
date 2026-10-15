import { useState, ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useNotifications } from "../hooks/useNotifications";
import { useTheme } from "../hooks/useTheme";

/* ---------------------------------------------------------
   Inline SVG icon set  2020, stroke 1.75, currentColor
   --------------------------------------------------------- */
type IconProps = { name: string };

function Icon({ name }: IconProps) {
  const common = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  const paths: Record<string, ReactNode> = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="9" rx="1.5" />
        <rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" />
        <rect x="3" y="16" width="7" height="5" rx="1.5" />
      </>
    ),
    upload: (
      <>
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </>
    ),
    link: (
      <>
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
      </>
    ),
    graduation: (
      <>
        <path d="M22 10v6" />
        <path d="M2 10l10-5 10 5-10 5z" />
        <path d="M6 12v5c3 3 9 3 12 0v-5" />
      </>
    ),
    users: (
      <>
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    ),
    book: (
      <>
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </>
    ),
    lecturer: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21v-1a6 6 0 0 1 12 0v1" />
        <path d="M20 12l2 2 3-3" />
      </>
    ),
    room: (
      <>
        <path d="M3 21V7l9-4 9 4v14" />
        <path d="M9 21V13h6v8" />
        <path d="M9 21h6" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <polyline points="12 7 12 12 15 14" />
      </>
    ),
    activity: (
      <>
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </>
    ),
    sparkle: (
      <>
        <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="4.5" width="18" height="16" rx="2" />
        <line x1="3" y1="10" x2="21" y2="10" />
        <line x1="8" y1="2.5" x2="8" y2="6.5" />
        <line x1="16" y1="2.5" x2="16" y2="6.5" />
      </>
    ),
    chart: (
      <>
        <line x1="4" y1="20" x2="20" y2="20" />
        <rect x="6" y="12" width="3" height="6" />
        <rect x="11" y="8" width="3" height="10" />
        <rect x="16" y="4" width="3" height="14" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21v-1a6 6 0 0 1 12 0v1" />
      </>
    ),
    exam: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="9" y1="15" x2="15" y2="15" />
        <line x1="9" y1="11" x2="15" y2="11" />
      </>
    ),
    schedule: (
      <>
        <rect x="3" y="4.5" width="18" height="16" rx="2" />
        <line x1="3" y1="10" x2="21" y2="10" />
        <circle cx="8" cy="14" r="1" />
        <circle cx="12" cy="14" r="1" />
        <circle cx="16" cy="14" r="1" />
      </>
    ),
    module: (
      <>
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
        <line x1="8" y1="7" x2="16" y2="7" />
        <line x1="8" y1="11" x2="14" y2="11" />
      </>
    ),
    profile: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21v-1a6 6 0 0 1 12 0v1" />
        <circle cx="20" cy="6" r="2" />
      </>
    ),
  };

  return (
    <svg {...common} aria-hidden="true">
      {paths[name] ?? paths.dashboard}
    </svg>
  );
}

/* ---------------------------------------------------------
   Navigation definitions
   --------------------------------------------------------- */
type NavItem = { path: string; label: string; icon: string };

const ADMIN_NAV: NavItem[] = [
  { path: "/", label: "Dashboard", icon: "dashboard" },
  { path: "/import", label: "Import Data", icon: "upload" },
  { path: "/link-users", label: "Link Users", icon: "link" },
  { path: "/api-explorer", label: "Admin API", icon: "link" },
  { path: "/api-keys", label: "API Keys", icon: "link" },
  { path: "/programmes", label: "Programmes", icon: "graduation" },
  { path: "/cohorts", label: "Cohorts", icon: "users" },
  { path: "/course-units", label: "Course Units", icon: "book" },
  { path: "/lecturers", label: "Lecturers", icon: "lecturer" },
  { path: "/rooms", label: "Rooms", icon: "room" },
  { path: "/time-periods", label: "Time Structure", icon: "clock" },
  { path: "/activities", label: "Activities", icon: "activity" },
  { path: "/generate", label: "Generate", icon: "sparkle" },
  { path: "/timetable", label: "View Timetable", icon: "calendar" },
  { path: "/analytics", label: "Analytics", icon: "chart" },
  { path: "/users", label: "Users", icon: "user" },
];

const STUDENT_NAV: NavItem[] = [
  { path: "/", label: "Dashboard", icon: "dashboard" },
  { path: "/my-timetable", label: "My Timetable", icon: "calendar" },
  { path: "/my-modules", label: "My Modules", icon: "module" },
  { path: "/my-schedule", label: "Weekly View", icon: "schedule" },
  { path: "/my-exams", label: "My Exams", icon: "exam" },
  { path: "/profile", label: "My Profile", icon: "profile" },
];

const LECTURER_NAV: NavItem[] = [
  { path: "/", label: "Dashboard", icon: "dashboard" },
  { path: "/my-schedule", label: "My Schedule", icon: "schedule" },
  { path: "/my-timetable", label: "Full Timetable", icon: "calendar" },
  { path: "/my-exams", label: "Exams", icon: "exam" },
  { path: "/profile", label: "My Profile", icon: "profile" },
  { path: "/lecturer/modules", label: "My Modules", icon: "module" },
  { path: "/lecturer/cohorts", label: "My Cohorts", icon: "users" },
];

/* ---------------------------------------------------------
   Component
   --------------------------------------------------------- */
export default function Layout({ children }: { children: React.ReactNode }) {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { has_new_timetable } = useNotifications();
  const { theme, toggle: toggleTheme } = useTheme();

  const navItems: NavItem[] =
    user?.role === "student" ? STUDENT_NAV
    : user?.role === "lecturer" ? LECTURER_NAV
    : ADMIN_NAV;

  const roleBadge = () => {
    const r = user?.role || "viewer";
    const colors: Record<string, string> = {
      admin: "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300",
      officer: "bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300",
      viewer: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
      student: "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
      lecturer: "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-300",
    };
    return (
      <span className={"px-2 py-0.5 rounded text-xs font-medium capitalize " + (colors[r] || colors.viewer)}>
        {r}
      </span>
    );
  };

  const SidebarContent = () => (
    <>
      <div className="p-6 border-b border-aviu-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white text-aviu-900 flex items-center justify-center font-bold text-lg">
            A
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">AVIU</h1>
            <p className="text-xs text-aviu-300">Timetable System</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors " +
                (active
                  ? "bg-aviu-700 text-white"
                  : "text-aviu-200 hover:bg-aviu-800 hover:text-white")
              }
            >
              <span className="shrink-0 flex items-center justify-center w-5">
                <Icon name={item.icon} />
              </span>
              <span className="flex-1">{item.label}</span>
              {(item.path === "/my-timetable" || item.path === "/my-schedule") && has_new_timetable && (
                <span
                  className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_0_3px_rgba(239,68,68,0.25)]"
                  title="New timetable available"
                />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-aviu-800">
        <div className="mb-2">
          <p className="text-sm font-medium truncate">{user?.full_name}</p>
          <p className="text-xs text-aviu-300 truncate mb-1.5">{user?.email}</p>
          {roleBadge()}
        </div>
        <button
          onClick={logout}
          className="w-full text-aviu-200 hover:text-white hover:bg-aviu-800 text-xs py-1.5 rounded transition-colors"
        >
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-950">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-30 bg-aviu-900 text-white px-4 py-3 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-white text-aviu-900 flex items-center justify-center font-bold">
            A
          </div>
          <span className="font-bold">AVIU Timetable</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-aviu-800 text-aviu-200 hover:text-white transition"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-1.5 rounded-lg hover:bg-aviu-800 flex items-center justify-center"
            aria-label="Toggle navigation"
          >
            {mobileOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40 top-14"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={
          "w-64 bg-aviu-900 text-white flex flex-col fixed lg:static top-14 lg:top-0 bottom-0 z-40 transition-transform " +
          (mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0")
        }
      >
        <SidebarContent />
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto pt-14 lg:pt-0">
        <div className="p-4 md:p-8 max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  );
}
