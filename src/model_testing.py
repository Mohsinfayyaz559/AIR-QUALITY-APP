import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import os
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor

##################################### LOAD DATA #####################################

# Read the CSV
df = pd.read_csv(r"utils\air_quality_historic_data_csv\historical_air_pollution_all_Rawalpindi.csv")

# PREPROCESSING time 
# Convert 'Date' to datetime
df['Date'] = pd.to_datetime(df['Timestamp'])
# Set 'Date' as index
df.set_index('Date', inplace=True)
# sorting by date
df = df.sort_values('Timestamp')

######################################## PREPROCESSING data (Feature enginnering) ######################################
# Create lag features
lag_hours = 30 # Number of lag features to create

lag_features = []
for lag in range(1, lag_hours + 1):
    for col in ['AQI', 'PM2.5', 'PM10', 'CO', 'NO', 'NO2', 'O3', 'SO2', 'NH3']:
        lag_col = df[col].shift(lag)
        lag_features.append(lag_col.rename(f'{col}_lag_{lag}'))

df_lagged = pd.concat([df] + lag_features, axis=1)

# === Forecast Targets ===
forecast_horizon = 12 # Number of hours to forecast
target_features = [df['AQI'].shift(-h).rename(f'AQI_t+{h}') for h in range(1, forecast_horizon + 1)]
df = pd.concat([df_lagged] + target_features, axis=1)

# Drop NaNs and reset index
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)



df.to_csv(r"utils/xgboost_data/historical_air_pollution_rawalpindi_lagged.csv", index= True)
###################################### SPLIT DATA #####################################
# Define the features and target variable
feature_cols = [col for col in df.columns if 'lag' in col]
target_cols = [col for col in df.columns if 'AQI_t+' in col]


# Split train/test
test_size = 8000 
X_train = df[:-test_size][feature_cols]
Y_train = df[:-test_size][target_cols]
X_test = df[-test_size:][feature_cols]
Y_test = df[-test_size:][target_cols]

################################## Train MultiOutput XGBoost #############################
# Initialize the base model
base_model = XGBRegressor(
    n_estimators=50, 
    learning_rate=0.1,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    n_jobs=-1,
    verbosity=0
)
# Initialize the multi-output model
multi_model = MultiOutputRegressor(base_model)
# Fit the model on the training data
multi_model.fit(X_train, Y_train)

################################### making predictions ####################################
# Make predictions on the test data
Y_pred = multi_model.predict(X_test)
Y_pred = np.rint(np.asarray(Y_pred, dtype=float)).astype(int)  # Ensure Y_pred is float array before rounding
preds_df = pd.DataFrame(Y_pred, columns=[f'Forecast_t+{i}' for i in range(1, forecast_horizon+1)])
actuals_df = Y_test.reset_index(drop=True)

##################################### error metrics #####################################
# === Metrics ===
errors = []
for h in range(1, forecast_horizon + 1):
    y_true = actuals_df[f"AQI_t+{h}"]
    y_pred = preds_df[f"Forecast_t+{h}"]
    rmse = root_mean_squared_error (y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    errors.append({'Horizon': h, 'RMSE': round(rmse, 2), 'MAE': round(mae, 2)})

error_df = pd.DataFrame(errors)
print("\nError Metrics:")
print(error_df)
error_df.to_csv(r'utils/xgboost_data/forecast_errors_multioutput.csv', index=False)
preds_df.to_csv(r'utils/xgboost_data/forecast_multioutput.csv', index=False)