import streamlit as st
from main import ImmigrationSDK

st.set_page_config(page_title="Immigration Dashboard", layout="wide")

# UI Styling
st.title("⚖️ Immigration Portal | Case Management")

# Sidebar for the Three Views
st.sidebar.header("Navigation")
view = st.sidebar.radio("Select View", ["Cases", "Lawyers", "Clients"])

# Fetch Data (Simulated API Call)
data = ImmigrationSDK.fetch_cases()

if view == "Cases":
    st.subheader("Active Case Files")
    
    # The "High Risk" Filter we discussed
    high_risk_only = st.toggle("🚨 Show High Risk Only")
    
    if high_risk_only:
        filtered_data = [c for c in data if len(c['flags']) > 0]
    else:
        filtered_data = data
        
    # Display table with flags and readiness
    st.dataframe(
        filtered_data,
        column_order=("case_key", "visa_name", "completion_rate", "flags"),
        hide_index=True
    )

elif view == "Lawyers":
    st.subheader("Lawyer Performance")
    st.info("This view aggregates data for your 5 lawyers.") #

elif view == "Clients":
    st.subheader("Client Directory")
    st.info("Master list of clients and their JSON metadata.")