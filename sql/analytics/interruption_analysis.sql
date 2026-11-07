SELECT
    developer_id,

    count() AS potential_interruptions,

    round(avg(minutes_after_coding), 2)
        AS average_minutes_after_coding,

    min(interruption_timestamp) AS first_interruption,

    max(interruption_timestamp) AS last_interruption

FROM cognistream.potential_interruptions

WHERE interruption_timestamp >=
    toDateTime(concat(toString({start_date:Date}), ' 00:00:00'), 'UTC')

AND interruption_timestamp <
    toDateTime(concat(toString({end_date_exclusive:Date}), ' 00:00:00'), 'UTC')

GROUP BY developer_id

ORDER BY potential_interruptions DESC;