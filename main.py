import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

# Loading data
@st.cache_data
def load_data():
    df = pd.read_excel(r'C:\streamlitDashboard\requests.xlsx')
    return df

# Set page configuration to wide
st.set_page_config(page_title="Supply Dashboard", page_icon="🚕", layout="wide")

# Loading data
df = load_data()

# Adding Filters
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

# Converting selected dates to Pandas datetime objects
selected_date_from = pd.Timestamp(selected_date_from)
selected_date_to = pd.Timestamp(selected_date_to)

# Applying Filters
filtered_df = df[
    ((df['CITY'].isin(selected_cities)) | ('All' in selected_cities)) &
    ((df['VEHICLETYPE'].astype(str).isin(selected_vehicle_types)) | ('All' in selected_vehicle_types)) &
    ((df['Date'] >= selected_date_from) & (df['Date'] <= selected_date_to)) &
    ((df['DRIVER'] == selected_driver) | (selected_driver == 'All')) &
    ((df['TRIPTYPE'] == selected_trip_type) | (selected_trip_type == 'All')) &
    ((df['Rider Mobile Number'].astype(str) == selected_rider) | (selected_rider == 'All')) &
    ((df['COUNTRY'] == selected_country) | (selected_country == 'All')) &
    ((df['Region'] == selected_region) | (selected_region == 'All')) &
    ((df['Corporate'] == selected_corporate) | (selected_corporate == 'All'))
]    

# Dropping rows with NaN values in Latitude and Longitude columns
filtered_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

# Calculating KPIs for filtered data
total_requests = len(filtered_df)
total_trips = filtered_df[filtered_df['Category'] == 'Trips'].shape[0]
driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation'].shape[0]
rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation'].shape[0]
no_driver_found = filtered_df[filtered_df['Category'] == 'No Drivers Found'].shape[0]
timeouts = filtered_df[filtered_df['Category'] == 'Timeout'].shape[0]

# Checking if total_trips is zero to avoid division by zero
if total_trips == 0:
    fulfillment_rate = 0
    acceptance_rate = 0
    driver_canc_rate = 0
else:
    fulfillment_rate = round((total_trips * 100) / (total_trips + driver_cancellations + rider_cancellations), 2)
    acceptance_rate = round((total_trips * 100) / (total_trips + driver_cancellations + rider_cancellations + timeouts), 2)
    driver_canc_rate = round((driver_cancellations * 100) / (total_trips + driver_cancellations + rider_cancellations + timeouts), 2)

# Title of the dashboard
st.title('🚕 Supply Requests Dashboard')

# KPIs Section
st.write('## Supply KPIs')

# Define KPIs
kpi_data = {
    'Total Requests': total_requests,
    'Total Trips': total_trips,
    'Driver Cancellations': driver_cancellations,
    'Rider Cancellations': rider_cancellations,
    'Timeouts': timeouts,
    'No Driver Found Cases': no_driver_found,
    'Fulfillment Rate (%)': fulfillment_rate,
    'Acceptance Rate (%)': acceptance_rate,
    'Driver Cancellation Rate (%)': driver_canc_rate
}

# CSS styles for the box
box_style = """
    background-color: #00008B;
    color: white;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 10px;
    font-size: 18px;
    font-style: italic;
"""

# Arrange KPIs in a 3x3 grid
col1, col2, col3 = st.columns(3)

# Display KPIs in each column with styled boxes
with col1:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Total Requests', 'Total Trips', 'Driver Cancellations']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)

with col2:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Rider Cancellations', 'Timeouts', 'No Driver Found Cases']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)

with col3:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Fulfillment Rate (%)', 'Acceptance Rate (%)', 'Driver Cancellation Rate (%)']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)


# Display filtered data
st.write('## 📑 Filtered Raw Data')

# Display the DataFrame without styling
st.write(filtered_df)

# Data Visualization
st.write('## 📊 Data Visualization')

