import { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface Toast {
  id: number;
  type: "ok" | "err" | "info";
  msg: string;
}

interface ToastContextValue {
  show: (type: "ok" | "err" | "info", msg: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((type: "ok" | "err" | "info", msg: string) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, type, msg }]);
    setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id));
    }, 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              "px-4 py-3 rounded-lg shadow-lg text-white font-medium min-w-[250px] max-w-md pointer-events-auto " +
              (t.type === "ok"
                ? "bg-green-600"
                : t.type === "err"
                ? "bg-red-600"
                : "bg-aviu-800")
            }
          >
            {t.type === "ok" && " "}
            {t.type === "err" && " "}
            {t.type === "info" && " "}
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}
