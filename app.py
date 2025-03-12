from src.air_polution_data_get import get_history_data,get_latest_data
import string 
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import streamlit as st

API_KEY = st.text_input("Enter (openweathermap.org) API KEY :",None)
city_name  = st.text_input("Enter city name:",None)
start_date = None
end_date = None
if st.checkbox("History Data"):
    start_date = st.text_input("Start date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:",None)
    end_date = st.text_input("Enter End date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format:",None)

if st.button("Get Data"):
    if(API_KEY and  city_name and start_date and end_date):
        data = get_history_data(city_name,start_date,end_date,API_KEY,"display")
        st.write(data)
    elif(API_KEY and  city_name):
        data = get_latest_data(city_name,API_KEY)
        st.write(data)
    else:
        st.write("Please enter all the required fields")