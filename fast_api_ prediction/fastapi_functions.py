import os
import joblib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import pytz
from timezonefinder import TimezoneFinder



async def get_cordinates(city_name, key):
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

async def get_history_data(city_name, start_date, end_date, key, mode="save"):
    """
    Fetch historical air pollution data for a given city and adjust timestamps to the local timezone.
    """
    latitude, longitude, timezone_str = await get_cordinates(city_name, key)
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
            os.makedirs("utils/air_quality_historic_data_csv", exist_ok=True)
            filename = f"utils/air_quality_historic_data_csv/historical_air_pollution_{start_date}_to_{end_date}_{city_name}.csv"
            df.to_csv(filename, index=False)
            return f"Data saved to {filename}"
        else:
            return df
    else:
        return f"Error {response.status_code}: {response.text}"


async def feature_and_target_creation(df, lag_hours=30, forecast_horizon=12):
    # PREPROCESSING time 
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df["Timestamp"])
    # Set 'Date' as index
    df.set_index('Date', inplace=True)
    # sorting by date
    df = df.sort_values('Timestamp')

    # Create lag features
    lag_features = []
    for lag in range(1, lag_hours + 1):
        for col in ['AQI', 'PM2.5', 'PM10', 'CO', 'NO', 'NO2', 'O3', 'SO2', 'NH3']: 
            lag_col = df[col].shift(lag)
            lag_features.append(lag_col.rename(f'{col}_lag_{lag}'))

    df_lagged = pd.concat([df] + lag_features, axis=1)

    # Create forecast targets
    target_features = [df['AQI'].shift(-h).rename(f'AQI_t+{h}') for h in range(1, forecast_horizon + 1)]
    df = pd.concat([df_lagged] + target_features, axis=1)

    # Drop NaNs and reset index
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Define features and target variable
    feature_cols = [col for col in df.columns if 'lag' in col]
    target_cols = [col for col in df.columns if 'AQI_t+' in col]

    return df,feature_cols,target_cols


async def predict(API_key, city_name = 'rawalpindi'):
    
    city_name = city_name.lower()
    
    # Paths for model and data files
    last_origin_path = f"utils/xgboost_data/{city_name}_last_origin_point"
    model_path = f"models/xgboost_model_{city_name}.pkl"
    pridictions_file = f"utils/xgboost_data/predictions_{city_name}.csv"
    
    # Load the origin i-e current timestamp
    origin_point = datetime.now()
    origin_point = origin_point.replace(minute=0, second=0, microsecond=0)
    
    
    # Check if the last origin point file exists
    if os.path.exists(last_origin_path):
        # load the last origin point from the file
        with open(last_origin_path, "r") as f:
            last_origin = datetime.fromisoformat(f.read().strip())
            print(last_origin, origin_point)
            if last_origin == origin_point:
                # If the last origin is the same as the current, return the previous predictions
                df = pd.read_csv(pridictions_file)
                return df, origin_point
    
    
    #days defore current timestamp
    starting_point = origin_point - timedelta(days=4)
    #convert to string format
    origin_point_str = origin_point.strftime('%Y-%m-%dT%H:%M:%S')
    starting_point_str = starting_point.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Check if the model exists
    if(not os.path.exists(model_path)):
        return "model not trained yet or does not exist", origin_point
    else:
        # Load the model
        model = joblib.load(model_path)
        #getting the data from api
        df = await get_history_data(key= API_key,start_date=starting_point_str, end_date=origin_point_str, city_name='rawalpindi', mode="Data" )
        if not isinstance(df, pd.DataFrame):
            return df, None  # Return the error message and None
        df = df.sort_values("Timestamp").reset_index(drop=True)
        # creating the features
        df,feature_cols,target_cols = await feature_and_target_creation(df, lag_hours=30, forecast_horizon=0)
        # # Load the last row of the DataFrame
        X_input = df[feature_cols].iloc[-1:]
        #model prediction
        Y_pred = model.predict(X_input)
        #coverting prediction to int and from row to column
        Y_pred = np.rint(Y_pred).astype(int).flatten()
        #getting last timestamp from the original data
        origin_time = pd.to_datetime(df['Timestamp'].iloc[-1])
        #creating the forecast hours for prediction
        forecast_hours = pd.date_range(start= origin_time + pd.Timedelta(hours=1), periods=12, freq='h')
        #joining the forecast hours with the prediction
        pred_df = pd.DataFrame({
            "Timestamp": forecast_hours,
            "AQI": Y_pred
        })
    
         # Combine last N historical values with forecast
        recent_actuals = df[['Timestamp', 'AQI']].copy()
        combined_df = pd.concat([recent_actuals, pred_df], ignore_index=True)
        os.makedirs("utils/xgboost_data", exist_ok=True)
        combined_df.to_csv(pridictions_file, index=False)
        # Save the origin point
        with open(last_origin_path, "w") as f:
            f.write(origin_point.isoformat())
        return combined_df, origin_point

