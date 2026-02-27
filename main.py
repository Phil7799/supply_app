import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import os
import json

# Set page configuration to wide
st.set_page_config(
    page_title="Supply Dashboard",
    page_icon="https://res.cloudinary.com/dnq8ne9lx/image/upload/v1753860594/infograph_ewfmm6.ico",
    layout="wide"
)

# Loading data
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'requests.xlsx')
    df = pd.read_excel(file_path)
    return df

df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.title('Filters')

selected_cities = st.sidebar.multiselect('Select City', ['All'] + sorted(df['CITY'].unique(), key=str))
selected_vehicle_types = st.sidebar.multiselect('Select Vehicle Type', ['All'] + sorted(df['VEHICLETYPE'].astype(str).unique()))
selected_date_from = st.sidebar.date_input('Select Date From')
selected_date_to = st.sidebar.date_input('Select Date To')
selected_driver = st.sidebar.selectbox('Select Driver', ['All'] + sorted(df['DRIVER'].astype(str).unique()))
selected_trip_type = st.sidebar.selectbox('Select Trip Type', ['All'] + sorted(df['TRIPTYPE'].astype(str).unique()))
selected_rider = st.sidebar.selectbox('Select Rider', ['All'] + sorted(df['Rider Mobile Number'].astype(str).unique()))
selected_country = st.sidebar.selectbox('Select Country', ['All'] + sorted(df['COUNTRY'].astype(str).unique()))
selected_region = st.sidebar.selectbox('Select Region', ['All'] + sorted(df['Region'].unique(), key=str))
selected_corporate = st.sidebar.selectbox('Select Corporate', ['All'] + sorted(df['Corporate'].unique(), key=str))

# ── NEW: Distance from Rider range filter ──
st.sidebar.markdown("---")
st.sidebar.subheader("📏 Distance from Rider Filter")
dist_col = 'DISTANCE FROM RIDER'
dist_min_val = float(df[dist_col].min())
dist_max_val = float(df[dist_col].max())
dist_range = st.sidebar.slider(
    'Distance from Rider (km)',
    min_value=dist_min_val,
    max_value=dist_max_val,
    value=(dist_min_val, dist_max_val),
    step=0.5
)

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
selected_date_from = pd.Timestamp(selected_date_from)
selected_date_to = pd.Timestamp(selected_date_to)

filtered_df = df[
    ((df['CITY'].isin(selected_cities)) | ('All' in selected_cities)) &
    ((df['VEHICLETYPE'].astype(str).isin(selected_vehicle_types)) | ('All' in selected_vehicle_types)) &
    ((df['Date'] >= selected_date_from) & (df['Date'] <= selected_date_to)) &
    ((df['DRIVER'] == selected_driver) | (selected_driver == 'All')) &
    ((df['TRIPTYPE'] == selected_trip_type) | (selected_trip_type == 'All')) &
    ((df['Rider Mobile Number'].astype(str) == selected_rider) | (selected_rider == 'All')) &
    ((df['COUNTRY'] == selected_country) | (selected_country == 'All')) &
    ((df['Region'] == selected_region) | (selected_region == 'All')) &
    ((df['Corporate'] == selected_corporate) | (selected_corporate == 'All')) &
    ((df[dist_col] >= dist_range[0]) & (df[dist_col] <= dist_range[1]))  # distance filter
]

# Drop rows with NaN Lat/Lon for map
map_df = filtered_df.dropna(subset=['Latitude', 'Longitude']).copy()

# ─────────────────────────────────────────────
# KPI CALCULATIONS
# ─────────────────────────────────────────────
total_requests = len(filtered_df)
total_trips = filtered_df[filtered_df['Category'] == 'Trips'].shape[0]
driver_cancellations_kpi = filtered_df[filtered_df['Category'] == 'Driver Cancellation'].shape[0]
rider_cancellations_kpi = filtered_df[filtered_df['Category'] == 'Rider Cancellation'].shape[0]
no_driver_found = filtered_df[filtered_df['Category'] == 'No Drivers Found'].shape[0]
timeouts_kpi = filtered_df[filtered_df['Category'] == 'Timeout'].shape[0]

if total_trips == 0:
    fulfillment_rate = 0
    acceptance_rate = 0
    driver_canc_rate = 0
