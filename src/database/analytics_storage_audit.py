

from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# These names and date expressions must match the existing
# ClickHouse analytics schema.
ANALYTICS_TABLES = {
    "developer_sessions": "toDate(session_start)",
    "context_switches": "toDate(from_timestamp)",
    "flow_blocks": "toDate(block_start)",
    "potential_interruptions": "toDate(interruption_timestamp)",
    "developer_daily_metrics": "metric_date",
}


def validate_metric_date(metric_date):
    """Validate and normalize a date to YYYY-MM-DD."""

    if isinstance(metric_date, datetime):
        raise ValueError("Provide a date, not a datetime.")

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


def audit_analytics_storage(client, metric_date, selected_tables=None):
    """
    Audit daily record counts in selected ClickHouse analytics tables.

    Args:
        client: Existing ClickHouse client.
        metric_date: Date object or YYYY-MM-DD string.
        selected_tables: Optional list/tuple of table names.
                         Defaults to all five analytics tables.

    Returns:
        JSON-serializable dictionary containing table results,
        total records, errors, and overall status.

    Raises:
        ValueError: If the date or selected table names are invalid.
    """

    normalized_date = validate_metric_date(metric_date)

    if selected_tables is None:
        tables_to_audit = list(ANALYTICS_TABLES)
    else:
        if not isinstance(selected_tables, (list, tuple)):
            raise ValueError("selected_tables must be a list or tuple.")

        if not selected_tables:
            raise ValueError("Select at least one analytics table.")

        unknown_tables = [
            name for name in selected_tables
            if name not in ANALYTICS_TABLES
        ]

        if unknown_tables:
            raise ValueError(
                f"Unknown analytics table(s): {', '.join(map(str, unknown_tables))}"
            )

        # Remove duplicates while preserving the requested order.
        tables_to_audit = list(dict.fromkeys(selected_tables))

    table_results = {}
    errors = {}
    successful_tables = 0
    failed_tables = 0
    total_records = 0

    for table_name in tables_to_audit:

        if client is None:
            error_message = "ClickHouse client is not provided."
            table_results[table_name] = {
                "status": "failed",
                "error": error_message,
            }
            errors[table_name] = error_message
            failed_tables += 1
            continue

        date_expression = ANALYTICS_TABLES[table_name]

        query = (
            f"SELECT count() "
            f"FROM {table_name} "
            f"WHERE {date_expression} = {{metric_date:Date}}"
        )

        try:
            result = client.query(
                query,
                parameters={"metric_date": normalized_date},
            )

            if not result.result_rows:
                raise ValueError("ClickHouse returned no count result.")

            record_count = int(result.result_rows[0][0])

            if record_count < 0:
                raise ValueError("ClickHouse returned a negative record count.")

            table_results[table_name] = {
                "status": "success",
                "record_count": record_count,
            }

            successful_tables += 1
            total_records += record_count

        except Exception as exc:
            error_message = str(exc)

            table_results[table_name] = {
                "status": "failed",
                "error": error_message,
            }

            errors[table_name] = error_message
            failed_tables += 1

            logger.exception("Storage audit failed for %s", table_name)

    if failed_tables == 0:
        overall_status = "success"
    elif successful_tables > 0:
        overall_status = "partial"
    else:
        overall_status = "failed"

    return {
        "metric_date": normalized_date,
        "status": overall_status,
        "total_tables": len(tables_to_audit),
        "successful_tables": successful_tables,
        "failed_tables": failed_tables,
        "total_records": total_records,
        "tables": table_results,
        "errors": errors,
    }
