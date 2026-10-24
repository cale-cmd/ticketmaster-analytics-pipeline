WITH silver_data AS (
    SELECT * 
    FROM {{ ref('silver_events') }}
),

event_summary AS (
    SELECT
        target_city,
        target_segment,
        
        COUNT(event_id) AS total_events,
        
        -- AVG ignores NULLs, so these only reflect events that actually have prices
        AVG(min_price) AS avg_min_price,
        AVG(max_price) AS avg_max_price,
        
        -- Lead time is bounded to 0-730 days in silver
        AVG(marketing_lead_time_days) AS avg_lead_time_days,
        MEDIAN(marketing_lead_time_days) AS median_lead_time_days,
        
        -- Sample sizes: how many events each metric is actually based on
        COUNT(min_price) AS priced_events,
        COUNT(marketing_lead_time_days) AS valid_lead_time_events,
        COUNT(*) FILTER (WHERE marketing_lead_time_days IS NULL) AS events_without_valid_lead_time
        
    FROM silver_data
    GROUP BY 
        target_city,
        target_segment
)

SELECT * FROM event_summary