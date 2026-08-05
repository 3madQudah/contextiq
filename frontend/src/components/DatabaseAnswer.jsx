import { motion } from "framer-motion";

import CodeBlock from "./CodeBlock.jsx";
import ResultsTable from "./ResultsTable.jsx";

export default function DatabaseAnswer({ result }) {
  const hasTable = result.columns?.length > 0 && result.rows?.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="max-w-[85%]"
    >
      <p className="text-base text-foreground">{result.answer}</p>

      <div className="mt-3">
        <p className="mb-1.5 text-sm text-muted">SQL used</p>
        <CodeBlock code={result.sql_query} />
      </div>

      {hasTable && (
        <div className="mt-3">
          <ResultsTable columns={result.columns} rows={result.rows} />
        </div>
      )}

      {result.truncated && (
        <p className="mt-2 text-sm text-muted">
          Results were capped at {result.row_count} row{result.row_count === 1 ? "" : "s"} — there may be
          more.
        </p>
      )}
    </motion.div>
  );
}
