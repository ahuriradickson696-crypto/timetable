import axios from "axios";

// Auto-detect host: works on localhost, LAN IP, and deployed domains
const HOST = window.location.hostname;
const API_BASE = `http://${HOST}:8000/api/v1`;

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("aviu_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("aviu_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface Programme {
  code: string;
  name: string;
  level: string;
  school_faculty: string;
  duration_years: number;
  active: boolean;
}

export interface Cohort {
  id: string;
  programme_code: string;
  year_level: number;
  mode: string;
  intake: string;
  academic_year: string;
  semester: number;
  estimated_students: number;
  status: string;
}

export interface CourseUnit {
  code: string;
  name: string;
  credit_units: number;
  contact_hours_per_week: number;
  normal_year: number;
  is_cross_cutting: boolean;
  preferred_room_type: string;
  owning_school?: string;
  active: boolean;
  notes?: string;
  shared_across_programmes: string[];
}

export interface Lecturer {
  id: string;
  full_name: string;
  max_hours_per_week: number;
  preferred_mode: string;
  email?: string;
  active: boolean;
  notes?: string;
  can_teach_modules: string[];
}

export interface Room {
  code: string;
  name: string;
  capacity: number;
  room_type: string;
  building?: string;
  available_modes: string;
  active: boolean;
}

export interface TimePeriod {
  id: number;
  period_id: string;
  day: string;
  start_time: string;
  end_time: string;
  mode: string;
  is_break: boolean;
  order_index: number;
}

export interface Activity {
  id: string;
  cohort_id: string;
  module_code: string;
  lecturer_id: string;
  duration_periods: number;
  preferred_room_type: string;
  students: number;
  split_allowed: boolean;
  joint_cohort_ids?: string;
  semester: number;
  intake: string;
  academic_year: string;
  activity_type: string;
  notes?: string;
}

export interface TimetableRun {
  id: number;
  intake: string;
  academic_year: string;
  semester: number;
  run_type: string;
  status: string;
  message?: string;
  metrics?: string;
  is_published: boolean;
  is_locked: boolean;
  published_at?: string;
  published_by?: number;
  created_at: string;
}

export interface TimetableCell {
  day: string;
  period_id: string;
  start_time: string;
  end_time: string;
  activity_id?: string;
  module_code?: string;
  module_name?: string;
  cohort_id?: string;
  lecturer_id?: string;
  lecturer_name?: string;
  room_code?: string;
  is_break: boolean;
  assignment_id?: number;
  is_manual: boolean;
  is_locked: boolean;
}

export interface MoveResponse {
  status: "ok" | "conflict";
  message: string;
  conflicts: Array<{ type: string; message: string; conflicting_activity?: string }>;
  assignment?: any;
}

export interface ChangeLogEntry {
  id: number;
  user_id?: number;
  action: string;
  entity_type: string;
  entity_id?: string;
  run_id?: number;
  details?: string;
  timestamp: string;
}

export async function downloadFile(url: string, filename: string) {
  try {
    const token = localStorage.getItem("aviu_token");
    const res = await axios.get(url, {
      responseType: "blob",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const blob = new Blob([res.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (e: any) {
    alert("Download failed: " + (e.response?.data?.detail || e.message));
    throw e;
  }
}