WITH bronze_data AS (
    SELECT * 
    FROM {{ ref('bronze_events') }}
),

cleaned_data AS (
    SELECT
        event_id,
        event_name,
        event_url,
        
        target_city,
        target_segment,
        
        CAST(on_sale_timestamp AS TIMESTAMP) AS on_sale_timestamp,
        CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
        
        -- Prices stay NULL when Ticketmaster has no priceRanges (no more fake $0).
        -- The bronze join returns one row per price range, so collapse to the
        -- event's overall floor and ceiling before deduplicating.
        MIN(min_price) OVER (PARTITION BY event_id) AS min_price,
        MAX(max_price) OVER (PARTITION BY event_id) AS max_price,
        
        -- Lead time is only valid when the on-sale date is on/before the event
        -- and within a plausible window (0-730 days). Anything else becomes NULL
        -- so placeholder dates can't distort the averages.
        CASE
            WHEN DATE_DIFF(
                    'day',
                    CAST(on_sale_timestamp AS DATE),
                    CAST(event_timestamp AS DATE)
                 ) BETWEEN 0 AND 730
            THEN DATE_DIFF(
                    'day',
                    CAST(on_sale_timestamp AS DATE),
                    CAST(event_timestamp AS DATE)
                 )
        END AS marketing_lead_time_days
        
    FROM bronze_data
    WHERE event_id IS NOT NULL
    
    QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp DESC) = 1
)

SELECT * FROM cleaned_data