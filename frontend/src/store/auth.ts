import { create } from "zustand";
import { api, User } from "../api/client";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("aviu_token"),
  loading: false,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const res = await api.post("/auth/login", { email, password });
      const token = res.data.access_token;
      localStorage.setItem("aviu_token", token);
      set({ token });
      const me = await api.get<User>("/auth/me");
      set({ user: me.data, loading: false });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("aviu_token");
    set({ user: null, token: null });
    window.location.href = "/login";
  },

  loadUser: async () => {
    const token = localStorage.getItem("aviu_token");
    if (!token) return;
    set({ loading: true });
    try {
      const me = await api.get<User>("/auth/me");
      set({ user: me.data, token, loading: false });
    } catch {
      localStorage.removeItem("aviu_token");
      set({ user: null, token: null, loading: false });
    }
  },
}));
