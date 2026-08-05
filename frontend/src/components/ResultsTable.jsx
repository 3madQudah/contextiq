export default function ResultsTable({ columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-hover">
            {columns.map((col, i) => (
              <th key={i} className="whitespace-nowrap px-3 py-2 font-medium text-foreground">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} className="whitespace-nowrap px-3 py-2 text-foreground">
                  {cell === null || cell === undefined ? (
                    <span className="italic text-muted">NULL</span>
                  ) : (
                    String(cell)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
