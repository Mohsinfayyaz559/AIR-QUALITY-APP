import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta, date
import os
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from dotenv import load_dotenv
from air_polution_data_get import get_history_data, get_latest_data,get_all_history_data
import joblib
import argparse

load_dotenv()
api_key = os.getenv("API_KEY")
os.makedirs("utils/xgboost_data", exist_ok=True)
os.makedirs("utils/xgboost_data/models", exist_ok=True)


 
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

class training:
    def __init__(self):
        pass

    def full_training(self):
        # Load data
        df = get_all_history_data(key = api_key, city_name='Rawalpindi')
    
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

        joblib.dump(multi_model, "utils/xgboost_data/models/xgboost_model.pkl")
       
        last_timestamp = df['Timestamp'].iloc[-1]
        # Save it to a file
        with open("utils/xgboost_data/last_trained_timestamp.txt", "w") as f:
            f.write(str(last_timestamp))

        return multi_model


    def  Warm_Start_Training(self):
        # Load data
        with open("utils/xgboost_data/last_trained_timestamp.txt", "r") as f:
            last_trained_ts = pd.to_datetime(f.read().strip())
        
       
        if last_trained_ts.date() == date.today():
            print("Model is already trained till today.")
            return None
           
        else :
            end_date = (datetime.now()).strftime('%Y-%m-%dT%H:%M:%S')
            start_date = last_trained_ts.strftime('%Y-%m-%dT%H:%M:%S')

            df = get_history_data(key = api_key,start_date = start_date, end_date = end_date,city_name='rawalpindi', mode="Data" )

            # Feature creation
            df,feature_cols,target_cols = feature_and_target_creation(df, lag_hours=30, forecast_horizon=12)

            X_train = df[:][feature_cols]
            Y_train = df[:][target_cols]

            # Load the existing model
            multi_model = joblib.load("utils/xgboost_data/models/xgboost_model.pkl")

            # Fit the model on the new data
            multi_model.fit(X_train, Y_train, xgb_model= multi_model)

            joblib.dump(multi_model, "utils/xgboost_data/models/xgboost_model.pkl")

            last_timestamp = df['Timestamp'].iloc[-1]
            # Save it to a file
            with open("utils/xgboost_data/last_trained_timestamp.txt", "w") as f:
                f.write(str(last_timestamp))

            return multi_model

def predict():
    model = joblib.load("utils/xgboost_data/models/xgboost_model.pkl")
    
    origin_point = datetime.now()
    starting_point = origin_point - timedelta(days=4)
    origin_point_str = origin_point.strftime('%Y-%m-%dT%H:%M:%S')
    print("origin_point_str",origin_point_str)
    starting_point_str = starting_point.strftime('%Y-%m-%dT%H:%M:%S')

    df = get_history_data(key= api_key,start_date=starting_point_str, end_date=origin_point_str, city_name='rawalpindi', mode="Data" )
    df = df.sort_values("Timestamp").reset_index(drop=True)
    df,feature_cols,target_cols = feature_and_target_creation(df, lag_hours=30, forecast_horizon=0)
    
    X_input = df[feature_cols].iloc[-1:]
    Y_pred = model.predict(X_input)
    Y_pred = np.rint(Y_pred).astype(int).flatten()
    

    origin_time = pd.to_datetime(df['Timestamp'].iloc[-1])
    forecast_hours = pd.date_range(start=origin_time + pd.Timedelta(hours=1), periods=12, freq='h')

    pred_df = pd.DataFrame({
        "Timestamp": forecast_hours,
        "AQI": Y_pred
    })

     # Combine last N historical values with forecast
    recent_actuals = df[['Timestamp', 'AQI']].copy()
    combined_df = pd.concat([recent_actuals, pred_df], ignore_index=True)
    combined_df.to_csv("utils/xgboost_data/predictions.csv", index=False)
    return combined_df
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="give arg action the following values: full_train, warm_train or predict")
    parser.add_argument("action", type=str, help="full_train, warm_train or predict") 
    args = parser.parse_args()
    if(args.action == "full_train"):
        model = training()
        model.full_training()
    if(args.action == "warm_train"):
        model = training()
        model.Warm_Start_Training()
    if(args.action == "predict"):
        model = predict()
        print(model)