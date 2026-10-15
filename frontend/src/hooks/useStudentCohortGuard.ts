import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function useStudentCohortGuard(enabled: boolean = true) {
  const navigate = useNavigate();
  useEffect(() => {
    if (!enabled) return;
    const originalGet = api.get.bind(api);
    let alreadyRedirecting = false;
    (api as any).get = async (...args: any[]) => {
      try {
        return await (originalGet as any)(...args);
      } catch (err: any) {
        const detail = err?.response?.data?.detail || "";
        if (
          err?.response?.status === 400 &&
          typeof detail === "string" &&
          detail.toLowerCase().includes("no cohort") &&
          !alreadyRedirecting
        ) {
          alreadyRedirecting = true;
          navigate("/register", { replace: true });
        }
        throw err;
      }
    };
    return () => { (api as any).get = originalGet; };
  }, [enabled, navigate]);
}