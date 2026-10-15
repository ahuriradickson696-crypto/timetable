import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import { useToast } from "../../components/ui/Toast";

interface PipelineStep {
  status?: string;
  stats?: Record<string, any>;
  message?: string;
  error?: string;
  id?: number;
  published?: boolean;
}

interface UploadResult {
  meta: {
    filename: string;
    size_bytes: number;
    sheets: string[];
    uploaded_at: string;
    archived_path?: string | null;
  };
  pipeline: {
    status: string;
    steps: Record<string, PipelineStep>;
    warnings: string[];
  };
}

interface ArchiveItem {
  name: string;
  size_bytes: number;
  modified_at: string;
}

export default function ImportData() {
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [archives, setArchives] = useState<ArchiveItem[]>([]);
  const [autoPublish, setAutoPublish] = useState(false);
  const [currentInfo, setCurrentInfo] = useState<any>(null);

  const loadStatus = async () => {
    try {
      const res = await api.get("/automation/status");
      setCurrentInfo(res.data.current);
    } catch {}
  };

  const loadArchives = async () => {
    try {
      const res = await api.get<ArchiveItem[]>("/automation/archives");
      setArchives(res.data);
    } catch {}
  };

  useEffect(() => {
    loadStatus();
    loadArchives();
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSet(dropped);
  };

  const validateAndSet = (f: File) => {
    if (!f.name.toLowerCase().endsWith(".xlsx")) {
      toast.show("err", "Only .xlsx files are allowed");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      toast.show("err", "File too large (max 50 MB)");
      return;
    }
    setFile(f);
    setResult(null);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await api.post<UploadResult>(
        `/automation/upload?auto_publish=${autoPublish}&run_solver=true`,
        fd,
        { headers: { "Content-Type": "multipart/form-data" }, timeout: 600000 }
      );
      setResult(res.data);
      if (res.data.pipeline.status === "ok") {
        toast.show("ok", "Pipeline completed successfully");
      } else {
        toast.show("err", "Pipeline finished with errors");
      }
      loadStatus();
      loadArchives();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const triggerCurrent = async () => {
    setUploading(true);
    setResult(null);
    try {
      const res = await api.post("/automation/trigger", null, { timeout: 600000 });
      toast.show("ok", "Pipeline re-run complete");
      setResult({ meta: currentInfo, pipeline: res.data });
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Trigger failed");
    } finally {
      setUploading(false);
    }
  };

  const rollback = async (name: string) => {
    if (!confirm(`Restore ${name} as current file?`)) return;
    try {
      await api.post(`/automation/rollback/${encodeURIComponent(name)}`);
      toast.show("ok", `Restored ${name}`);
      loadStatus();
      loadArchives();
    } catch (e: any) {
      toast.show("err", e.response?.data?.detail || "Rollback failed");
    }
  };

  const formatBytes = (b: number) => {
    if (b < 1024) return b + " B";
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
    return (b / (1024 * 1024)).toFixed(1) + " MB";
  };

  const StepRow = ({ label, step }: { label: string; step?: PipelineStep }) => {
    if (!step) return null;
    const isOk = step.status === "ok";
    const isErr = step.status === "error";
    const isSkip = step.status === "skip";
    return (
      <div className="flex items-start gap-3 py-2 border-b last:border-0">
        <span className={"mt-0.5 " + (isOk ? "text-green-600" : isErr ? "text-red-600" : "text-yellow-600")}>
          {isOk ? "" : isErr ? "" : ""}
        </span>
        <div className="flex-1">
          <div className="font-medium text-sm">{label}</div>
          {step.stats && (
            <div className="text-xs text-gray-600 mt-0.5">
              {Object.entries(step.stats)
                .filter(([k]) => !k.endsWith("_count"))
                .map(([k, v]) => `${k}: ${v}`)
                .join("    ")}
            </div>
          )}
          {step.message && <div className="text-xs text-gray-600">{step.message}</div>}
          {step.id && <div className="text-xs text-gray-500">Run #{step.id} {step.published && "  published"}</div>}
          {step.error && <div className="text-xs text-red-600 mt-1">{step.error}</div>}
        </div>
      </div>
    );
  };

  return (
    <div>
      <PageHeader
        title="Import Master Data"
        subtitle="Drop your AVIU workbook  the system handles everything automatically"
      />

      {/* Drag and drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={
          "bg-white rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition " +
          (dragging
            ? "border-aviu-500 bg-aviu-50 scale-[1.01]"
            : "border-gray-300 hover:border-aviu-400 hover:bg-aviu-50")
        }
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          hidden
          onChange={(e) => e.target.files?.[0] && validateAndSet(e.target.files[0])}
        />
        <div className="text-6xl mb-3">{dragging ? "" : ""}</div>
        <div className="text-xl font-bold text-gray-800 mb-1">
          {dragging ? "Drop the Excel file here" : "Drag & drop the Excel workbook"}
        </div>
        <div className="text-sm text-gray-500 mb-4">
          or click to browse  .xlsx only, up to 50 MB
        </div>

        {file && (
          <div className="inline-flex items-center gap-3 bg-aviu-100 text-aviu-900 px-4 py-2 rounded-lg mt-3">
            <span className="text-lg"></span>
            <span className="font-medium">{file.name}</span>
            <span className="text-xs text-aviu-700">({formatBytes(file.size)})</span>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="text-aviu-700 hover:text-red-600 font-bold"
            >
              
            </button>
          </div>
        )}
      </div>

      {/* Options + Upload button */}
      {file && (
        <div className="mt-4 flex items-center justify-between bg-white rounded-xl border border-gray-200 p-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="font-medium">Auto-publish</span>
            <span className="text-gray-500">(only if zero warnings)</span>
          </label>
          <button
            onClick={upload}
            disabled={uploading}
            className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-400 text-white font-semibold px-6 py-3 rounded-lg"
          >
            {uploading ? " Running pipeline..." : " Upload & Run Pipeline"}
          </button>
        </div>
      )}

      {/* Progress and result */}
      {uploading && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="animate-spin text-2xl"></div>
            <div className="font-semibold">Running full pipeline...</div>
          </div>
          <div className="text-sm text-gray-500">
            Importing data  Generating activities  Assigning lecturers  Running solver
          </div>
          <div className="mt-3 h-2 bg-gray-100 rounded overflow-hidden">
            <div className="h-2 bg-gradient-to-r from-aviu-500 to-aviu-800 animate-pulse" style={{ width: "100%" }} />
          </div>
        </div>
      )}

      {result && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold">
                {result.pipeline.status === "ok" ? " Pipeline Complete" : " Pipeline Failed"}
              </h2>
              <p className="text-sm text-gray-500">
                {result.meta.filename}  {formatBytes(result.meta.size_bytes)}  {result.meta.sheets.length} sheets
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl">
                {result.pipeline.status === "ok" ? "" : ""}
              </div>
            </div>
          </div>

          <div className="space-y-1 mb-4">
            <StepRow label="Import master data" step={result.pipeline.steps["import"]} />
            <StepRow label="Generate activities" step={result.pipeline.steps["activities"]} />
            <StepRow label="Assign lecturers" step={result.pipeline.steps["lecturers"]} />
            <StepRow label="Run solver (teaching)" step={result.pipeline.steps["teaching_run"]} />
            {result.pipeline.steps["exam_run"] && (
              <StepRow label="Run solver (exams)" step={result.pipeline.steps["exam_run"]} />
            )}
          </div>

          {result.pipeline.warnings.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="font-semibold text-yellow-800 text-sm mb-1">
                 {result.pipeline.warnings.length} warning(s)
              </div>
              <ul className="text-xs text-yellow-700 space-y-0.5">
                {result.pipeline.warnings.slice(0, 5).map((w, i) => <li key={i}> {w}</li>)}
                {result.pipeline.warnings.length > 5 && <li>... and more</li>}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Current file */}
      {currentInfo && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold mb-3"> Current Workbook</h2>
          <div className="text-sm space-y-1">
            <div><span className="text-gray-500">Path:</span> <code className="text-xs">{currentInfo.path}</code></div>
            <div><span className="text-gray-500">Size:</span> {formatBytes(currentInfo.size_bytes)}</div>
            <div><span className="text-gray-500">Modified:</span> {new Date(currentInfo.modified_at).toLocaleString()}</div>
            <div><span className="text-gray-500">Sheets:</span> {currentInfo.sheets.join(", ")}</div>
          </div>
          <button
            onClick={triggerCurrent}
            disabled={uploading}
            className="mt-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium px-4 py-2 rounded-lg text-sm"
          >
             Re-run pipeline with this file
          </button>
        </div>
      )}

      {/* Archive history */}
      {archives.length > 0 && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold mb-3"> Upload History</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {archives.map((a) => (
              <div key={a.name} className="flex items-center justify-between p-3 border rounded-lg hover:bg-aviu-50">
                <div>
                  <div className="font-medium text-sm">{a.name}</div>
                  <div className="text-xs text-gray-500">
                    {new Date(a.modified_at).toLocaleString()}  {formatBytes(a.size_bytes)}
                  </div>
                </div>
                <button
                  onClick={() => rollback(a.name)}
                  className="text-aviu-800 hover:underline text-sm font-medium"
                >
                  Restore
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