# Aggregate data by vehicle type and date
request_count_by_date = filtered_df.groupby(['VEHICLETYPE', 'Date']).size().reset_index(name='count')

# Create a line chart using Altair with smooth lines
chart1 = alt.Chart(request_count_by_date).mark_line(interpolate='basis').encode(
    x=alt.X('Date:T', axis=alt.Axis(format='%Y-%m-%d'), title='Date'),
    y=alt.Y('count:Q', axis=alt.Axis(title='Request Count')),
    color='VEHICLETYPE:N',
    tooltip=['Date', 'count']
).properties(
    width=1500,
    height=400,
    title='Request Count by Vehicle Type Over Time'
).interactive()

# Render the chart
st.altair_chart(chart1)

# Aggregate data by Category and Hour
request_count_by_hour = filtered_df.groupby(['Category', 'Hour']).size().reset_index(name='count')

# Create a line chart using Altair with smooth lines
chart2 = alt.Chart(request_count_by_hour).mark_line(interpolate='basis').encode(
    x=alt.X('Hour:O', title='Hour'),
    y=alt.Y('count:Q', axis=alt.Axis(title='Request Count')),
    color='Category:N',
    tooltip=['Hour', 'count']
).properties(
    width=1500,
    height=400,
    title='Request Count by Category Over Hour'
).interactive()

# Render the chart
st.altair_chart(chart2)

# Display map chart of requests
st.write('## 🌍 Map of Requests')

# Filter out rows with missing latitude or longitude values
filtered_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

# Rename columns to match expected names for latitude and longitude
filtered_df = filtered_df.rename(columns={'Latitude': 'LAT', 'Longitude': 'LON'})

# Define the map layer with Google Maps as the basemap
layer = pdk.Layer(
    'ScatterplotLayer',
    data=filtered_df,
    get_position='[LON, LAT]',
    get_radius=20,  # Set radius of the points
    get_fill_color='[200, 30, 0, 160]',  # Color of the points
    pickable=True,
)

# Set the initial view state (latitude, longitude, zoom level)
view_state = pdk.ViewState(
    latitude=filtered_df['LAT'].mean(),
    longitude=filtered_df['LON'].mean(),
    zoom=10,  # You can adjust this value for the desired zoom level
    pitch=50,  # Adjust the pitch for 3D view
)

# Create the deck.gl map
r = pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',  # Google Maps style
    layers=[layer],
    initial_view_state=view_state,
)

# Render the map in Streamlit
st.pydeck_chart(r)

# Display filtered data
st.write('## 📈 Driver Data Table')

# Filter out 'No Drivers Found' from the total requests
filtered_df = filtered_df[filtered_df['Category'] != 'No Drivers Found']

# Calculate total requests per driver
driver_requests = filtered_df.groupby('DRIVER').size().reset_index(name='Total Requests')

# Filter out 'Trips' from the filtered DataFrame
filtered_df_trips = filtered_df[filtered_df['Category'] == 'Trips']

# Group data by driver and calculate total trips
driver_trips = filtered_df_trips.groupby('DRIVER').size().reset_index(name='Total Trips')

# Merge total requests and total trips tables on DRIVER column
driver_kpis = pd.merge(driver_requests, driver_trips, on='DRIVER', how='left')

# Filter out 'Driver Cancellation' from the filtered DataFrame
filtered_df_driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation']

# Group data by driver and calculate total driver cancellations
driver_cancellations = filtered_df_driver_cancellations.groupby('DRIVER').size().reset_index(name='Driver Cancellation')

# Merge total requests, total trips, and total driver cancellations tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, driver_cancellations, on='DRIVER', how='left')

# Filter out 'Rider Cancellation' from the filtered DataFrame
filtered_df_rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation']

# Group data by driver and calculate total rider cancellations
rider_cancellations = filtered_df_rider_cancellations.groupby('DRIVER').size().reset_index(name='Rider Cancellation')

# Merge total requests, total trips, and total rider cancellations tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, rider_cancellations, on='DRIVER', how='left')

