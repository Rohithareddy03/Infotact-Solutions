SELECT
    developer_id,

    count() AS session_count,

    round(avg(duration_minutes), 2)
        AS average_session_minutes,

    round(max(duration_minutes), 2)
        AS longest_session_minutes,

    round(sum(duration_minutes), 2)
        AS total_activity_minutes,

    sum(event_count) AS total_session_events

FROM cognistream.developer_sessions

WHERE session_start >=
    toDateTime(concat(toString({start_date:Date}), ' 00:00:00'), 'UTC')

AND session_start <
    toDateTime(concat(toString({end_date_exclusive:Date}), ' 00:00:00'), 'UTC')

GROUP BY developer_id

ORDER BY total_activity_minutes DESC;