else:
    fulfillment_rate = round((total_trips * 100) / max(total_trips + driver_cancellations_kpi + rider_cancellations_kpi, 1), 2)
    acceptance_rate = round((total_trips * 100) / max(total_trips + driver_cancellations_kpi + rider_cancellations_kpi + timeouts_kpi, 1), 2)
    driver_canc_rate = round((driver_cancellations_kpi * 100) / max(total_trips + driver_cancellations_kpi + rider_cancellations_kpi + timeouts_kpi, 1), 2)

# ─────────────────────────────────────────────
# DASHBOARD TITLE & KPIs
# ─────────────────────────────────────────────
st.title('🚕 Supply Requests Dashboard')

# Show active distance filter info
st.info(f"📏 Distance from Rider filter active: **{dist_range[0]} – {dist_range[1]} km** | Showing **{total_requests}** requests")

st.write('## Supply KPIs')

kpi_data = {
    'Total Requests': total_requests,
    'Total Trips': total_trips,
    'Driver Cancellations': driver_cancellations_kpi,
    'Rider Cancellations': rider_cancellations_kpi,
    'Timeouts': timeouts_kpi,
    'No Driver Found Cases': no_driver_found,
    'Fulfillment Rate (%)': fulfillment_rate,
    'Acceptance Rate (%)': acceptance_rate,
    'Driver Cancellation Rate (%)': driver_canc_rate
}

box_style = """
    background-color: #00008B;
    color: white;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 10px;
    font-size: 18px;
    font-style: italic;
"""

col1, col2, col3 = st.columns(3)
with col1:
    for k, v in kpi_data.items():
        if k in ['Total Requests', 'Total Trips', 'Driver Cancellations']:
            st.markdown(f'<div style="{box_style}">{k}: {v}</div>', unsafe_allow_html=True)
with col2:
    for k, v in kpi_data.items():
        if k in ['Rider Cancellations', 'Timeouts', 'No Driver Found Cases']:
            st.markdown(f'<div style="{box_style}">{k}: {v}</div>', unsafe_allow_html=True)
with col3:
    for k, v in kpi_data.items():
        if k in ['Fulfillment Rate (%)', 'Acceptance Rate (%)', 'Driver Cancellation Rate (%)']:
            st.markdown(f'<div style="{box_style}">{k}: {v}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RAW DATA
# ─────────────────────────────────────────────
st.write('## 📑 Filtered Raw Data')
st.write(filtered_df)

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
st.write('## 📊 Data Visualization')

request_count_by_date = filtered_df.groupby(['VEHICLETYPE', 'Date']).size().reset_index(name='count')
chart1 = alt.Chart(request_count_by_date).mark_line(interpolate='basis').encode(
    x=alt.X('Date:T', axis=alt.Axis(format='%Y-%m-%d'), title='Date'),
    y=alt.Y('count:Q', title='Request Count'),
    color='VEHICLETYPE:N',
    tooltip=['Date', 'count']
).properties(width=1500, height=400, title='Request Count by Vehicle Type Over Time').interactive()
st.altair_chart(chart1)

request_count_by_hour = filtered_df.groupby(['Category', 'Hour']).size().reset_index(name='count')
chart2 = alt.Chart(request_count_by_hour).mark_line(interpolate='basis').encode(
    x=alt.X('Hour:O', title='Hour'),
    y=alt.Y('count:Q', title='Request Count'),
    color='Category:N',
    tooltip=['Hour', 'count']
).properties(width=1500, height=400, title='Request Count by Category Over Hour').interactive()
st.altair_chart(chart2)

# ─────────────────────────────────────────────
# HEAT MAPS (NEW)
# ─────────────────────────────────────────────
st.write('## 🌡️ Hourly Heatmaps by Region')

# ── Heatmap 1: Fulfillment Rate by Region & Hour ──
st.write('### Fulfilment Rate Heatmap (Region × Hour)')

# Build pivot: trips / (trips + driver_canc + rider_canc)
def compute_fulfillment_pivot(data):
    trips = data[data['Category'] == 'Trips'].groupby(['Region', 'Hour']).size().reset_index(name='Trips')
    dc = data[data['Category'] == 'Driver Cancellation'].groupby(['Region', 'Hour']).size().reset_index(name='DC')
    rc = data[data['Category'] == 'Rider Cancellation'].groupby(['Region', 'Hour']).size().reset_index(name='RC')
    merged = trips.merge(dc, on=['Region', 'Hour'], how='left').merge(rc, on=['Region', 'Hour'], how='left').fillna(0)
    merged['Fulfillment Rate (%)'] = (merged['Trips'] / (merged['Trips'] + merged['DC'] + merged['RC']).clip(lower=1)) * 100
    return merged

fr_data = compute_fulfillment_pivot(filtered_df)

if not fr_data.empty:
    all_regions_fr = sorted(fr_data['Region'].unique().tolist(), key=str)
    heatmap_fr = alt.Chart(fr_data).mark_rect().encode(
        x=alt.X('Hour:O', title='Hour of Day', sort=list(range(24))),
        y=alt.Y('Region:N', title='Region', sort=all_regions_fr,
                axis=alt.Axis(labelLimit=200)),
        color=alt.Color('Fulfillment Rate (%):Q',
                        scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100]),
                        legend=alt.Legend(title='Fulfilment Rate (%)')),
        tooltip=['Region', 'Hour', 'Fulfillment Rate (%)', 'Trips', 'DC', 'RC']
    ).properties(
        width=900,
        height=max(300, len(all_regions_fr) * 30),
        title='Hourly Fulfilment Rate by Region'
    ).interactive()
    st.altair_chart(heatmap_fr, use_container_width=True)