# Filter out 'Timeouts' from the filtered DataFrame
filtered_df_timeouts = filtered_df[filtered_df['Category'] == 'Timeout']

# Group data by driver and calculate total timeouts
timeouts = filtered_df_timeouts.groupby('DRIVER').size().reset_index(name='Timeout')

# Merge total requests, total trips, and total timeouts tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, timeouts, on='DRIVER', how='left')

# Fill NaN values with 0
driver_kpis.fillna(0, inplace=True)

# Calculate Fulfillment Rate
driver_kpis['Fulfillment Rate (%)'] = (driver_kpis['Total Trips'] / (driver_kpis['Total Trips'] + driver_kpis['Driver Cancellation'] + driver_kpis['Rider Cancellation'])) * 100

# Calculate Acceptance Rate
driver_kpis['Acceptance Rate (%)'] = (driver_kpis['Total Trips'] / (driver_kpis['Total Trips'] + driver_kpis['Driver Cancellation'] + driver_kpis['Rider Cancellation']+ driver_kpis['Timeout'])) * 100

# Calculate Driver Cancellation Rate
driver_kpis['Driver Cancellation Rate (%)'] = (driver_kpis['Driver Cancellation'] / (driver_kpis['Total Requests'])) * 100

# Calculate Rider Cancellation Rate
driver_kpis['Rider Cancellation (%)'] = (driver_kpis['Rider Cancellation'] / (driver_kpis['Total Requests'])) * 100

# Calculate Timeout Rate
driver_kpis['Timeout Rate (%)'] = (driver_kpis['Timeout'] / (driver_kpis['Total Requests'])) * 100

# Displaying the table
st.write(driver_kpis)

# Display filtered data
st.write('## 📈 Clients Data Table')

# Filter out 'No Drivers Found' from the total requests
filtered_df = filtered_df[filtered_df['Category'] != 'No Drivers Found']

# Calculate total requests per driver
rider_requests = filtered_df.groupby('Rider Mobile Number').size().reset_index(name='Total Requests')

# Filter out 'Trips' from the filtered DataFrame
filtered_df_trips = filtered_df[filtered_df['Category'] == 'Trips']

# Group data by RIDER and calculate total trips
rider_trips = filtered_df_trips.groupby('Rider Mobile Number').size().reset_index(name='Total Trips')

# Merge total requests and total trips tables on DRIVER column
rider_kpis = pd.merge(rider_requests, rider_trips, on='Rider Mobile Number', how='left')

# Filter out 'Driver Cancellation' from the filtered DataFrame
filtered_df_driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation']

# Group data by RIDER and calculate total driver cancellations
driver_cancellations = filtered_df_driver_cancellations.groupby('Rider Mobile Number').size().reset_index(name='Driver Cancellation')

# Merge total requests, total trips, and total driver cancellations tables on DRIVER column
rider_kpis = pd.merge(rider_kpis, driver_cancellations, on='Rider Mobile Number', how='left')

# Filter out 'Rider Cancellation' from the filtered DataFrame
filtered_df_rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation']

# Group data by RIDER and calculate total rider cancellations
rider_cancellations = filtered_df_rider_cancellations.groupby('Rider Mobile Number').size().reset_index(name='Rider Cancellation')

# Merge total requests, total trips, and total rider cancellations tables on DRIVER column
rider_kpis = pd.merge(rider_kpis, rider_cancellations, on='Rider Mobile Number', how='left')

# Filter out 'Timeouts' from the filtered DataFrame
filtered_df_timeouts = filtered_df[filtered_df['Category'] == 'Timeout']

# Group data by driver and calculate total timeouts
timeouts = filtered_df_timeouts.groupby('Rider Mobile Number').size().reset_index(name='Timeout')

# Merge total requests, total trips, and total timeouts tables on DRIVER column
rider_kpis = pd.merge(rider_kpis, timeouts, on='Rider Mobile Number', how='left')

# Fill NaN values with 0
rider_kpis.fillna(0, inplace=True)

