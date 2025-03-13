import string 
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import argparse
import pytz
from timezonefinder import TimezoneFinder

def get_cordinates(city_name, key):
    """
    Get the latitude, longitude, and timezone for a city.
    """
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            latitude = data[0]["lat"]
            longitude = data[0]["lon"]
            
            # Get timezone using latitude and longitude
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
            
            if not timezone_str:
                timezone_str = "UTC"  # Fallback to UTC
            
            return latitude, longitude, pytz.timezone(timezone_str)
    print(f"Error: {response.status_code} - {response.text}")
    return None, None, pytz.utc

def get_latest_data(city_name, key):
    """
    This function takes the city name as input and returns the latest air pollution data of the city.
    """
    latitude, longitude, timezone_str = get_cordinates(city_name, key)
    
    if latitude is None or longitude is None:
        return "Error: Could not retrieve location data."
    
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={key}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        pollution_data = data["list"][0]  # Get the first (and usually only) entry
        components = pollution_data["components"]
        
        # Convert UTC timestamp to local timezone
        utc_time = datetime.fromtimestamp(pollution_data["dt"], timezone.utc)
        local_time = utc_time.astimezone(timezone_str)
        readable_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
    
        df = pd.DataFrame([{
            "Timestamp": readable_time,
            "AQI": pollution_data["main"]["aqi"],
            "CO": components["co"],
            "NO": components["no"],
            "NO2": components["no2"],
            "O3": components["o3"],
            "SO2": components["so2"],
            "PM2.5": components["pm2_5"],
            "PM10": components["pm10"],
            "NH3": components["nh3"]
        }])
        return df
    
    else:
        return f"Error {response.status_code}: {response.text}"

def get_history_data(city_name, start_date, end_date, key, mode="save"):
    """
    Fetch historical air pollution data for a given city and adjust timestamps to the local timezone.
    """
    latitude, longitude, timezone_str = get_cordinates(city_name, key)

    if latitude is None or longitude is None:
        return "Error: Could not retrieve location data."

    if (start_date == end_date):
        return "Error: Start date and end date cannot be the same."
    
    if "T" in start_date and "T" in end_date:
        local_start_dt = timezone_str.localize(datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S"))
        local_end_dt = timezone_str.localize(datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S"))
    else:
        local_start_dt = timezone_str.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        local_end_dt = timezone_str.localize(datetime.strptime(end_date, "%Y-%m-%d")) + timedelta(hours=23, minutes=59, seconds=59)
    
    start_timestamp = int(local_start_dt.astimezone(timezone.utc).timestamp())
    end_timestamp = int(local_end_dt.astimezone(timezone.utc).timestamp())

    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={latitude}&lon={longitude}&start={start_timestamp}&end={end_timestamp}&appid={key}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        # Extract relevant data
        records = []
        for entry in data.get("list", []):
            components = entry["components"]

            # Convert UTC timestamp to local timezone
            utc_time = datetime.fromtimestamp(entry["dt"], timezone.utc)
            local_time = utc_time.astimezone(timezone_str)
            readable_time = local_time.strftime('%Y-%m-%d %H:%M:%S')

            records.append({
                "Timestamp": readable_time,
                "AQI": entry["main"]["aqi"],
                "CO": components["co"],
                "NO": components["no"],
                "NO2": components["no2"],
                "O3": components["o3"],
                "SO2": components["so2"],
                "PM2.5": components["pm2_5"],
                "PM10": components["pm10"],
                "NH3": components["nh3"]
            })

        df = pd.DataFrame(records)

        if mode == "save":
            filename = f"historical_air_pollution_{start_date}_to_{end_date}_{city_name}.csv"
            df.to_csv(filename, index=False)
            return f"Data saved to {filename}"
        else:
            return df
    else:
        return f"Error {response.status_code}: {response.text}"

if __name__ == '__main__':
    load_dotenv()
    api_key = os.getenv("API_KEY")
    parser = argparse.ArgumentParser(description="Fetch historical air pollution data.")
    parser.add_argument("city_name", type=str, help="City name")
    parser.add_argument("start_date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("end_date", type=str, help="End date in YYYY-MM-DD format") 
    parser.add_argument("mode", type=str, help="Enter 'save' to save as CSV, or 'display' to return data") 
    args = parser.parse_args()

    print(get_history_data(args.city_name, args.start_date, args.end_date, api_key, args.mode))
