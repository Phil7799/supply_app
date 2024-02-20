import streamlit as st
import pandas as pd
import altair as alt
import openpyxl 

# Set page configuration
st.set_page_config(
    page_title="Little Loan Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"  # Expand sidebar by default
)

# Load data from Excel
@st.cache
def load_data():
    df = pd.read_excel(r'C:\streamlitDashboard\Loans2024.xlsx')
    return df

df = load_data()

# Apply custom styling
st.markdown(
    """
    <style>
        body {
            background-color: #1E1B1A; /* Dark grey background */
            color: white; /* White text */
        }

        .sidebar .sidebar-content {
            background-color: #1E1B1A; /* Dark sidebar */
            color: white; /* White text in sidebar */
        }

        .kpi-card {
            background-color: #030C7A; /* Blue background for KPI cards */
            padding: 20px;
            margin: 10px;
            border-radius: 10px;
        }

        .kpi-title {
            font-size: 24px;
            font-weight: bold;
            color: #9DA0C2; /* white text for KPI titles */
            margin-bottom: 10px;
        }

        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: white; /* White text for KPI values */
        }

        .chart-container {
            margin-top: 20px;
        }

        .chart-title {
            font-size: 24px;
            font-weight: bold;
            color: #1E88E5;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Display the data
st.title('🚕Little Loan Dashboard')

# Add interactive elements to the sidebar
st.sidebar.title('Filters')

# Filter by Loan ID
loan_ids = df['LoanID'].unique()
selected_loan_id = st.sidebar.selectbox('Select Loan ID', ['All'] + list(loan_ids))

# Filter by Driver Email
driver_emails = df['Driver Email'].unique()
selected_driver_email = st.sidebar.selectbox('Select Driver Email', ['All'] + list(driver_emails))

# Filter by Date of Issue
date_issued_range = st.sidebar.date_input('Select Date Issued Range', [df['Date of issue'].min(), df['Date of issue'].max()])
date_issued_start, date_issued_end = date_issued_range

# Apply filters
filtered_df = df.copy()
if selected_loan_id != 'All':
    filtered_df = filtered_df[filtered_df['LoanID'] == selected_loan_id]
if selected_driver_email != 'All':
    filtered_df = filtered_df[filtered_df['Driver Email'] == selected_driver_email]
filtered_df = filtered_df[(filtered_df['Date of issue'] >= pd.Timestamp(date_issued_start)) & 
                           (filtered_df['Date of issue'] <= pd.Timestamp(date_issued_end))]

# Calculate KPIs based on filtered data
total_amount_issued = filtered_df['Amount Issued'].sum()
total_amount_expected = filtered_df['Amount Payable'].sum()
total_amount_paid = filtered_df['Amount Paid'].sum()
total_outstanding_amount = filtered_df['Outstanding Amount'].sum()

loans_due = filtered_df[filtered_df['Date due'] < pd.Timestamp.now()]
amount_paid_for_loans_due = loans_due['Amount Paid'].sum()
outstanding_amount_for_loans_due = loans_due['Outstanding Amount'].sum()

# Display KPIs in a scorecard format
st.write("## Key Performance Indicators (KPIs)")

# Define the HTML structure for the KPI scorecards
kpi_scorecard = """
<div style="display: flex; flex-wrap: wrap; justify-content: space-between;">

<div class="kpi-card" style="flex: 1; margin-right: 10px;">
        <div class="kpi-title">Total amount issued:</div>
        <div class="kpi-value">{}</div>
    </div>

 <div class="kpi-card" style="flex: 1; margin-right: 10px;">
        <div class="kpi-title">Total amount expected to be paid:</div>
        <div class="kpi-value">{}</div>
    </div>

<div class="kpi-card" style="flex: 1;">
        <div class="kpi-title">Total amount paid so far:</div>
        <div class="kpi-value">{}</div>
    </div>

</div>

<div style="margin-top: 20px; display: flex; flex-wrap: wrap; justify-content: space-between;">

<div class="kpi-card" style="flex: 1; margin-right: 10px;">
        <div class="kpi-title">Total outstanding amount:</div>
        <div class="kpi-value">{}</div>
    </div>

<div class="kpi-card" style="flex: 1; margin-right: 10px;">
        <div class="kpi-title">Loans that are due:</div>
        <div class="kpi-value">{}</div>
    </div>

<div class="kpi-card" style="flex: 1;">
        <div class="kpi-title">Amount paid for loans that are due:</div>
        <div class="kpi-value">{}</div>
    </div>

</div>

<div style="margin-top: 20px; display: flex; justify-content: left;">
    <div class="kpi-card" style="margin-right: 10px;">
        <div class="kpi-title">Outstanding amount for loans that due:</div>
        <div class="kpi-value">{}</div>
    </div>
</div>

"""

# Populate the HTML structure with KPI values
kpi_scorecard = kpi_scorecard.format(
    total_amount_issued,
    total_amount_expected,
    total_amount_paid,
    total_outstanding_amount,
    len(loans_due),
    amount_paid_for_loans_due,
    outstanding_amount_for_loans_due
)

# Display the KPI scorecard
st.markdown(kpi_scorecard, unsafe_allow_html=True)

# Display filtered data
st.write("## Filtered Data")
st.write(filtered_df)

# Line chart for sum of amounts issued by date
st.write("## Amount Issued Over Time")
chart_data = filtered_df.groupby(pd.Grouper(key='Date of issue', freq='D'))['Amount Issued'].sum().reset_index()
chart = alt.Chart(chart_data).mark_line(interpolate='basis').encode(
    x=alt.X('Date of issue:T', title='Date'),
    y=alt.Y('Amount Issued:Q', title='Amount Issued'),
    tooltip=['Date of issue', 'Amount Issued']
).properties(
    width=800,
    height=400
)

# Title for the line chart
st.markdown("<div class='chart-title'>Amount Issued Over Time</div>", unsafe_allow_html=True)

# Display the line chart
st.altair_chart(chart, use_container_width=True)