# Calculate Fulfillment Rate
rider_kpis['Fulfillment Rate (%)'] = (rider_kpis['Total Trips'] / (rider_kpis['Total Trips'] + rider_kpis['Driver Cancellation'] + rider_kpis['Rider Cancellation'])) * 100

# Calculate Acceptance Rate
rider_kpis['Acceptance Rate (%)'] = (rider_kpis['Total Trips'] / (rider_kpis['Total Trips'] + rider_kpis['Driver Cancellation'] + rider_kpis['Rider Cancellation']+ rider_kpis['Timeout'])) * 100

# Calculate Driver Cancellation Rate
rider_kpis['Driver Cancellation Rate (%)'] = (rider_kpis['Driver Cancellation'] / (rider_kpis['Total Requests'])) * 100

# Calculate Rider Cancellation Rate
rider_kpis['Rider Cancellation (%)'] = (rider_kpis['Rider Cancellation'] / (rider_kpis['Total Requests'])) * 100

# Calculate Timeout Rate
rider_kpis['Timeout Rate (%)'] = (rider_kpis['Timeout'] / (rider_kpis['Total Requests'])) * 100

# Displaying the table
st.write(rider_kpis)

# Displaying filtered data
st.write('## 📈 Regions Data Table')

# Filtering out 'No Drivers Found' from the total requests
filtered_df = filtered_df[filtered_df['Category'] != 'No Drivers Found']

# Calculating total requests per region
region_requests = filtered_df.groupby('Region').size().reset_index(name='Total Requests')

# Filtering out 'Trips' from the filtered DataFrame
filtered_df_trips = filtered_df[filtered_df['Category'] == 'Trips']

# Grouping data by region and calculate total trips
region_trips = filtered_df_trips.groupby('Region').size().reset_index(name='Total Trips')

# Merging total requests and total trips tables on Region column
region_kpis = pd.merge(region_requests, region_trips, on='Region', how='left')

# Filter out 'Driver Cancellation' from the filtered DataFrame
filtered_df_driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation']

# Grouping data by region and calculate total driver cancellations
driver_cancellations = filtered_df_driver_cancellations.groupby('Region').size().reset_index(name='Driver Cancellation')

# Merging total requests, total trips, and total driver cancellations tables on Region column
region_kpis = pd.merge(region_kpis, driver_cancellations, on='Region', how='left')

# Filtering out 'Rider Cancellation' from the filtered DataFrame
filtered_df_rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation']

# Grouping data by region and calculate total rider cancellations
rider_cancellations = filtered_df_rider_cancellations.groupby('Region').size().reset_index(name='Rider Cancellation')

# Merging total requests, total trips, and total rider cancellations tables on Region column
region_kpis = pd.merge(region_kpis, rider_cancellations, on='Region', how='left')

# Filtering out 'Timeouts' from the filtered DataFrame
filtered_df_timeouts = filtered_df[filtered_df['Category'] == 'Timeout']

# Grouping data by Region and calculate total timeouts
timeouts = filtered_df_timeouts.groupby('Region').size().reset_index(name='Timeout')

# Merging total requests, total trips, and total timeouts tables on DRIVER column
region_kpis = pd.merge(region_kpis, timeouts, on='Region', how='left')

# Fill NaN values with 0
region_kpis.fillna(0, inplace=True)

# Calculate Fulfillment Rate
region_kpis['Fulfillment Rate (%)'] = (region_kpis['Total Trips'] / (region_kpis['Total Trips'] + region_kpis['Driver Cancellation'] + region_kpis['Rider Cancellation'])) * 100

# Calculate Acceptance Rate
region_kpis['Acceptance Rate (%)'] = (region_kpis['Total Trips'] / (region_kpis['Total Trips'] + region_kpis['Driver Cancellation'] + region_kpis['Rider Cancellation']+ region_kpis['Timeout'])) * 100

# Calculate Driver Cancellation Rate
region_kpis['Driver Cancellation Rate (%)'] = (region_kpis['Driver Cancellation'] / (region_kpis['Total Requests'])) * 100

