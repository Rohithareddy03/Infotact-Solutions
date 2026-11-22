
import time
from datetime import datetime, timezone

from src.database.clickhouse_connection import (
    create_clickhouse_client,
)

DEFAULT_SLOW_QUERY_THRESHOLD_MS = 1000


def execute_monitored_query(
    client,
    query: str,
    parameters: dict = None,
    slow_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS,
):
    """Execute a query and monitor its performance."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")

    if slow_threshold_ms < 0:
        raise ValueError("Threshold cannot be negative")

    executed_at = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()

    try:
        if parameters is None:
            result = client.query(query)
        else:
            result = client.query(query, parameters=parameters)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        rows = result.result_rows or []

        return {
            "status": "success",
            "executed_at": executed_at,
            "execution_time_ms": round(elapsed_ms, 3),
            "rows_returned": len(rows),
            "slow_query": elapsed_ms > slow_threshold_ms,
            "threshold_ms": slow_threshold_ms,
            "error": None,
            "result": result,
        }

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "status": "failed",
            "executed_at": executed_at,
            "execution_time_ms": round(elapsed_ms, 3),
            "rows_returned": 0,
            "slow_query": elapsed_ms > slow_threshold_ms,
            "threshold_ms": slow_threshold_ms,
            "error": str(exc),
            "result": None,
        }


def benchmark_analytics_queries(
    queries: dict,
    client=None,
    slow_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS,
):
    """Benchmark multiple named analytical queries."""

    if not isinstance(queries, dict):
        raise ValueError("Queries must be a dictionary")

    if slow_threshold_ms < 0:
        raise ValueError("Threshold cannot be negative")

    if client is None:
        client = create_clickhouse_client()

    results = {}

    for name, query in queries.items():
        results[name] = execute_monitored_query(
            client,
            query,
            slow_threshold_ms=slow_threshold_ms,
        )

    successful = [
        item for item in results.values()
        if item["status"] == "success"
    ]

    failed = [
        item for item in results.values()
        if item["status"] == "failed"
    ]

    slow = [
        name for name, item in results.items()
        if item["slow_query"]
    ]

    average_time = (
        sum(item["execution_time_ms"] for item in successful)
        / len(successful)
        if successful else 0
    )

    return {
        "total_queries": len(results),
        "successful_queries": len(successful),
        "failed_queries": len(failed),
        "slow_queries": slow,
        "average_execution_time_ms": round(average_time, 3),
        "threshold_ms": slow_threshold_ms,
        "query_results": results,
    }


def run_database_health_check(
    client=None,
    slow_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS,
):
    """Check ClickHouse connectivity using SELECT 1."""

    if client is None:
        client = create_clickhouse_client()

    return execute_monitored_query(
        client,
        "SELECT 1",
        slow_threshold_ms=slow_threshold_ms,
    )

