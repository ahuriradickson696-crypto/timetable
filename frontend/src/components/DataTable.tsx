import { useMemo, useState } from "react";
import SearchInput from "./ui/SearchInput";
import Pagination from "./ui/Pagination";
import { TableSkeleton } from "./ui/Skeleton";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  searchable?: boolean;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

export default function DataTable<T extends { [k: string]: any }>({
  columns,
  data,
  loading = false,
  emptyMessage = "No records",
  emptyIcon = "",
  onEdit,
  onDelete,
  actions,
  pageSize = 15,
  rowKey,
}: {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  emptyIcon?: string;
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  actions?: (item: T) => React.ReactNode;
  pageSize?: number;
  rowKey?: (item: T) => string | number;
}) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  // Filter by search
  const filtered = useMemo(() => {
    if (!search) return data;
    const q = search.toLowerCase();
    return data.filter((row) => {
      for (const c of columns) {
        const val = row[c.key];
        if (val != null && String(val).toLowerCase().includes(q)) return true;
      }
      return false;
    });
  }, [data, search, columns]);

  // Sort
  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return sortDir === "asc" ? -1 : 1;
      if (bv == null) return sortDir === "asc" ? 1 : -1;
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return copy;
  }, [filtered, sortKey, sortDir]);

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageData = sorted.slice((safePage - 1) * pageSize, safePage * pageSize);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  if (loading) return <TableSkeleton rows={pageSize > 10 ? 8 : 5} />;

  const showActions = !!onEdit || !!onDelete || !!actions;

  return (
    <div>
      {/* Search bar */}
      {data.length > 0 && (
        <div className="mb-4 max-w-md">
          <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search..." />
        </div>
      )}

      {pageData.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-5xl mb-3">{emptyIcon}</div>
          <p className="text-gray-500">{search ? `No matches for "${search}"` : emptyMessage}</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-aviu-800 text-white">
              <tr>
                {columns.map((c) => (
                  <th
                    key={c.key}
                    onClick={() => c.sortable && toggleSort(c.key)}
                    className={
                      "text-left px-4 py-3 text-sm font-semibold " +
                      (c.sortable ? "cursor-pointer hover:bg-aviu-700 select-none" : "") +
                      (c.className ? " " + c.className : "")
                    }
                  >
                    <span className="inline-flex items-center gap-1">
                      {c.label}
                      {c.sortable && sortKey === c.key && (
                        <span className="text-xs">{sortDir === "asc" ? "" : ""}</span>
                      )}
                      {c.sortable && sortKey !== c.key && (
                        <span className="text-xs opacity-40"></span>
                      )}
                    </span>
                  </th>
                ))}
                {showActions && <th className="text-right px-4 py-3 text-sm font-semibold">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {pageData.map((row, i) => (
                <tr
                  key={rowKey ? rowKey(row) : i}
                  className={i % 2 === 0 ? "bg-white" : "bg-aviu-50"}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={"px-4 py-3 text-sm text-gray-800 " + (c.className || "")}>
                      {c.render ? c.render(row) : row[c.key]}
                    </td>
                  ))}
                  {showActions && (
                    <td className="px-4 py-3 text-sm text-right whitespace-nowrap">
                      {actions && actions(row)}
                      {onEdit && (
                        <button
                          onClick={() => onEdit(row)}
                          className="text-aviu-700 hover:underline font-medium mr-3"
                        >
                          Edit
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={() => onDelete(row)}
                          className="text-red-600 hover:underline font-medium"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 pb-4">
            <Pagination
              page={safePage}
              pageSize={pageSize}
              total={sorted.length}
              onPageChange={setPage}
            />
          </div>
        </div>
      )}
    </div>
  );
}
