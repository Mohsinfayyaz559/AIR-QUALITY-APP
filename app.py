#to run file use command: streamlit run app.py

from src.air_polution_data_get import get_history_data, get_latest_data,get_cordinates
import streamlit as st
import plotly.express as px
import datetime
import os
import sys
import requests
import pandas as pd

st.set_page_config(
    page_title="Air QualityApp",
    layout="wide",  # <- This sets wide mode
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize session state variables
if "data" not in st.session_state:
    st.session_state.data = None
if "predictions" not in st.session_state:
    st.session_state.predictions = None
if "key_validation" not in st.session_state:
    st.session_state.key_validation = None

# Set page configuration
st.title(":blue[Air Quality Prediction App]")
st.subheader("This app fetches air quality data and predicts future values based on historical data.",divider=True)
API_KEY = st.text_input("Enter (openweathermap.org) API KEY:", type="password")
#checking api key
latitude, longitude, timezone_str,error = get_cordinates("rawalpindi", API_KEY)

check_api_key = st.button("Check API Key")
if st.session_state.key_validation is None:
    st.session_state.key_validation = False
    if check_api_key:
        if latitude is None or longitude is None or timezone_str is None:
            st.error(error)
            st.session_state.key_validation = False
        else:
            st.session_state.key_validation = True
            st.success("API Key is valid!")

else:
    if latitude is None or longitude is None or timezone_str is None:
        st.error(error)
        st.session_state.key_validation = False
    else:
        st.session_state.key_validation = True
        st.success("API Key is valid!")
        

data_tab,prediction_tab = st.tabs(["Data", "Prediction"])

if st.session_state.key_validation is True:
    
    with data_tab:
        input_col,output_col = st.columns([0.2,0.8])
        with input_col:
            st.write("Input Parameters")
            city_name = st.text_input("Enter city name:")
            start_date, end_date = None, None


            if st.checkbox("History Data"):
                today = datetime.date.today()
                date_range = st.date_input(
                    "Select date range",
                    [today - datetime.timedelta(days=7), today],
                    min_value=datetime.date(2022,1,1),
                    max_value=today
                )
                if len(date_range) == 2 : 
                    start_date, end_date = date_range
                    start_date = start_date.strftime("%Y-%m-%d")
                    end_date = end_date.strftime("%Y-%m-%d")
                else:
                    start_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    print("Using default date range:", start_date, "to", end_date)


            if st.button("Get Data"):
            
                if API_KEY and city_name:
                    with st.spinner("Fetching data..."):
                        try:
                            if start_date and end_date:
                                fresh_data = get_history_data(city_name, start_date, end_date, API_KEY, "display")
                            else:
                                fresh_data = get_latest_data(city_name, API_KEY)

                            if isinstance(fresh_data,str):
                                st.error(fresh_data)
                            elif isinstance(fresh_data, pd.DataFrame):
                                st.session_state.data = fresh_data
                                st.success("Data updated successfully!")
                            else:
                                st.error("Unexpected data type returned.")

                        except Exception as e:
                            st.error(f"Error fetching data: {str(e)}")
                else:
                    st.error("Please enter city name to fetch data.")
            # Add option to switch between table and graph
            view_option_data = st.radio("Select View:", ("Table", "Graph"),key="data_get")

        # Main content area

        with output_col:
            if st.session_state.data is not None and not isinstance(st.session_state.data, str):

                if view_option_data == "Table":
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


    with prediction_tab:
            city = st.selectbox("Select city", ["islamabad", "rawalpindi","lahore","larkana","multan","peshawar","quetta","karachi","faisalabad"], key="city_select")

            if st.button("Predict"):    
                with st.spinner("Predicting future values..."):
                    try:
                        url = f"http://127.0.0.1:8000/prediction?openweathermap_api_key={API_KEY}&city_name={city}"
                        response = requests.get(url)
                        predictions = response.json()
                        predictions = pd.DataFrame(predictions)
                        st.session_state.predictions = predictions
                    except Exception as e:
                        st.error(f"Error during prediction: {str(e)}")

            view_option_predict = st.radio("Select View:", ("Table", "Graph"),key="predict")

            if st.session_state.predictions is not None and not isinstance(st.session_state.predictions, str):
                if view_option_predict == "Table":
                    st.write("Predicted Values:")
                    st.write(st.session_state.predictions)
                else:
                    st.write("Predicted Values Graph")
                    fig = px.line(
                        st.session_state.predictions, 
                        x="Timestamp", 
                        y="AQI",
                        title=f"Predicted AQI Over Time",
                        labels={"Timestamp": "Date & Time",  "AQI": "AQI Level"},
                        markers=True
                    )
                    # Customize the layout
                    fig.update_layout(
                        xaxis_title="Date & Time",
                        yaxis_title="AQI Level",
                        legend_title="prediction",
                        hovermode="x unified"
                    )
                    # Display the plot using Streamlit
                    st.plotly_chart(fig, use_container_width=True)