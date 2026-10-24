import streamlit as st
import duckdb
import pandas as pd
import altair as alt

# Minimum sample size before a group is shown in the price / lead-time charts
MIN_SAMPLE = 30

# Dashboard Configuration
st.set_page_config(page_title="Ticketmaster Market Analytics", layout="wide")
st.title("🎫 Ticketmaster Market Analytics")
st.markdown("Pipeline metrics from the dbt Gold layer, refreshed daily.")


# 1. Load Data (cache expires hourly; data only changes with the daily pipeline run)
@st.cache_data(ttl=3600)
def load_data():
    token = st.secrets["MOTHERDUCK_TOKEN_READ"]  # set in .streamlit/secrets.toml locally, or in the app's Secrets settings when deployed
    # read_only=True prevents database locking conflicts
    with duckdb.connect(f"md:my_db?motherduck_token={token}", read_only=True) as conn:
        return conn.execute("SELECT * FROM main.gold_metrics").df()


df = load_data()


# Weighted average: each group counts in proportion to the rows that feed its metric
def wavg(col, weight):
    m = df[col].notna() & (df[weight] > 0)
    total = df.loc[m, weight].sum()
    if total == 0:
        return None
    return (df.loc[m, col] * df.loc[m, weight]).sum() / total


# Dynamic data-quality notes
priced_share = df["priced_events"].sum() / df["total_events"].sum()
valid_lead_share = df["valid_lead_time_events"].sum() / df["total_events"].sum()

st.caption(
    f"Price data available for {priced_share:.0%} of events; "
    f"valid lead time for {valid_lead_share:.0%}."
)

# 2. Top-Level KPI Metrics
st.subheader("Market Averages")
col1, col2, col3 = st.columns(3)

avg_price = wavg("avg_min_price", "priced_events")
avg_lead = wavg("avg_lead_time_days", "valid_lead_time_events")

col1.metric("Total Tracked Events", f"{int(df['total_events'].sum()):,}")
col2.metric("Avg Minimum Price", f"${avg_price:.2f}" if avg_price is not None else "n/a")
col3.metric("Avg Lead Time (Days)", f"{avg_lead:.1f}" if avg_lead is not None else "n/a")

# Filtered views for charts that need a minimum sample size
df_price = df[df["priced_events"] >= MIN_SAMPLE]
df_lead = df[df["valid_lead_time_events"] >= MIN_SAMPLE]

# 3. Visualizations - row 1
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Genre Saturation (Event Volume)")
    saturation_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("target_city:N", title="City", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("total_events:Q", title="Total Events"),
        color=alt.Color("target_segment:N", title="Segment"),
        tooltip=["target_city", "target_segment", "total_events"],
    )
    st.altair_chart(saturation_chart, width="stretch")

with col_chart2:
    st.subheader("Cross-Market Pricing Power")
    pricing_chart = alt.Chart(df_price).mark_bar().encode(
        x=alt.X("target_segment:N", title="Segment", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("avg_min_price:Q", title="Avg Min Price ($)"),
        color=alt.Color("target_city:N", title="City"),
        xOffset="target_city:N",
        tooltip=["target_city", "target_segment", "avg_min_price", "priced_events"],
    )
    st.altair_chart(pricing_chart, width="stretch")
    st.caption(f"Groups with fewer than {MIN_SAMPLE} priced events are hidden.")

# 3. Visualizations - row 2
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("Price Floor to Ceiling")
    range_chart = alt.Chart(df_price).mark_bar().encode(
        x=alt.X("avg_min_price:Q", title="Avg Price Range ($)"),
        x2="avg_max_price:Q",
        y=alt.Y("target_segment:N", title="Segment"),
        yOffset="target_city:N",
        color=alt.Color("target_city:N", title="City"),
        tooltip=[
            "target_city",
            "target_segment",
            "avg_min_price",
            "avg_max_price",
            "priced_events",
        ],
    )
    st.altair_chart(range_chart, width="stretch")
    st.caption(f"Groups with fewer than {MIN_SAMPLE} priced events are hidden.")

with col_chart4:
    st.subheader("Median Booking Lead Time")
    lead_chart = alt.Chart(df_lead).mark_bar().encode(
        x=alt.X("target_segment:N", title="Segment", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("median_lead_time_days:Q", title="Median Lead Time (days)"),
        color=alt.Color("target_city:N", title="City"),
        xOffset="target_city:N",
        tooltip=[
            "target_city",
            "target_segment",
            "median_lead_time_days",
            "valid_lead_time_events",
        ],
    )
    st.altair_chart(lead_chart, width="stretch")
    st.caption(
        f"Groups with fewer than {MIN_SAMPLE} valid lead times are hidden. "
        "Lead time is limited to 0-730 days."
    )

# 4. Raw Gold Layer Data
st.subheader("Gold Layer Outputs")
st.dataframe(df, width="stretch")