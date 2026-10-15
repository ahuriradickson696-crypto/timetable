import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Programme } from "../../api/client";
import { useToast } from "../../components/ui/Toast";

interface Module {
  code: string;
  name: string;
  credit_units: number;
  contact_hours_per_week: number;
  preferred_room_type: string;
  is_cross_cutting: boolean;
}

const INTAKES = ["Aug", "Jan", "May"];
const ACADEMIC_YEARS = ["2025/2026", "2026/2027", "2027/2028"];
const YEARS = [1, 2, 3, 4, 5, 6];
const SEMESTERS = [1, 2];
const MODES = ["Day", "Weekend"];

export default function RegisterWizard({ onComplete }: { onComplete?: () => void }) {
  const navigate = useNavigate();
  const toast = useToast();

  const [step, setStep] = useState<1 | 2>(1);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [programmeCode, setProgrammeCode] = useState<string>("");
  const [combination, setCombination] = useState<"BC" | "MP">("BC");
  const [yearLevel, setYearLevel] = useState<number>(1);
  const [semester, setSemester] = useState<number>(1);
  const [intake, setIntake] = useState<string>("Aug");
  const [academicYear, setAcademicYear] = useState<string>("2026/2027");
  const [mode, setMode] = useState<string>("Day");

  const [cohortId, setCohortId] = useState<string>("");
  const [modules, setModules] = useState<Module[]>([]);
  const [totalCU, setTotalCU] = useState<number>(0);
  const [loadingModules, setLoadingModules] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load programmes list once
  useEffect(() => {
    api.get<Programme[]>("/programmes")
      .then((res) => setProgrammes(res.data))
      .catch(() => toast.show("err", "Failed to load programmes"));
  }, [toast]);

  const needsCombination = programmeCode === "BSE";
  const currentProgramme = programmes.find((p) => p.code === programmeCode);

  const loadModules = async () => {
    if (!programmeCode) {
      toast.show("err", "Pick a programme first");
      return;
    }
    setLoadingModules(true);

    // Build the exact same query string the backend test proved works
    const params = new URLSearchParams();
    params.set("programme", programmeCode);
    params.set("year", String(yearLevel));
    params.set("semester", String(semester));
    params.set("intake", intake);
    params.set("academic_year", academicYear);
    params.set("mode", mode);
    if (needsCombination) {
      params.set("combination", combination);
    }

    const url = "/cohorts/preview?" + params.toString();
    // eslint-disable-next-line no-console
    console.log("[WIZARD] GET", url);

    try {
      const res = await api.get(url);
      // eslint-disable-next-line no-console
      console.log("[WIZARD] response", res.data);

      if (!res.data?.cohort_id) {
        toast.show("err", "That combination does not exist yet. Ask admin to create the cohort.");
        setLoadingModules(false);
        return;
      }
      setCohortId(res.data.cohort_id);
      setModules(res.data.modules || []);
      setTotalCU(res.data.total_credit_units || 0);
      setStep(2);
    } catch (e: any) {
      const status = e.response?.status;
      const detail = e.response?.data?.detail || e.message;
      // eslint-disable-next-line no-console
      console.error("[WIZARD] loadModules failed", status, detail);
      toast.show("err", "(" + status + ") " + detail);
    } finally {
      setLoadingModules(false);
    }
  };

  const save = async () => {
    if (!cohortId || modules.length === 0) {
      toast.show("err", "Nothing to save");
      return;
    }
    setSaving(true);
    let ok = 0;
    let failed = 0;

    for (const m of modules) {
      try {
        // eslint-disable-next-line no-console
        console.log("[WIZARD] POST /enrollments/me", m.code, "cohort_id=" + cohortId);
        await api.post(
          "/enrollments/me?cohort_id=" + encodeURIComponent(cohortId),
          {
            module_code: m.code,
            academic_year: academicYear,
            semester,
          }
        );
        ok++;
      } catch (inner: any) {
        const status = inner.response?.status;
        const detail = inner.response?.data?.detail || inner.message;
        // eslint-disable-next-line no-console
        console.warn("[WIZARD] enroll failed", m.code, status, detail);
        // Duplicate / already enrolled -> ignore
        if (status === 400 && String(detail).toLowerCase().includes("already")) {
          ok++;
        } else {
          failed++;
        }
      }
    }

    try {
      // Final: make sure the cohort_id is stamped on the user
      await api.post("/enrollments/me/auto-enroll", { cohort_id: cohortId });
    } catch {
      /* non-fatal, individual enrolls should have set the cohort */
    }

    setSaving(false);

    if (failed > 0) {
      toast.show("err", "Saved " + ok + ", failed " + failed + " -- check console");
      return;
    }

    toast.show("ok", "Enrolled in " + ok + " modules");
    if (onComplete) onComplete();
    else navigate("/my-timetable");
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2].map((n) => (
            <div key={n} className="flex items-center gap-2">
              <div
                className={
                  "w-10 h-10 rounded-full flex items-center justify-center font-bold " +
                  (step >= n
                    ? "bg-aviu-800 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400")
                }
              >
                {n}
              </div>
              {n < 2 && (
                <div
                  className={
                    "w-16 h-1 rounded " +
                    (step > n ? "bg-aviu-800" : "bg-gray-200 dark:bg-gray-700")
                  }
                />
              )}
            </div>
          ))}
        </div>

        {step === 1 && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 shadow-sm">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Your Academic Details
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Tell us about your programme so we can show you the right modules.
            </p>

            <div className="space-y-4">
              {/* Programme - buttons, not select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Programme
                </label>
                <div className="grid md:grid-cols-3 gap-3">
                  {programmes.map((p) => {
                    const active = programmeCode === p.code;
                    return (
                      <button
                        key={p.code}
                        type="button"
                        onClick={() => setProgrammeCode(p.code)}
                        className={
                          "p-4 rounded-lg border-2 text-left transition " +
                          (active
                            ? "border-aviu-800 bg-aviu-50 dark:bg-aviu-900/30"
                            : "border-gray-200 dark:border-gray-800 hover:border-aviu-300")
                        }
                      >
                        <div className="font-bold text-aviu-900 dark:text-aviu-100 text-sm">
                          {p.code}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-tight">
                          {p.name}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">{p.level}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {needsCombination && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Teaching Combination (BSE only)
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setCombination("BC")}
                      className={
                        "p-4 rounded-lg border-2 text-left transition " +
                        (combination === "BC"
                          ? "border-aviu-800 bg-aviu-50 dark:bg-aviu-900/30"
                          : "border-gray-200 dark:border-gray-800 hover:border-aviu-300")
                      }
                    >
                      <div className="font-bold text-aviu-900 dark:text-aviu-100">BC</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Biology and Chemistry
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setCombination("MP")}
                      className={
                        "p-4 rounded-lg border-2 text-left transition " +
                        (combination === "MP"
                          ? "border-aviu-800 bg-aviu-50 dark:bg-aviu-900/30"
                          : "border-gray-200 dark:border-gray-800 hover:border-aviu-300")
                      }
                    >
                      <div className="font-bold text-aviu-900 dark:text-aviu-100">MP</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Mathematics and Physics
                      </div>
                    </button>
                  </div>
                </div>
              )}

              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Year of Study
                  </label>
                  <select
                    value={yearLevel}
                    onChange={(e) => setYearLevel(Number(e.target.value))}
                    className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-700"
                  >
                    {YEARS.map((y) => (
                      <option key={y} value={y}>
                        Year {y}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Semester
                  </label>
                  <select
                    value={semester}
                    onChange={(e) => setSemester(Number(e.target.value))}
                    className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-700"
                  >
                    {SEMESTERS.map((s) => (
                      <option key={s} value={s}>
                        Semester {s}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Intake
                  </label>
                  <select
                    value={intake}
                    onChange={(e) => setIntake(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-700"
                  >
                    {INTAKES.map((i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Academic Year
                  </label>
                  <select
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-700"
                  >
                    {ACADEMIC_YEARS.map((y) => (
                      <option key={y} value={y}>
                        {y}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Mode
                  </label>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-700"
                  >
                    {MODES.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-8">
              <button
                onClick={loadModules}
                disabled={!programmeCode || loadingModules}
                className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white px-6 py-3 rounded-lg font-semibold"
              >
                {loadingModules ? "Loading..." : "Continue"}
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Your Modules
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                  {currentProgramme?.name} - Year {yearLevel} - Semester {semester}
                  {needsCombination && " - " + combination}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  Cohort: {cohortId}
                </p>
              </div>
              <button
                onClick={() => setStep(1)}
                className="text-sm text-aviu-800 dark:text-aviu-300 hover:underline"
              >
                Back
              </button>
            </div>

            <div className="bg-aviu-50 dark:bg-aviu-900/30 rounded-lg p-4 mb-4">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <strong>{modules.length}</strong> modules in your curriculum
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Total: <strong>{totalCU}</strong> credit units
              </div>
            </div>

            <div className="max-h-[500px] overflow-y-auto space-y-2 pr-2">
              {modules.map((m) => (
                <div
                  key={m.code}
                  className="flex items-center gap-4 p-4 rounded-xl border-2 border-aviu-100 dark:border-aviu-900/50 bg-aviu-50/40 dark:bg-aviu-900/20"
                >
                  <div className="w-8 h-8 rounded-full bg-aviu-800 text-white flex items-center justify-center font-bold text-xs">
                    OK
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm font-mono">{m.code}</span>
                      {m.is_cross_cutting && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800 font-medium">
                          Shared
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-700 dark:text-gray-300">{m.name}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {m.credit_units} credits - {m.contact_hours_per_week} hrs/week -{" "}
                      {m.preferred_room_type}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-6 border-t border-gray-200 dark:border-gray-800">
              <button
                onClick={() => setStep(1)}
                className="bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 text-gray-800 dark:text-gray-200 px-5 py-3 rounded-lg font-medium"
              >
                Back
              </button>
              <button
                onClick={save}
                disabled={saving || modules.length === 0}
                className="bg-aviu-800 hover:bg-aviu-900 disabled:bg-aviu-300 text-white px-6 py-3 rounded-lg font-semibold"
              >
                {saving ? "Saving..." : "Confirm & Save"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}