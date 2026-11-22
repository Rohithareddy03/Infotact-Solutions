import clickhouse_connect

from src.api import config


def get_clickhouse_client():
    """Create and return a ClickHouse client."""
    try:
        client = clickhouse_connect.get_client(
            host=config.CLICKHOUSE_HOST,
            port=config.CLICKHOUSE_PORT,
            username=config.CLICKHOUSE_USER,
            password=config.CLICKHOUSE_PASSWORD,
            database=config.CLICKHOUSE_DATABASE,
        )
        return client

    except Exception as exc:
        raise ConnectionError(
            "Unable to connect to the ClickHouse database."
        ) from exc
