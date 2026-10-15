import { useEffect, useState } from "react";

export default function Splash({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const start = Date.now();
    const DURATION = 10000;

    const tick = setInterval(() => {
      const elapsed = Date.now() - start;
      const pct = Math.min(100, (elapsed / DURATION) * 100);
      setProgress(pct);
      if (pct >= 100) {
        clearInterval(tick);
        setFading(true);
        setTimeout(onComplete, 700);
      }
    }, 50);

    return () => clearInterval(tick);
  }, [onComplete]);

  const skip = () => {
    setFading(true);
    setTimeout(onComplete, 500);
  };

  return (
    <div
      className={
        "fixed inset-0 z-[200] flex items-center justify-center bg-gradient-to-br from-aviu-900 via-aviu-800 to-aviu-950 text-white transition-opacity duration-700 " +
        (fading ? "opacity-0 pointer-events-none" : "opacity-100")
      }
      onClick={skip}
    >
      <div className="max-w-3xl px-8 text-center">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center">
            <span className="text-4xl font-bold">A</span>
          </div>
        </div>

        <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2">
          AVIU Timetable
        </h1>
        <p className="text-aviu-200 text-sm md:text-base mb-8">
          Avance International University
        </p>

        <div className="w-24 h-px bg-aviu-400/40 mx-auto mb-8" />

        <div className="space-y-4 text-base md:text-lg leading-relaxed text-aviu-50 italic">
          <p>May this system serve AVANCE International University well.</p>
          <p>May it save the registrar hours of manual work.</p>
          <p>May students and lecturers always find their classes on time.</p>
          <p>May it be built with integrity, used with wisdom, and sustained with care.</p>
          <p>And may God receive the glory for the skills, patience, and persistence He gave.</p>
        </div>

        <div className="mt-10 text-2xl"></div>
        <div className="mt-2 text-aviu-200 text-sm tracking-widest uppercase">
          Amen
        </div>

        <div className="mt-10 max-w-sm mx-auto">
          <div className="h-1 bg-white/10 rounded overflow-hidden">
            <div
              className="h-1 bg-aviu-300 transition-all duration-100 ease-linear"
              style={{ width: progress + "%" }}
            />
          </div>
          <div className="flex justify-between items-center mt-3 text-xs text-aviu-300">
            <span>Entering system...</span>
            <span>{Math.ceil((100 - progress) / 10)}s</span>
          </div>
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); skip(); }}
          className="mt-8 text-xs text-aviu-300 hover:text-white underline underline-offset-4 transition"
        >
          Click anywhere to continue
        </button>
      </div>
    </div>
  );
}
