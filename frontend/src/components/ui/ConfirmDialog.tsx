import { ReactNode } from "react";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl max-w-md w-full shadow-xl">
        <div className="p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
          <div className="text-gray-600">{message}</div>
        </div>
        <div className="p-4 bg-gray-50 rounded-b-xl flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 font-medium"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={
              "px-4 py-2 rounded-lg text-white font-medium " +
              (danger
                ? "bg-red-600 hover:bg-red-700"
                : "bg-aviu-800 hover:bg-aviu-900")
            }
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}