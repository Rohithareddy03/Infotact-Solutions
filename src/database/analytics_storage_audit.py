
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# Only predefined table names and date expressions are used.
# This prevents user-provided SQL identifiers.
ANALYTICS_TABLES = {
    "developer_sessions": "toDate(session_start)",
    "context_switches": "toDate(from_timestamp)",
    "flow_blocks": "toDate(block_start)",
    "potential_interruptions": "toDate(interruption_timestamp)",
    "developer_daily_metrics": "metric_date",
}


def validate_metric_date(metric_date):
    """Validate and normalize a YYYY-MM-DD date."""

    if isinstance(metric_date, datetime):
        raise ValueError("Datetime values are not accepted. Use YYYY-MM-DD.")

    if isinstance(metric_date, date):
        return metric_date.isoformat()

    if not isinstance(metric_date, str):
        raise ValueError("Metric date must be a date object or YYYY-MM-DD string.")

    try:
        parsed_date = date.fromisoformat(metric_date)
    except ValueError as exc:
        raise ValueError("Invalid metric date. Expected YYYY-MM-DD.") from exc

    if parsed_date.isoformat() != metric_date:
        raise ValueError("Invalid metric date. Expected YYYY-MM-DD.")

    return parsed_date.isoformat()


def audit_analytics_storage(client, metric_date):
    """
    Audit daily record counts across all analytics tables.

    Each table is checked independently. A failure in one table
    does not prevent the remaining tables from being checked.

    Returns a JSON-serializable audit report.
    """

    normalized_date = validate_metric_date(metric_date)

    table_results = {}
    successful_tables = 0
    failed_tables = 0

    for table_name, date_column in ANALYTICS_TABLES.items():
        query = (
            f"SELECT count() AS record_count "
            f"FROM {table_name} "
            f"WHERE {date_column} = {{metric_date:Date}}"
        )

        try:
            result = client.query(
                query,
                parameters={"metric_date": normalized_date},
            )

            record_count = int(result.result_rows[0][0])

            table_results[table_name] = {
                "status": "success",
                "record_count": record_count,
            }

            successful_tables += 1

            logger.info(
                "Storage audit successful for %s: %s records",
                table_name,
                record_count,
            )

        except Exception as exc:
            table_results[table_name] = {
                "status": "failed",
                "error": str(exc),
            }

            failed_tables += 1

            logger.exception(
                "Storage audit failed for table %s",
                table_name,
            )

    if successful_tables == len(ANALYTICS_TABLES):
        overall_status = "success"
    elif successful_tables > 0:
        overall_status = "partial"
    else:
        overall_status = "failed"

    return {
        "metric_date": normalized_date,
        "status": overall_status,
        "total_tables": len(ANALYTICS_TABLES),
        "successful_tables": successful_tables,
        "failed_tables": failed_tables,
        "tables": table_results,
    }
