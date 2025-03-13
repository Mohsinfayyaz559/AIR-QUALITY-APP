from src.air_polution_data_get import get_history_data, get_latest_data
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

# Create two columns layout
input_col, output_col = st.columns([0.3, 0.7])

# Store data persistently
if "data" not in st.session_state:
    st.session_state.data = None

with input_col:
    st.write("Input Parameters")
    API_KEY = st.text_input("Enter (openweathermap.org) API KEY:", type="password")
    city_name = st.text_input("Enter city name:")
    start_date, end_date = None, None
    if st.checkbox("History Data"):
        start_date = st.text_input("Start date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:")
        end_date = st.text_input("Enter End date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:")
    
    # Fetch data only when button is pressed
    if st.button("Get Data"):
        if API_KEY and city_name:
            if start_date and end_date:
                st.session_state.data = get_history_data(city_name, start_date, end_date, API_KEY, "display")
            else:
                st.session_state.data = get_latest_data(city_name, API_KEY)

# Add option to switch between table and graph
view_option = st.radio("Select View:", ("Table", "Graph"))

with output_col:
    if st.session_state.data is not None and not isinstance(st.session_state.data, str):
        # Convert Timestamp to datetime format
        st.session_state.data["Timestamp"] = pd.to_datetime(st.session_state.data["Timestamp"])
        
        if view_option == "Table":
            st.write("Air Quality Table")
            st.write(st.session_state.data)
        else:
            st.write("Air Quality Graph")
            
            # Dropdown for selecting which graph to display
            parameter = st.selectbox("Select a parameter to plot:", ["PM2.5", "PM10", "NO2", "CO", "O3", "SO2", "AQI", "NH3"], key="param_select")
            
            # Plot selected parameter
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(st.session_state.data["Timestamp"], st.session_state.data[parameter], label=parameter, marker="o", linestyle="-")
            
            # Format x-axis to show both date and hour with vertical labels
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.tick_params(axis='x', labelsize=8, rotation=90)
            
            ax.set_xlabel("Date & Time")
            ax.set_ylabel(f"{parameter} Level")
            ax.set_title(f"{parameter} Over Time")
            ax.legend()
            ax.grid()
            
            # Show plot in Streamlit
            st.pyplot(fig)
