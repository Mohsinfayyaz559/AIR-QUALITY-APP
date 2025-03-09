import string 
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone


def get_cordinates(city_name, key):
    """
    This function will take the city name as input and return the latitude and longitude of the city
    """
    # Get the city name and API key and return the latitude and longitude of the city
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={key}"
    response = requests.get(url)
    if (response.status_code == 200):
        data = response.json()
        response_json = response.json()
        if data:
            latitude = data[0]["lat"]
            longitude = data[0]["lon"]
        return latitude, longitude
    else:
        print(f"Error: {response.status_code} - {response.text}")





def get_latest_data(city_name, key):
    """
    This function will take the city name as input and return the historic air polution data of the city
    """
    # Get the city name and API key and return the historic air polution data of the city
    latitude, longitude = get_cordinates(city_name, key)
    
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={key}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extract the relevant data
        pollution_data = data["list"][0]  # Get the first (and usually only) entry
        components = pollution_data["components"]
        
        # Convert timestamp to readable datetime
        readable_time = datetime.fromtimestamp(pollution_data["dt"], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
        # Convert to DataFrame
        df = pd.DataFrame([{
            "CO": components["co"],
            "NO": components["no"],
            "NO2": components["no2"],
            "O3": components["o3"],
            "SO2": components["so2"],
            "PM2.5": components["pm2_5"],
            "PM10": components["pm10"],
            "NH3": components["nh3"],
            "AQI": pollution_data["main"]["aqi"],
            "Timestamp": readable_time
            }])
        return df

    else:
        print(f"Error {response.status_code}: {response.text}")


def get_history_data(city_name,start_date,end_date,key):
    """
    This function will take the city name as input and return the historic air polution data of the city
    """
    # Get the city name and API key and return the historic air polution data of the city
    latitude, longitude = get_cordinates(city_name, key)

    # Convert to UNIX timestamp
    start_date = f"{start_date} 00:00:00"
    end_date = f"{end_date} 23:59:59"
    start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
    end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={latitude}&lon={longitude}&start={start_timestamp}&end={end_timestamp}&appid={key}"

    # Make the API request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Extract relevant data
        records = []
        for entry in data.get("list", []):
            components = entry["components"]
            readable_time = datetime.fromtimestamp(entry["dt"], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            records.append({
                "CO": components["co"],
                "NO": components["no"],
                "NO2": components["no2"],
                "O3": components["o3"],
                "SO2": components["so2"],
                "PM2.5": components["pm2_5"],
                "PM10": components["pm10"],
                "NH3": components["nh3"],
                "AQI": entry["main"]["aqi"],
                "Timestamp": readable_time
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Save to CSV
        filename = f"historical_air_pollution_{start_date[:10]}_to_{end_date[:10]}_{city_name}.csv"
        df.to_csv(filename, index=False)
        
        print("Historical data saved successfully!")
    
    else:
        print(f"Error {response.status_code}: {response.text}")



get_history_data("rawalpindi", "2022-01-01", "2022-12-31", "c2d947c816991fb95a2c2895de5d10b3")


