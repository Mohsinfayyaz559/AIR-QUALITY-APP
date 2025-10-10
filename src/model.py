import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from datetime import datetime, timedelta
import os
from sklearn.multioutput import MultiOutputRegressor
from dotenv import load_dotenv,find_dotenv
from src.air_polution_data_get import get_history_data, update_history_data,safe_upload
import joblib
import argparse
import pytz
import asyncio
from huggingface_hub import HfApi, upload_file,hf_hub_download

load_dotenv(find_dotenv())  
api_key = os.getenv("openweather_API_key")
hf_token = os.getenv("HF_TOKEN")

 
def feature_and_target_creation(df, lag_hours=30, forecast_horizon=12):
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


async def training():
    # Load data
    cities = ["islamabad","rawalpindi","lahore","larkana","multan","peshawar","quetta","karachi","faisalabad"]
    
    for city in cities:
        df = await update_history_data(city_name=city)
        # Feature creation
        df,feature_cols,target_cols = feature_and_target_creation(df, lag_hours=30, forecast_horizon=12)
    
        X_train = df[feature_cols]
        Y_train = df[target_cols]
        
        # Train MultiOutput XGBoost
        base_model = XGBRegressor(
            n_estimators=50, 
            learning_rate=0.1,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            verbosity=0
        )
        
        multi_model = MultiOutputRegressor(base_model)
        multi_model.fit(X_train, Y_train)
        for sub in ["air_quality_historic_data_csv", "models"]:
            os.makedirs(os.path.join("/tmp", sub), exist_ok=True)
        model_name = os.path.join("/tmp", "models", f"xgboost_model_{city}.pkl")
        joblib.dump(multi_model, model_name)
        print(f"Model for {city} trained successfully.")

        await safe_upload(
            model_name,
            repo_id="mk12rule/pakistan_air_quality_models",
            repo_type="model",
            token=hf_token
            )
            
        last_timestamp = df['Timestamp'].iloc[-1]
        # Save it to a file
        for sub in ["air_quality_historic_data_csv", "models","predictions"]:
            os.makedirs(os.path.join("/tmp", sub), exist_ok=True)
        time_stamp_file = os.path.join("/tmp", "models", f"{city}_last_trained_timestamp.txt")
        with open(time_stamp_file, "w") as f:
            f.write(str(last_timestamp))
            print(f"Model for {city} saved as {model_name}")
            print("model trained till",last_timestamp)

    print("All models trained successfully.")

async def predict( city_name = 'rawalpindi'):

    for sub in ["air_quality_historic_data_csv", "models","predictions"]:
            os.makedirs(os.path.join("/tmp", sub), exist_ok=True)

    city_name = city_name.lower()
    last_origin_path = os.path.join("/tmp", "predictions", f"{city_name}_last_origin_point.txt")
    pridictions_file = os.path.join("/tmp", "predictions", f"predictions_{city_name}.csv")
    # Paths for model and data files
    try:
        model_path = hf_hub_download(
        repo_id="mk12rule/pakistan_air_quality_models",
        filename=f"xgboost_model_{city_name}.pkl",
        )
    except Exception as e:
        file_path = os.path.join("/tmp", "models", f"xgboost_model_{city_name}.pkl")
        print(f"Error: {e}")
        if os.path.exists(file_path):
            model_path = file_path
            print(f"Using local model at {model_path}")
        else:
            model_path = f"backup/models/xgboost_model_{city_name}.pkl"
            print(f"Using backup model at {model_path}")

    # Load the origin i-e current timestamp
    tz = pytz.timezone("Asia/Karachi")
    origin_point = datetime.now(tz)
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
        df = await get_history_data(start_date=starting_point_str, end_date=origin_point_str, city_name= city_name, mode="Data" )
        if not isinstance(df, pd.DataFrame):
            return df, None  # Return the error message and None
        df = df.sort_values("Timestamp").reset_index(drop=True)
        # creating the features
        df,feature_cols,target_cols = feature_and_target_creation(df, lag_hours=30, forecast_horizon=0)
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
    
        #saving pred data frame
        for sub in ["air_quality_historic_data_csv", "models"]:
            os.makedirs(os.path.join("/tmp", sub), exist_ok=True)
        pred_df.to_csv(pridictions_file, index=False)
        # Save the origin point
        with open(last_origin_path, "w") as f:
            f.write(origin_point.isoformat())
        return pred_df, origin_point
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="give arg action the following values: train or predict")
    parser.add_argument("action", type=str, help="train or predict")
    parser.add_argument("--city", type=str, help="Optional city name for prediction")
    args = parser.parse_args()
    if args.action == "train":
        asyncio.run(training())
    if args.action == "predict":
        predictions = asyncio.run(predict(city_name = args.city if args.city else 'Rawalpindi'))
        print(predictions)