else:
    st.warning("Not enough data for the Fulfilment Rate heatmap with current filters.")

# ── Heatmap 2: Total Requests by Region & Hour ──
st.write('### Total Requests Heatmap (Region × Hour)')

req_by_region_hour = filtered_df.groupby(['Region', 'Hour']).size().reset_index(name='Total Requests')

if not req_by_region_hour.empty:
    all_regions_req = sorted(req_by_region_hour['Region'].unique().tolist(), key=str)
    heatmap_req = alt.Chart(req_by_region_hour).mark_rect().encode(
        x=alt.X('Hour:O', title='Hour of Day', sort=list(range(24))),
        y=alt.Y('Region:N', title='Region', sort=all_regions_req,
                axis=alt.Axis(labelLimit=200)),
        color=alt.Color('Total Requests:Q',
                        scale=alt.Scale(scheme='blues'),
                        legend=alt.Legend(title='Total Requests')),
        tooltip=['Region', 'Hour', 'Total Requests']
    ).properties(
        width=900,
        height=max(300, len(all_regions_req) * 30),
        title='Hourly Total Requests by Region'
    ).interactive()
    st.altair_chart(heatmap_req, use_container_width=True)
else:
    st.warning("Not enough data for the Total Requests heatmap with current filters.")

# ─────────────────────────────────────────────
# MAP (FIXED)
# ─────────────────────────────────────────────
st.write('## 🌍 Map of Requests')

if map_df.empty:
    st.warning("No data with valid coordinates to display on the map.")
else:
    map_df = map_df.rename(columns={'Latitude': 'LAT', 'Longitude': 'LON'})

    # Color by category
    category_colors = {
        'Trips': [0, 200, 100, 180],
        'Driver Cancellation': [255, 100, 0, 180],
        'Rider Cancellation': [255, 200, 0, 180],
        'No Drivers Found': [150, 0, 200, 180],
        'Timeout': [200, 0, 0, 180],
    }
    map_df['color'] = map_df['Category'].map(lambda c: category_colors.get(c, [100, 100, 100, 160]))

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_df,
        get_position='[LON, LAT]',
        get_radius=80,
        get_fill_color='color',
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=map_df['LAT'].mean(),
        longitude=map_df['LON'].mean(),
        zoom=10,
        pitch=40,
    )

    tooltip = {
        "html": "<b>Category:</b> {Category}<br/><b>Driver:</b> {DRIVER}<br/><b>City:</b> {CITY}<br/><b>Region:</b> {Region}<br/><b>Distance:</b> {DISTANCE FROM RIDER} km",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    r = pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )
    st.pydeck_chart(r)

    # Legend
    st.markdown("""
    **Map Legend:**
    🟢 Trips &nbsp;&nbsp; 🟠 Driver Cancellation &nbsp;&nbsp; 🟡 Rider Cancellation &nbsp;&nbsp; 🟣 No Drivers Found &nbsp;&nbsp; 🔴 Timeout
    """)

