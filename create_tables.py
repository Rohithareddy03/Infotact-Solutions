from pathlib import Path
from src.database.clickhouse_connection import create_clickhouse_client

client = create_clickhouse_client()

def execute_sql_file(file_path, stop_marker=None):
    sql = Path(file_path).read_text(encoding="utf-8")

    if stop_marker:
        sql = sql.split(stop_marker)[0]

    # Remove SQL comment lines
    sql = "\n".join(
        line for line in sql.splitlines()
        if not line.strip().startswith("--")
    )

    statements = [s.strip() for s in sql.split(";") if s.strip()]

    for statement in statements:
        client.command(statement)
        print("Executed:", statement.splitlines()[0][:75])

execute_sql_file("sql/schema/analytics_tables.sql")

execute_sql_file(
    "sql/schema/developer_events.sql.txt",
    stop_marker="### Explanation"
)

print("\nAll six table creation statements executed successfully!")
