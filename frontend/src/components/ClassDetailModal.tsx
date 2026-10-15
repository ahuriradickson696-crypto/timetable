import { useEffect, useState } from "react";
import { api } from "../api/client";

interface ActivityDetail {
  id: string;
  module_code: string;
  module_name: string;
  credit_units?: number;
  contact_hours_per_week?: number;
  normal_year?: number;
  is_cross_cutting?: boolean;
  owning_school?: string;
  notes?: string;
  lecturer_id: string;
  lecturer_name?: string;
  lecturer_email?: string;
  lecturer_preferred_mode?: string;
  lecturer_phone?: string;
  cohort_id: string;
  cohort_size?: number;
  programme_code?: string;
  programme_name?: string;
  duration_periods: number;
  students: number;
  preferred_room_type: string;
  activity_type: string;
  room_code?: string;
  room_name?: string;
  room_building?: string;
  room_capacity?: number;
  day?: string;
  start_time?: string;
  end_time?: string;
}

export default function ClassDetailModal({
  activityId,
  onClose,
  roomCode,
  day,
  startTime,
  endTime,
}: {
  activityId: string;
  onClose: () => void;
  roomCode?: string;
  day?: string;
  startTime?: string;
  endTime?: string;
}) {
  const [detail, setDetail] = useState<ActivityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<ActivityDetail>(
          `/portal/activity/${encodeURIComponent(activityId)}/details`
        );
        // Attach anything the parent already knew
        setDetail({
          ...res.data,
          room_code: res.data.room_code || roomCode,
          day: res.data.day || day,
          start_time: res.data.start_time || startTime,
          end_time: res.data.end_time || endTime,
        });
      } catch (e: any) {
        setError(e.response?.data?.detail || "Failed to load details");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [activityId, roomCode, day, startTime, endTime]);

  const mapsUrl = (q: string) =>
    "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(q);

  const Row = ({ label, value }: { label: string; value: any }) => {
    if (value === null || value === undefined || value === "") return null;
    return (
      <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 gap-4">
        <span className="text-sm text-gray-500 dark:text-gray-400 shrink-0">{label}</span>
        <span className="text-sm text-gray-900 dark:text-gray-100 font-medium text-right">{value}</span>
      </div>
    );
  };

  const typeLabel =
    detail?.activity_type === "exam"
      ? "Exam"
      : detail?.activity_type === "test"
      ? "Test"
      : "Class";

  return (
    <div
      className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-br from-aviu-800 to-aviu-900 text-white p-6 rounded-t-2xl sticky top-0 z-10">
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-3">
              {loading ? (
                <div className="h-6 bg-white dark:bg-gray-900/20 rounded w-32 animate-pulse"></div>
              ) : (
                <>
                  <div className="text-aviu-200 text-xs uppercase tracking-wider mb-1">
                    {typeLabel} Details
                  </div>
                  <div className="text-2xl font-bold mb-1 font-mono">
                    {detail?.module_code}
                  </div>
                  <div className="text-sm text-aviu-100">{detail?.module_name}</div>
                  {detail?.day && (
                    <div className="text-xs text-aviu-200 mt-2">
                      {detail.day}
                      {detail.start_time && detail.end_time && (
                        <> &middot; {detail.start_time} - {detail.end_time}</>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-3xl leading-none w-8 h-8 flex items-center justify-center"
              aria-label="Close"
            >
              
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="space-y-3 animate-pulse">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              {error}
            </div>
          )}

          {detail && (
            <>
              {/* Room / Location section (prominent) */}
              {(detail.room_code || detail.room_name) && (
                <div className="mb-6 bg-aviu-50 dark:bg-aviu-900/30 border border-aviu-100 rounded-xl p-4">
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div>
                      <div className="text-xs uppercase tracking-wider text-aviu-800 font-semibold mb-1">
                        Location
                      </div>
                      <div className="text-lg font-bold text-aviu-900">
                        {detail.room_name || detail.room_code}
                      </div>
                      {detail.room_code && detail.room_name && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          Code: {detail.room_code}
                        </div>
                      )}
                      {detail.room_building && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          Building: {detail.room_building}
                        </div>
                      )}
                      {detail.room_capacity && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          Capacity: {detail.room_capacity} seats
                        </div>
                      )}
                    </div>
                    <a
                      href={mapsUrl((detail.room_name || detail.room_code) + " AVIU")}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-aviu-800 hover:bg-aviu-900 text-white font-semibold px-4 py-2 rounded-lg transition text-sm whitespace-nowrap"
                    >
                      Open in Maps
                    </a>
                  </div>
                </div>
              )}

              {/* Module */}
              <div className="mb-6">
                <h3 className="font-bold text-sm uppercase tracking-wider text-aviu-800 mb-3">
                  Module
                </h3>
                <Row label="Code" value={detail.module_code} />
                <Row label="Name" value={detail.module_name} />
                <Row label="Credit units" value={detail.credit_units} />
                <Row label="Contact hours / week" value={detail.contact_hours_per_week} />
                <Row label="Owning school" value={detail.owning_school} />
                {detail.is_cross_cutting && (
                  <Row label="Cross-cutting" value="Shared across programmes" />
                )}
                {detail.notes && (
                  <div className="mt-2 p-3 bg-aviu-50 dark:bg-aviu-900/30 rounded-lg">
                    <div className="text-xs text-aviu-800 font-semibold mb-1">Notes</div>
                    <div className="text-xs text-gray-700 dark:text-gray-300">{detail.notes}</div>
                  </div>
                )}
              </div>

              {/* Lecturer */}
              <div className="mb-6">
                <h3 className="font-bold text-sm uppercase tracking-wider text-aviu-800 mb-3">
                  Lecturer
                </h3>
                <Row label="Name" value={detail.lecturer_name || detail.lecturer_id} />
                {detail.lecturer_email && (
                  <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-800 gap-4">
                    <span className="text-sm text-gray-500 dark:text-gray-400">Email</span>
                    <a
                      href={`mailto:${detail.lecturer_email}?subject=Regarding ${encodeURIComponent(detail.module_code)}`}
                      className="text-sm text-aviu-800 font-medium hover:underline truncate"
                    >
                      {detail.lecturer_email}
                    </a>
                  </div>
                )}
                {detail.lecturer_phone && (
                  <Row label="Phone" value={detail.lecturer_phone} />
                )}
                {detail.lecturer_email && (
                  <a
                    href={`mailto:${detail.lecturer_email}?subject=Regarding ${encodeURIComponent(detail.module_code)}`}
                    className="mt-3 inline-flex items-center gap-2 bg-aviu-800 hover:bg-aviu-900 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
                  >
                    Email Lecturer
                  </a>
                )}
              </div>

              {/* Cohort */}
              <div className="mb-6">
                <h3 className="font-bold text-sm uppercase tracking-wider text-aviu-800 mb-3">
                  Cohort
                </h3>
                <Row label="Cohort ID" value={detail.cohort_id} />
                <Row label="Programme" value={detail.programme_name} />
                <Row label="Programme code" value={detail.programme_code} />
                <Row
                  label="Cohort size"
                  value={detail.cohort_size && `${detail.cohort_size} students`}
                />
                <Row label="Students in class" value={detail.students} />
              </div>

              {/* Session */}
              <div>
                <h3 className="font-bold text-sm uppercase tracking-wider text-aviu-800 mb-3">
                  Session
                </h3>
                {detail.day && (
                  <Row
                    label="When"
                    value={`${detail.day}${detail.start_time ? " " + detail.start_time : ""}${
                      detail.end_time ? " - " + detail.end_time : ""
                    }`}
                  />
                )}
                <Row
                  label="Duration"
                  value={`${detail.duration_periods} period${
                    detail.duration_periods !== 1 ? "s" : ""
                  }`}
                />
                <Row label="Preferred room type" value={detail.preferred_room_type} />
              </div>

              {/* Add to calendar button */}
              {detail.day && detail.start_time && (
                <div className="mt-6 pt-6 border-t border-gray-100 dark:border-gray-800">
                  <a
                    href={`${(api.defaults.baseURL || "").replace("/api/v1", "")}/api/v1/portal/my-timetable/ical`}
                    className="inline-flex items-center gap-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 text-gray-800 dark:text-gray-200 text-sm font-medium px-4 py-2 rounded-lg transition"
                  >
                    Add my timetable to Calendar
                  </a>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-gray-50 dark:bg-gray-950 rounded-b-2xl border-t border-gray-100 dark:border-gray-800 text-right">
          <button
            onClick={onClose}
            className="bg-aviu-800 hover:bg-aviu-900 text-white px-5 py-2 rounded-lg font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
