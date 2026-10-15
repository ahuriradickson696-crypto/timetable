export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (total <= pageSize) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  const pages: (number | "")[] = [];
  const add = (n: number | "") => pages.push(n);
  add(1);
  for (let i = page - 1; i <= page + 1; i++) {
    if (i > 1 && i < totalPages) add(i);
  }
  if (totalPages > 1) add(totalPages);
  const deduped = pages.filter((p, i, a) => p !== a[i - 1]);

  return (
    <div className="flex items-center justify-between mt-4 text-sm">
      <div className="text-gray-600">
        Showing <strong>{start}</strong><strong>{end}</strong> of <strong>{total}</strong>
      </div>
      <div className="flex gap-1">
        <button
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className="px-3 py-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
        >
           Prev
        </button>
        {deduped.map((p, i) =>
          p === "" ? (
            <span key={"e" + i} className="px-2 py-1.5 text-gray-400"></span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p as number)}
              className={
                "px-3 py-1.5 rounded-lg border " +
                (p === page
                  ? "bg-aviu-800 text-white border-aviu-800 font-medium"
                  : "border-gray-300 hover:bg-gray-50")
              }
            >
              {p}
            </button>
          )
        )}
        <button
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className="px-3 py-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
        >
          Next 
        </button>
      </div>
    </div>
  );
}
