export const DB_TYPE_LABELS = {
  postgresql: "PostgreSQL",
  mysql: "MySQL",
  sqlite: "SQLite",
};

export function getDbTypeLabel(dbType) {
  return DB_TYPE_LABELS[dbType] || dbType;
}
