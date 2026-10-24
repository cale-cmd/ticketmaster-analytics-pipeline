import duckdb

# 1. Connect to your local database file
conn = duckdb.connect("ticketmaster.duckdb")

# 2. List all tables across all schemas (including 'raw')
print("--- My Tables ---")
conn.sql("SHOW ALL TABLES").show()

# 3. Query the first 5 rows of your joined events table 
print("\n--- My Event Data ---")
query = """
SELECT * 
FROM raw.ticketmaster_events AS parent 
LEFT JOIN raw.ticketmaster_events__price_ranges AS prices 
    ON parent._dlt_id = prices._dlt_parent_id
LIMIT 5
"""
test = conn.execute(query).fetch_df()
print(test)

# 4. Properly close the connection
conn.close()