# ─────────────────────────────────────────────
# HELPER: build KPI table for a groupby column
# ─────────────────────────────────────────────
def build_kpi_table(data, group_col):
    data = data[data['Category'] != 'No Drivers Found']
    requests = data.groupby(group_col).size().reset_index(name='Total Requests')
    trips = data[data['Category'] == 'Trips'].groupby(group_col).size().reset_index(name='Total Trips')
    dc = data[data['Category'] == 'Driver Cancellation'].groupby(group_col).size().reset_index(name='Driver Cancellation')
    rc = data[data['Category'] == 'Rider Cancellation'].groupby(group_col).size().reset_index(name='Rider Cancellation')
    to = data[data['Category'] == 'Timeout'].groupby(group_col).size().reset_index(name='Timeout')

    kpis = requests.merge(trips, on=group_col, how='left') \
                   .merge(dc, on=group_col, how='left') \
                   .merge(rc, on=group_col, how='left') \
                   .merge(to, on=group_col, how='left')
    kpis.fillna(0, inplace=True)

    kpis['Fulfillment Rate (%)'] = (kpis['Total Trips'] / (kpis['Total Trips'] + kpis['Driver Cancellation'] + kpis['Rider Cancellation']).clip(lower=1)) * 100
    kpis['Acceptance Rate (%)'] = (kpis['Total Trips'] / (kpis['Total Trips'] + kpis['Driver Cancellation'] + kpis['Rider Cancellation'] + kpis['Timeout']).clip(lower=1)) * 100
    kpis['Driver Cancellation Rate (%)'] = (kpis['Driver Cancellation'] / kpis['Total Requests'].clip(lower=1)) * 100
    kpis['Rider Cancellation (%)'] = (kpis['Rider Cancellation'] / kpis['Total Requests'].clip(lower=1)) * 100
    kpis['Timeout Rate (%)'] = (kpis['Timeout'] / kpis['Total Requests'].clip(lower=1)) * 100
    return kpis

# ─────────────────────────────────────────────
# DATA TABLES
# ─────────────────────────────────────────────
st.write('## 📈 Driver Data Table')
st.write(build_kpi_table(filtered_df.copy(), 'DRIVER'))

st.write('## 📈 Clients Data Table')
st.write(build_kpi_table(filtered_df.copy(), 'Rider Mobile Number'))

st.write('## 📈 Regions Data Table')
st.write(build_kpi_table(filtered_df.copy(), 'Region'))

st.write('## 📈 Corporate Data Table')
st.write(build_kpi_table(filtered_df.copy(), 'Corporate'))

# ─────────────────────────────────────────────
# CHATBOT (NEW)
# ─────────────────────────────────────────────

def _local_answer(question, kpi_dict, data, d_range):
    """Fallback local answering when API is unavailable."""
    q = question.lower()
    region_kpis = build_kpi_table(data.copy(), 'Region')

    if 'fulfillment' in q or 'fulfilment' in q:
        if 'region' in q or 'best' in q or 'highest' in q:
            if not region_kpis.empty:
                best = region_kpis.loc[region_kpis['Fulfillment Rate (%)'].idxmax()]
                return (f"The region with the highest fulfilment rate is **{best['Region']}** "
                        f"at **{best['Fulfillment Rate (%)']:.2f}%** "
                        f"({int(best['Total Trips'])} trips out of {int(best['Total Requests'])} requests).")
        if 'lowest' in q or 'worst' in q:
            if not region_kpis.empty:
                worst = region_kpis.loc[region_kpis['Fulfillment Rate (%)'].idxmin()]
                return (f"The region with the lowest fulfilment rate is **{worst['Region']}** "
                        f"at **{worst['Fulfillment Rate (%)']:.2f}%**.")
        return (f"The overall **Fulfilment Rate** for the current filters is **{kpi_dict['Fulfillment Rate (%)']}%**. "
                f"This is based on {kpi_dict['Total Trips']} trips vs "
                f"{kpi_dict['Driver Cancellations']} driver cancellations and "
                f"{kpi_dict['Rider Cancellations']} rider cancellations.")

    if 'acceptance' in q:
        return (f"The overall **Acceptance Rate** is **{kpi_dict['Acceptance Rate (%)']}%**. "
                f"Calculated from {kpi_dict['Total Trips']} trips against all outcomes including "
                f"{kpi_dict['Timeouts']} timeouts.")

    if 'summary' in q or 'overview' in q:
        return (f"**Dashboard Summary** (Distance filter: {d_range[0]}–{d_range[1]} km)\n\n"
                f"- Total Requests: **{kpi_dict['Total Requests']}**\n"
                f"- Total Trips: **{kpi_dict['Total Trips']}**\n"
                f"- Fulfilment Rate: **{kpi_dict['Fulfillment Rate (%)']}%**\n"
                f"- Acceptance Rate: **{kpi_dict['Acceptance Rate (%)']}%**\n"
                f"- Driver Cancellations: **{kpi_dict['Driver Cancellations']}** "
                f"({kpi_dict['Driver Cancellation Rate (%)']}%)\n"
                f"- Rider Cancellations: **{kpi_dict['Rider Cancellations']}**\n"
                f"- Timeouts: **{kpi_dict['Timeouts']}**\n"
                f"- No Driver Found: **{kpi_dict['No Driver Found Cases']}**")

    if 'driver cancell' in q:
        return (f"Driver Cancellation Rate is **{kpi_dict['Driver Cancellation Rate (%)']}%** "
                f"({kpi_dict['Driver Cancellations']} cancellations out of {kpi_dict['Total Requests']} requests).")

    if 'distance' in q:
        return f"The current distance from rider filter is set to **{d_range[0]} – {d_range[1]} km**."

    return (f"I can answer questions about fulfilment rate, acceptance rate, cancellations, timeouts, "
            f"regional performance, driver stats, and more. Here's a quick summary:\n\n"
            f"- Total Requests: **{kpi_dict['Total Requests']}**\n"
            f"- Fulfilment Rate: **{kpi_dict['Fulfillment Rate (%)']}%**\n"
            f"- Acceptance Rate: **{kpi_dict['Acceptance Rate (%)']}%**\n\n"
            f"Try asking: *'Which region has the best fulfillment rate?'* or *'Give me a summary.'*")


