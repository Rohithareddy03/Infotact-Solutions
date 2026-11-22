
# CogniStream Query Performance Monitoring

## Objective

Measure the execution performance of ClickHouse analytical
queries and identify slow or failed queries.

## Monitored Information

- Query execution status
- Execution time in milliseconds
- Number of returned rows
- Query failure details
- Slow-query identification
- Average execution time

## Slow Query Threshold

Default threshold: 1000 milliseconds.

A query exceeding this threshold is marked as slow.

The threshold can be configured when executing individual
queries or benchmarking multiple queries.

## Benchmarking

The benchmark module supports multiple named SQL queries.

Examples:

- Developer KPI query
- Developer session analysis
- Interruption analysis
- Flow block analysis

## Database Health Check

The health check executes SELECT 1 to verify whether
ClickHouse is responding successfully.

## Validation

Unit tests use a mocked ClickHouse client to verify:

- Execution-time reporting
- Successful query execution
- Slow-query identification
- Failed-query handling
- Query parameter support
- Benchmark summaries
- Database health checks

## Limitations

Execution time measured by this module includes client-side
query execution and result retrieval.

It is not a pure server-side execution-time measurement.

For detailed server-side analysis, use ClickHouse
system.query_log and EXPLAIN indexes.
