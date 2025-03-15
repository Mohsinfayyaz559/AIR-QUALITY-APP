from src.air_polution_data_get import get_history_data, get_latest_data
import streamlit as st
import plotly.express as px

sidebar = st.sidebar

# Initialize session state variables
if "data" not in st.session_state:
    st.session_state.data = None


with sidebar:
    st.write("Input Parameters")

    API_KEY = st.text_input("Enter (openweathermap.org) API KEY:", type="password")
    city_name = st.text_input("Enter city name:")
    start_date, end_date = None, None
    if st.checkbox("History Data"):
        start_date = st.text_input("Start date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:")
        end_date = st.text_input("Enter End date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:")
    
    if st.button("Get Data"):
        
        if API_KEY and city_name:
            with st.spinner("Fetching data..."):
                try:
                    # Always make a fresh API call
                    if start_date and end_date:
                        fresh_data = get_history_data(city_name, start_date, end_date, API_KEY, "display")
                    else:
                        fresh_data = get_latest_data(city_name, API_KEY)
                    
                    # Update session state with fresh data
                    st.session_state.data = fresh_data
                    st.success("Data updated successfully!")
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")

    # Add option to switch between table and graph
    view_option = st.radio("Select View:", ("Table", "Graph"))

# Main content area
if st.session_state.data is not None and not isinstance(st.session_state.data, str):
    
    if view_option == "Table":
        st.write("Air Quality Table")
        st.write(st.session_state.data)
    else:
        st.write("Air Quality Graph")
        
        # Dropdown for selecting which graph to display
        parameter = st.selectbox("Select a parameter to plot:", ["PM2.5", "PM10", "NO2", "CO", "O3", "SO2", "AQI", "NH3"], key="param_select")

        fig = px.line(
            st.session_state.data, 
            x="Timestamp", 
            y=parameter,
            title=f"{parameter} Over Time",
            labels={"Timestamp": "Date & Time", parameter: f"{parameter} Level"},
            markers=True
        )
        
        # Customize the layout
        fig.update_layout(
            xaxis_title="Date & Time",
            yaxis_title=f"{parameter} Level",
            legend_title="Parameter",
            hovermode="x unified"
        )
        
        # Display the plot using Streamlit
        st.plotly_chart(fig, use_container_width=True)