st.write('## 🤖 AI Data Assistant')
st.markdown("""
Ask me anything about the filtered data — fulfilment rates, acceptance rates, driver performance,
regional breakdowns, trends, summaries, and more.
""")

# Build a concise data summary to inject as context
def build_data_summary(data, kpi_dict):
    region_kpis = build_kpi_table(data.copy(), 'Region')
    driver_kpis = build_kpi_table(data.copy(), 'DRIVER')
    corporate_kpis = build_kpi_table(data.copy(), 'Corporate')

    region_summary = region_kpis.to_dict(orient='records')
    top_drivers_fr = driver_kpis.sort_values('Fulfillment Rate (%)', ascending=False).head(10).to_dict(orient='records')
    bottom_drivers_fr = driver_kpis.sort_values('Fulfillment Rate (%)').head(10).to_dict(orient='records')
    corporate_summary = corporate_kpis.to_dict(orient='records')

    # Hour breakdown
    hour_cats = data.groupby(['Hour', 'Category']).size().reset_index(name='count')
    hour_pivot = hour_cats.pivot_table(index='Hour', columns='Category', values='count', fill_value=0)

    summary = {
        "overall_kpis": kpi_dict,
        "region_kpis": region_summary,
        "top_10_drivers_by_fulfillment": top_drivers_fr,
        "bottom_10_drivers_by_fulfillment": bottom_drivers_fr,
        "corporate_kpis": corporate_summary,
        "total_rows_in_filtered_data": len(data),
        "distance_filter_applied": f"{dist_range[0]} to {dist_range[1]} km",
        "hourly_category_counts": hour_pivot.reset_index().to_dict(orient='records'),
    }
    return json.dumps(summary, default=str)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask about the data (e.g. 'Which region has the highest fulfillment rate?')")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build context
    data_summary = build_data_summary(filtered_df.copy(), kpi_data)
    system_prompt = f"""You are a data analyst assistant embedded in a ride-hailing supply dashboard.
You have access to the following summarised data (JSON) derived from the currently filtered dataset.
Answer user questions accurately and concisely using ONLY this data. If a question can't be answered
from the data, say so clearly.

DATA SUMMARY:
{data_summary}

Key metric definitions:
- Fulfillment Rate = Trips / (Trips + Driver Cancellations + Rider Cancellations) × 100
- Acceptance Rate = Trips / (Trips + Driver Cancellations + Rider Cancellations + Timeouts) × 100
- Driver Cancellation Rate = Driver Cancellations / Total Requests × 100
- Rider Cancellation Rate = Rider Cancellations / Total Requests × 100
- Timeout Rate = Timeouts / Total Requests × 100

Always format rates to 2 decimal places. Be helpful, precise, and data-driven.
"""

    # Build messages for API
    messages = []
    # Include last 10 turns for context
    for h in st.session_state.chat_history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})

    # Call Anthropic API
    import urllib.request
    import urllib.error

    api_payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": messages
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(api_payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode('utf-8'))
        assistant_reply = response_data['content'][0]['text']
    except Exception as e:
        # Fallback: answer from the summary directly without API
        assistant_reply = _local_answer(user_input, kpi_data, filtered_df.copy(), dist_range)

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)