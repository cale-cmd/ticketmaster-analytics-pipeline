# 🎫 Live Entertainment Market Analytics: Automated ELT Pipeline

An end-to-end, cloud-native Analytics Engineering pipeline that extracts live event inventory from the Ticketmaster Discovery API, loads it into a serverless cloud lakehouse, transforms it through a Medallion Architecture, and serves interactive market intelligence via Streamlit.

## 🏗️ Architecture & Tech Stack

* **Data Ingestion:** Python & `dlt` (Data Load Tool) — Memory-optimized generator extraction with rate-limit handling, parameter iteration, and automatic relational normalization of nested JSON arrays.
* **Cloud Data Warehouse:** **MotherDuck** (Serverless Cloud DuckDB) — Zero-copy analytical storage.
* **Transformation & Testing:** **dbt Core** (`dbt-duckdb`) — Modular SQL transformations structured in a Bronze, Silver, and Gold Medallion Architecture with automated data quality tests.
* **Orchestration (CI/CD):** **GitHub Actions** — Automated daily cron schedule executing extraction, transformation, and schema testing hands-free.
* **BI & Presentation:** **Streamlit**  — Live interactive dashboard querying the Gold layer directly from MotherDuck.

---

## 📊 Business Problem & Key Metrics

This pipeline is designed to help event promoters, tour managers, and ticket brokers evaluate market dynamics across major US entertainment hubs (**New York, Los Angeles, and Chicago**) and segments (**Music, Sports, and Arts & Theatre**):

1. **Genre Saturation (Event Density):** Identifies oversaturated vs. underserved entertainment segments across target metropolitan markets to optimize tour routing.
2. **Cross-Market Pricing Power:** Compares average price floors and ceilings (`min_price` / `max_price`) across cities and genres to gauge consumer willingness to pay.
3. **Marketing Lead-Time (The Pacing Curve):** Calculates the delta in days between public on-sale timestamps and event dates (`DATE_DIFF`) to reveal how far in advance regional promoters launch ticket sales.

---

## 🥇 Medallion Architecture (`dbt`)

* **Raw Layer (`dlt`):** Ingests paginated JSON responses from the `/discovery/v2/events` endpoint and normalizes nested arrays (`priceRanges`) into relational parent-child tables (`ticketmaster_events` and `ticketmaster_events__price_ranges`).
* **Bronze Layer (`view`):** Acts as a schema shock-absorber. Performs `LEFT JOIN` operations using `_dlt_id` keys, standardizes column aliases, and casts pricing and timestamp data types.
* **Silver Layer (`view`):** Enforces data hygiene. Handles missing pricing values via `COALESCE`, calculates `marketing_lead_time_days`, and guarantees strict record deduplication using `QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id)`. Enforces `unique` and `not_null` schema tests.
* **Gold Layer (`table`):** Pre-aggregates event counts, average price floors/ceilings, and lead-time metrics grouped by city and segment for sub-second dashboard queries.

---

## 🚀 Running Locally

1. Clone the repository and set up the virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt