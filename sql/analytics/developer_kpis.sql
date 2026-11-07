SELECT
    metric_date,
    developer_id,

    sum(total_events) AS total_events,
    sum(total_commits) AS total_commits,
    sum(total_sessions) AS total_sessions,

    round(sum(estimated_activity_minutes), 2)
        AS estimated_activity_minutes,

    if(
        sum(total_sessions) = 0,
        0,
        round(
            sum(estimated_activity_minutes)
            / sum(total_sessions),
            2
        )
    ) AS average_session_minutes,

    sum(total_context_switches) AS total_context_switches,
    sum(total_blocks) AS total_blocks,
    sum(qualifying_blocks) AS qualifying_blocks,

    round(sum(estimated_flow_minutes), 2)
        AS estimated_flow_minutes,

    sum(total_coding_events) AS total_coding_events,
    sum(potential_interruptions) AS potential_interruptions,

    round(
        if(
            sum(total_coding_events) = 0,
            0,
            sum(potential_interruptions) * 100.0
            / sum(total_coding_events)
        ),
        2
    ) AS interruption_rate_pct

FROM cognistream.developer_daily_metrics

WHERE metric_date BETWEEN
    {start_date:Date}
    AND {end_date:Date}

GROUP BY
    metric_date,
    developer_id

ORDER BY
    metric_date,
    developer_id;