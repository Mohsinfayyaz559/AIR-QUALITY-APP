from statsmodels.graphics.tsaplots import plot_pacf  # Added for PACF
import pandas as pd
import matplotlib.pyplot as plt
import os

# Get the current script's directory
current_dir = os.path.dirname(__file__)
# Construct the relative path to the CSV
csv_path = os.path.join(current_dir, '..', 'utils', 'air_quality_historic_data_csv', 'historical_air_pollution_2022-01-01_to_2025-3-01_rawalpindi.csv')

# Normalize the path
csv_path = os.path.abspath(csv_path)
# Read the CSV
df = pd.read_csv(csv_path)

##################################### PREPROCESSING time #####################################
# Convert 'Date' to datetime
df['Date'] = pd.to_datetime(df['Timestamp'])
# Set 'Date' as index
df.set_index('Date', inplace=True)
# sorting by date
df = df.sort_values('Timestamp')

########################################## ploting ######################################
plt.figure(figsize=(10, 4))
plot_pacf(df['PM2.5'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of PM2.5")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['NO2'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['PM10'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['NH3'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['SO2'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['O3'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['NO'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plot_pacf(df['CO'].dropna(), lags=40, method='ywm')
plt.title("Partial Autocorrelation of NO2")
plt.xlabel("Lag (hours)")
plt.ylabel("PACF")
plt.tight_layout()
plt.show()
