import os
import glob
import requests
import time
import pandas as pd

# Define the path to the 'ready' directory
ready_dir = './'  # Update this to the actual path

# List all .py files in the 'ready' directory
py_files = glob.glob(os.path.join(ready_dir, '*.py'))

# Base URL and headers for the API
url = 'https://api.hyperliquid.xyz/info'
headers = {'Content-Type': 'application/json'}

# Iterate over the Python files to extract coin names
for file_path in py_files:
    coin = os.path.basename(file_path).split('.')[0]

    # Specific case correction for known coin names
    if coin.upper() == "KPEPE":
        coin = "kPEPE"  # Correct case for kPEPE
    elif coin.upper() == "KBONK":
        coin = "kBONK"  # Assume "kBONK" is the correct format; adjust as necessary
    else:
        coin = coin.upper()
    
    # Calculate start time and end time
    current_time = int(time.time()) * 1000  # in milliseconds
    two_weeks_in_milliseconds = 14 * 24 * 60 * 60 * 1000
    interval = '1m'
    start_time = current_time - two_weeks_in_milliseconds
    end_time = current_time

    data = {
      "type": "candleSnapshot",
      "req": {
        "coin": coin,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time
      }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        candles_data = response.json()
        if candles_data and isinstance(candles_data, list) and isinstance(candles_data[0], dict):
            candles = []
            for candle in candles_data:
                candles.append({
                    'Timestamp': pd.to_datetime(candle['t'], unit='ms'),
                    'Open': candle['o'],
                    'High': candle['h'],
                    'Low': candle['l'],
                    'Close': candle['c'],
                    'Volume': candle['v'],
                })
            new_df = pd.DataFrame(candles).set_index('Timestamp')

            # File path for saving
            filename = os.path.join(ready_dir, f"{coin}.csv")
            
            # Check if the file exists to append without duplicating
            if os.path.exists(filename):
                existing_df = pd.read_csv(filename, index_col='Timestamp', parse_dates=['Timestamp'])
                # Filter new data for rows not in existing data
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates()
            else:
                combined_df = new_df

            print(f"Attempting to save candle data to {filename}")
            combined_df.to_csv(filename)
            print(f"Candle data saved to {filename}")
        else:
            print(f'Invalid candle data for {coin}:', candles_data)
    else:
        print(f"Error {response.status_code} retrieving candle data for {coin}: {response.reason}")

print("Done processing all coins.")
