from src.air_polution_data_get import get_history_data
import string 
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import streamlit as st



API_KEY = st.text_input("Enter API_KEY:",None)
city_name  = st.text_input("Enter city name:",None)
start_date = st.text_input("Enter Start date in YYYY-MM-DD format:",None)
end_date = st.text_input("Enter End date in YYYY-MM-DD format:",None)

if st.button("Fetch Data"):
    if(API_KEY and  city_name and start_date and end_date):
        data = get_history_data(city_name,start_date,end_date,API_KEY)
        st.write(data)