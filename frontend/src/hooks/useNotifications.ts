import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

interface NotificationState {
  latest_published_run_id: number | null;
  last_seen_run_id: number | null;
  has_new_timetable: boolean;
}

export function useNotifications(pollMs = 60000) {
  const [state, setState] = useState<NotificationState>({
    latest_published_run_id: null,
    last_seen_run_id: null,
    has_new_timetable: false,
  });

  const refresh = useCallback(async () => {
    try {
      const res = await api.get<NotificationState>("/notifications/me");
      setState(res.data);
    } catch {
      /* silent  user not logged in or server cold */
    }
  }, []);

  const markSeen = useCallback(async () => {
    try {
      await api.post("/notifications/mark-seen");
      setState((s) => ({ ...s, has_new_timetable: false, last_seen_run_id: s.latest_published_run_id }));
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { ...state, refresh, markSeen };
}
