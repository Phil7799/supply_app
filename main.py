import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import os
import json
import hashlib
import re
from datetime import datetime

# Set page configuration to wide
st.set_page_config(
    page_title="Supply Dashboard",
    page_icon="https://res.cloudinary.com/dnq8ne9lx/image/upload/v1753860594/infograph_ewfmm6.ico",
    layout="wide"
)

# ─────────────────────────────────────────────
# AUTH CONFIG
# ─────────────────────────────────────────────
ADMIN_EMAIL = "admin@little.africa"          # ← change to your actual email
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        # Bootstrap: create users.json with only the admin account
        initial = {
            ADMIN_EMAIL: {
                "password": hash_password("admin123"),  # ← change admin password here
                "role": "admin",
                "active": True,
                "created_at": datetime.now().isoformat()
            }
        }
        save_users(initial)
        return initial
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[\w.\-+]+@little\.africa$', email.strip().lower()))

def authenticate(email: str, password: str) -> tuple:
    """Returns (success, message)."""
    users = load_users()
    email = email.strip().lower()
    if email not in users:
        return False, "Email not registered."
    user = users[email]
    if not user.get("active", True):
        return False, "Your access has been revoked. Please contact the admin."
    if user["password"] != hash_password(password):
        return False, "Incorrect password."
    return True, "ok"

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
    .login-wrapper {
        display: flex; justify-content: center; align-items: center;
        padding-top: 80px;
    }
    .login-box {
        background: #00008B; color: white;
        padding: 40px 48px; border-radius: 12px;
        text-align: center; max-width: 420px; width: 100%;
    }
    .login-box h2 { margin-bottom: 4px; font-size: 1.8rem; }
    .login-box p  { color: #c8c8ff; margin-bottom: 28px; font-size: 0.95rem; }
    </style>
    <div class="login-wrapper">
      <div class="login-box">
        <h2>🚕 Supply Dashboard</h2>
        <p>Sign in with your @little.africa account</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        email_input    = st.text_input("Email", placeholder="you@little.africa", key="login_email")
        password_input = st.text_input("Password", type="password", key="login_password")
        login_btn      = st.button("Sign In", use_container_width=True)

        if login_btn:
            if not email_input:
                st.error("Please enter your email.")
            elif not is_valid_email(email_input):
                st.error("Only @little.africa email addresses are allowed.")
            elif not password_input:
                st.error("Please enter your password.")
            else:
                ok, msg = authenticate(email_input, password_input)
                if ok:
                    users = load_users()
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"]  = email_input.strip().lower()
                    st.session_state["current_role"]  = users[email_input.strip().lower()]["role"]
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────
def show_admin_panel():
    st.write("## 🔐 Admin Panel – User Management")
    users = load_users()

    # ── Current users table ──
    st.write("### Registered Users")
    user_rows = []
    for email, info in users.items():
        user_rows.append({
            "Email": email,
            "Role": info.get("role", "user"),
            "Status": "✅ Active" if info.get("active", True) else "🚫 Revoked",
            "Created": info.get("created_at", "—")[:10],
        })
    st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    col_add, col_rev = st.columns(2)

    # ── Add new user ──
    with col_add:
        st.write("#### ➕ Add New User")
        new_email    = st.text_input("New user email (@little.africa)", key="new_email")
        new_password = st.text_input("Temporary password", type="password", key="new_pass")
        new_role     = st.selectbox("Role", ["user", "admin"], key="new_role")
        if st.button("Add User", key="add_user_btn"):
            new_email_clean = new_email.strip().lower()
            if not is_valid_email(new_email_clean):
                st.error("Email must be @little.africa format.")
            elif new_email_clean in users:
                st.warning("This email is already registered.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                users[new_email_clean] = {
                    "password": hash_password(new_password),
                    "role": new_role,
                    "active": True,
                    "created_at": datetime.now().isoformat()
                }
                save_users(users)
                st.success(f"✅ {new_email_clean} added successfully!")
                st.rerun()

    # ── Revoke / restore / delete ──
    with col_rev:
        st.write("#### 🔧 Manage Access")
        other_users = [e for e in users if e != st.session_state["current_user"]]
        if not other_users:
            st.info("No other users to manage.")
        else:
            target = st.selectbox("Select user", other_users, key="manage_target")
            target_info = users[target]
            is_active = target_info.get("active", True)

            c1, c2, c3 = st.columns(3)
            with c1:
                if is_active:
                    if st.button("🚫 Revoke Access", key="revoke_btn"):
                        users[target]["active"] = False
                        save_users(users)
                        st.success(f"Access revoked for {target}.")
                        st.rerun()
                else:
                    if st.button("✅ Restore Access", key="restore_btn"):
                        users[target]["active"] = True
                        save_users(users)
                        st.success(f"Access restored for {target}.")
                        st.rerun()
            with c2:
                new_pw = st.text_input("Reset password", type="password", key="reset_pw")
                if st.button("🔑 Reset Password", key="reset_btn"):
                    if len(new_pw) < 6:
                        st.error("Min 6 characters.")
                    else:
                        users[target]["password"] = hash_password(new_pw)
                        save_users(users)
                        st.success(f"Password reset for {target}.")
                        st.rerun()
            with c3:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete User", key="delete_btn"):
                    del users[target]
                    save_users(users)
                    st.success(f"{target} deleted.")
                    st.rerun()

    st.markdown("---")

# ─────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    show_login()
    st.stop()

# ─────────────────────────────────────────────
# LOGGED-IN HEADER (sidebar)
# ─────────────────────────────────────────────
current_user = st.session_state["current_user"]
current_role = st.session_state["current_role"]

with st.sidebar:
    st.markdown(f"""
    <div style='background:#00008B;color:white;padding:12px 16px;border-radius:8px;margin-bottom:12px;font-size:0.85rem;'>
        👤 <b>{current_user}</b><br>
        <span style='color:#c8c8ff;font-size:0.78rem;'>{current_role.capitalize()}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Sign Out"):
        for key in ["authenticated", "current_user", "current_role", "chat_history"]:
            st.session_state.pop(key, None)
        st.rerun()

# ─────────────────────────────────────────────
# ADMIN PANEL (only for admins)
# ─────────────────────────────────────────────
if current_role == "admin":
    with st.expander("🔐 Admin Panel – User Management", expanded=False):
        show_admin_panel()

# ─────────────────────────────────────────────
# Loading data
# ─────────────────────────────────────────────
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

# ── Distance from Rider range filter ──
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

# ── Hour range filter ──
st.sidebar.markdown("---")
st.sidebar.subheader("🕐 Hour Filter")
hour_min_val = int(df['Hour'].min())
hour_max_val = int(df['Hour'].max())
hour_range = st.sidebar.slider(
    'Hour of Day',
    min_value=hour_min_val,
    max_value=hour_max_val,
    value=(hour_min_val, hour_max_val),
    step=1
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
    ((df[dist_col] >= dist_range[0]) & (df[dist_col] <= dist_range[1])) &
    ((df['Hour'] >= hour_range[0]) & (df['Hour'] <= hour_range[1]))
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

# ── Line chart: Fulfillment Rate & Acceptance Rate by Hour ──
st.write('### 📈 Fulfillment Rate & Acceptance Rate by Hour')

def compute_rates_by_hour(data):
    trips = data[data['Category'] == 'Trips'].groupby('Hour').size().reset_index(name='Trips')
    dc = data[data['Category'] == 'Driver Cancellation'].groupby('Hour').size().reset_index(name='DC')
    rc = data[data['Category'] == 'Rider Cancellation'].groupby('Hour').size().reset_index(name='RC')
    to = data[data['Category'] == 'Timeout'].groupby('Hour').size().reset_index(name='Timeout')
    merged = trips.merge(dc, on='Hour', how='outer') \
                  .merge(rc, on='Hour', how='outer') \
                  .merge(to, on='Hour', how='outer').fillna(0)
    merged['Fulfillment Rate (%)'] = (
        merged['Trips'] / (merged['Trips'] + merged['DC'] + merged['RC']).clip(lower=1)
    ) * 100
    merged['Acceptance Rate (%)'] = (
        merged['Trips'] / (merged['Trips'] + merged['DC'] + merged['RC'] + merged['Timeout']).clip(lower=1)
    ) * 100
    return merged

rates_by_hour = compute_rates_by_hour(filtered_df)

if not rates_by_hour.empty:
    rates_melted = rates_by_hour[['Hour', 'Fulfillment Rate (%)', 'Acceptance Rate (%)']].melt(
        id_vars='Hour', var_name='Metric', value_name='Rate (%)'
    )
    chart_rates = alt.Chart(rates_melted).mark_line(point=True, interpolate='monotone').encode(
        x=alt.X('Hour:O', title='Hour of Day', sort=list(range(24))),
        y=alt.Y('Rate (%):Q', title='Rate (%)', scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('Metric:N', scale=alt.Scale(
            domain=['Fulfillment Rate (%)', 'Acceptance Rate (%)'],
            range=['#2ecc71', '#3498db']
        )),
        tooltip=['Hour', 'Metric', alt.Tooltip('Rate (%):Q', format='.2f')]
    ).properties(width=1500, height=400, title='Fulfillment Rate & Acceptance Rate by Hour of Day').interactive()
    st.altair_chart(chart_rates)
else:
    st.warning("Not enough data to compute hourly rates.")

# ─────────────────────────────────────────────
# HEAT MAPS
# ─────────────────────────────────────────────
st.write('## 🌡️ Hourly Heatmaps by Region')

st.write('### Fulfilment Rate Heatmap (Region × Hour)')

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
        y=alt.Y('Region:N', title='Region', sort=all_regions_fr, axis=alt.Axis(labelLimit=200)),
        color=alt.Color('Fulfillment Rate (%):Q', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100]),
                        legend=alt.Legend(title='Fulfilment Rate (%)')),
        tooltip=['Region', 'Hour', 'Fulfillment Rate (%)', 'Trips', 'DC', 'RC']
    ).properties(width=900, height=max(300, len(all_regions_fr) * 30), title='Hourly Fulfilment Rate by Region').interactive()
    st.altair_chart(heatmap_fr, use_container_width=True)
else:
    st.warning("Not enough data for the Fulfilment Rate heatmap with current filters.")

st.write('### Total Requests Heatmap (Region × Hour)')

req_by_region_hour = filtered_df.groupby(['Region', 'Hour']).size().reset_index(name='Total Requests')

if not req_by_region_hour.empty:
    all_regions_req = sorted(req_by_region_hour['Region'].unique().tolist(), key=str)
    heatmap_req = alt.Chart(req_by_region_hour).mark_rect().encode(
        x=alt.X('Hour:O', title='Hour of Day', sort=list(range(24))),
        y=alt.Y('Region:N', title='Region', sort=all_regions_req, axis=alt.Axis(labelLimit=200)),
        color=alt.Color('Total Requests:Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(title='Total Requests')),
        tooltip=['Region', 'Hour', 'Total Requests']
    ).properties(width=900, height=max(300, len(all_regions_req) * 30), title='Hourly Total Requests by Region').interactive()
    st.altair_chart(heatmap_req, use_container_width=True)
else:
    st.warning("Not enough data for the Total Requests heatmap with current filters.")

# ─────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────
st.write('## 🌍 Map of Requests')

if map_df.empty:
    st.warning("No data with valid coordinates to display on the map.")
else:
    map_df = map_df.rename(columns={'Latitude': 'LAT', 'Longitude': 'LON'})
    category_colors = {
        'Trips': [0, 200, 100, 180],
        'Driver Cancellation': [255, 100, 0, 180],
        'Rider Cancellation': [255, 200, 0, 180],
        'No Drivers Found': [150, 0, 200, 180],
        'Timeout': [200, 0, 0, 180],
    }
    map_df['color'] = map_df['Category'].map(lambda c: category_colors.get(c, [100, 100, 100, 160]))
    layer = pdk.Layer('ScatterplotLayer', data=map_df, get_position='[LON, LAT]',
                      get_radius=80, get_fill_color='color', pickable=True, auto_highlight=True)
    view_state = pdk.ViewState(latitude=map_df['LAT'].mean(), longitude=map_df['LON'].mean(), zoom=10, pitch=40)
    tooltip = {
        "html": "<b>Category:</b> {Category}<br/><b>Driver:</b> {DRIVER}<br/><b>City:</b> {CITY}<br/><b>Region:</b> {Region}<br/><b>Distance:</b> {DISTANCE FROM RIDER} km",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }
    r = pdk.Deck(map_style='mapbox://styles/mapbox/streets-v11', layers=[layer],
                 initial_view_state=view_state, tooltip=tooltip)
    st.pydeck_chart(r)
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
# CHATBOT
# ─────────────────────────────────────────────
def _local_answer(question, kpi_dict, data, d_range):
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
        return f"The overall **Fulfilment Rate** is **{kpi_dict['Fulfillment Rate (%)']}%**."
    if 'acceptance' in q:
        return f"The overall **Acceptance Rate** is **{kpi_dict['Acceptance Rate (%)']}%**."
    if 'summary' in q or 'overview' in q:
        return (f"**Dashboard Summary**\n\n"
                f"- Total Requests: **{kpi_dict['Total Requests']}**\n"
                f"- Total Trips: **{kpi_dict['Total Trips']}**\n"
                f"- Fulfilment Rate: **{kpi_dict['Fulfillment Rate (%)']}%**\n"
                f"- Acceptance Rate: **{kpi_dict['Acceptance Rate (%)']}%**\n"
                f"- Driver Cancellations: **{kpi_dict['Driver Cancellations']}**\n"
                f"- Rider Cancellations: **{kpi_dict['Rider Cancellations']}**\n"
                f"- Timeouts: **{kpi_dict['Timeouts']}**")
    if 'driver cancell' in q:
        return f"Driver Cancellation Rate is **{kpi_dict['Driver Cancellation Rate (%)']}%**."
    if 'distance' in q:
        return f"Distance filter: **{d_range[0]} – {d_range[1]} km**."
    return (f"- Total Requests: **{kpi_dict['Total Requests']}**\n"
            f"- Fulfilment Rate: **{kpi_dict['Fulfillment Rate (%)']}%**\n"
            f"- Acceptance Rate: **{kpi_dict['Acceptance Rate (%)']}%**")

st.write('## 🤖 Nexus Phil')
st.markdown("Ask me anything about the filtered data: fulfilment rates, acceptance rates, driver performance, regional breakdowns, and more.")

def build_data_summary(data, kpi_dict):
    region_kpis = build_kpi_table(data.copy(), 'Region')
    driver_kpis = build_kpi_table(data.copy(), 'DRIVER')
    corporate_kpis = build_kpi_table(data.copy(), 'Corporate')
    hour_cats = data.groupby(['Hour', 'Category']).size().reset_index(name='count')
    hour_pivot = hour_cats.pivot_table(index='Hour', columns='Category', values='count', fill_value=0)
    summary = {
        "overall_kpis": kpi_dict,
        "region_kpis": region_kpis.to_dict(orient='records'),
        "top_10_drivers_by_fulfillment": driver_kpis.sort_values('Fulfillment Rate (%)', ascending=False).head(10).to_dict(orient='records'),
        "bottom_10_drivers_by_fulfillment": driver_kpis.sort_values('Fulfillment Rate (%)').head(10).to_dict(orient='records'),
        "corporate_kpis": corporate_kpis.to_dict(orient='records'),
        "total_rows_in_filtered_data": len(data),
        "distance_filter_applied": f"{dist_range[0]} to {dist_range[1]} km",
        "hourly_category_counts": hour_pivot.reset_index().to_dict(orient='records'),
    }
    return json.dumps(summary, default=str)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about the data (e.g. 'Which region has the highest fulfillment rate?')")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    data_summary = build_data_summary(filtered_df.copy(), kpi_data)
    system_prompt = f"""You are a data analyst assistant embedded in a ride-hailing supply dashboard.
You have access to the following summarised data (JSON) derived from the currently filtered dataset.
Answer user questions accurately and concisely using ONLY this data.

DATA SUMMARY:
{data_summary}

Key metric definitions:
- Fulfillment Rate = Trips / (Trips + Driver Cancellations + Rider Cancellations) × 100
- Acceptance Rate = Trips / (Trips + Driver Cancellations + Rider Cancellations + Timeouts) × 100
- Driver Cancellation Rate = Driver Cancellations / Total Requests × 100
Always format rates to 2 decimal places. Be helpful, precise, and data-driven.
"""

    messages = []
    for h in st.session_state.chat_history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})

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
            headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode('utf-8'))
        assistant_reply = response_data['content'][0]['text']
    except Exception:
        assistant_reply = _local_answer(user_input, kpi_data, filtered_df.copy(), dist_range)

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)