# Calculate Rider Cancellation Rate
region_kpis['Rider Cancellation (%)'] = (region_kpis['Rider Cancellation'] / (region_kpis['Total Requests'])) * 100

# Calculate Timeout Rate
region_kpis['Timeout Rate (%)'] = (region_kpis['Timeout'] / (region_kpis['Total Requests'])) * 100

# Displaying the table
st.write(region_kpis)

# Displaying filtered data
st.write('## 📈 Corporate Data Table')

# Filtering out 'No Drivers Found' from the total requests
filtered_df = filtered_df[filtered_df['Category'] != 'No Drivers Found']

# Calculating total requests per region
corporate_requests = filtered_df.groupby('Corporate').size().reset_index(name='Total Requests')

# Filtering out 'Trips' from the filtered DataFrame
filtered_df_trips = filtered_df[filtered_df['Category'] == 'Trips']

# Grouping data by corporate and calculate total trips
corporate_trips = filtered_df_trips.groupby('Corporate').size().reset_index(name='Total Trips')

# Merging total requests and total trips tables on Region column
corporate_kpis = pd.merge(corporate_requests, corporate_trips, on='Corporate', how='left')

# Filter out 'Driver Cancellation' from the filtered DataFrame
filtered_df_driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation']

# Grouping data by corporate and calculate total driver cancellations
driver_cancellations = filtered_df_driver_cancellations.groupby('Corporate').size().reset_index(name='Driver Cancellation')

# Merging total requests, total trips, and total driver cancellations tables on corporate column
corporate_kpis = pd.merge(corporate_kpis, driver_cancellations, on='Corporate', how='left')

# Filtering out 'Rider Cancellation' from the filtered DataFrame
filtered_df_rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation']

# Grouping data by corporate and calculate total rider cancellations
rider_cancellations = filtered_df_rider_cancellations.groupby('Corporate').size().reset_index(name='Rider Cancellation')

# Merging total requests, total trips, and total rider cancellations tables on corporate column
corporate_kpis = pd.merge(corporate_kpis, rider_cancellations, on='Corporate', how='left')

# Filtering out 'Timeouts' from the filtered DataFrame
filtered_df_timeouts = filtered_df[filtered_df['Category'] == 'Timeout']

# Grouping data by Region and calculate total timeouts
timeouts = filtered_df_timeouts.groupby('Corporate').size().reset_index(name='Timeout')

# Merging total requests, total trips, and total timeouts tables on DRIVER column
corporate_kpis = pd.merge(corporate_kpis, timeouts, on='Corporate', how='left')

# Fill NaN values with 0
corporate_kpis.fillna(0, inplace=True)

# Calculate Fulfillment Rate
corporate_kpis['Fulfillment Rate (%)'] = (corporate_kpis['Total Trips'] / (corporate_kpis['Total Trips'] + corporate_kpis['Driver Cancellation'] + corporate_kpis['Rider Cancellation'])) * 100

# Calculate Acceptance Rate
corporate_kpis['Acceptance Rate (%)'] = (corporate_kpis['Total Trips'] / (corporate_kpis['Total Trips'] + corporate_kpis['Driver Cancellation'] + corporate_kpis['Rider Cancellation']+ corporate_kpis['Timeout'])) * 100

# Calculate Driver Cancellation Rate
corporate_kpis['Driver Cancellation Rate (%)'] = (corporate_kpis['Driver Cancellation'] / (corporate_kpis['Total Requests'])) * 100

# Calculate Rider Cancellation Rate
corporate_kpis['Rider Cancellation (%)'] = (corporate_kpis['Rider Cancellation'] / (corporate_kpis['Total Requests'])) * 100

# Calculate Timeout Rate
corporate_kpis['Timeout Rate (%)'] = (corporate_kpis['Timeout'] / (corporate_kpis['Total Requests'])) * 100

# Displaying the table
st.write(corporate_kpis)
