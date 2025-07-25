import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from datetime import datetime, timedelta
import os
from sklearn.multioutput import MultiOutputRegressor
from dotenv import load_dotenv
from air_polution_data_get import get_history_data, update_history_data
import joblib
import argparse

load_dotenv()
api_key = os.getenv("API_KEY")


 
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


def training(city = 'Rawalpindi'):
    # Load data
    df = update_history_data(key = api_key, city_name=city)

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
    os.makedirs("utils/xgboost_data/models", exist_ok=True)
    model_name = f'utils/xgboost_data/models/xgboost_model_{city}.pkl'
    joblib.dump(multi_model, model_name)
   
    last_timestamp = df['Timestamp'].iloc[-1]
    # Save it to a file
    time_stamp_file = f"utils/xgboost_data/{city}_last_trained_timestamp.txt"
    with open(time_stamp_file, "w") as f:
        f.write(str(last_timestamp))
    print("model trained till",last_timestamp)
    return multi_model

def predict(city = 'Rawalpindi'):
    model_path = f"utils/xgboost_data/models/xgboost_model_{city}.pkl"
    if( not os.path.exists(model_path) ):
        print("model not trained yet/does not exist")
        return None
    else:
        # Load the model
        model = joblib.load(model_path)
        # Load the origin i-e current timestamp
        origin_point = datetime.now()
        #days defore current timestamp
        starting_point = origin_point - timedelta(days=4)
        #convert to string format
        origin_point_str = origin_point.strftime('%Y-%m-%dT%H:%M:%S')
        starting_point_str = starting_point.strftime('%Y-%m-%dT%H:%M:%S')
        #getting the data from api
        df_data = get_history_data(key= api_key,start_date=starting_point_str, end_date=origin_point_str, city_name=city, mode="Data" )
        if not isinstance(df_data, pd.DataFrame):
            return df_data, None  # Return the error message and None
        df = df_data.sort_values("Timestamp").reset_index(drop=True)
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
        os.makedirs("utils/xgboost_data", exist_ok=True)
        pridictions_file = f"utils/xgboost_data/predictions_{city}.csv"
        pred_df.to_csv(pridictions_file, index=False)
        return pred_df, origin_point
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="give arg action the following values: train or predict")
    parser.add_argument("action", type=str, help="train or predict")
    parser.add_argument("--city", type=str, help="Optional city name for prediction")

    args = parser.parse_args()

    if args.action == "train":
        training(city = args.city if args.city else 'Rawalpindi')

    if args.action == "predict":
        predictions = predict(city = args.city if args.city else 'Rawalpindi')
        print(predictions)