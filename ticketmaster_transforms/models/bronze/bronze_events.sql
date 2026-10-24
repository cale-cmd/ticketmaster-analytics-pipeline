SELECT
    parent.id AS event_id,
    parent.name AS event_name,
    parent.url AS event_url,
    
    parent.target_city,
    parent.target_segment,
    
    parent.sales__public__start_date_time AS on_sale_timestamp,
    parent.dates__start__date_time AS event_timestamp,
    
    CAST(prices.min AS FLOAT) AS min_price,
    CAST(prices.max AS FLOAT) AS max_price

FROM {{ source('ticketmaster_source', 'ticketmaster_events') }} AS parent
LEFT JOIN {{ source('ticketmaster_source', 'ticketmaster_events__price_ranges') }} AS prices
    ON parent._dlt_id = prices._dlt_parent_id