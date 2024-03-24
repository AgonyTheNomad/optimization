import os
import glob
import requests
import time
import pandas as pd

# Define the path to the 'ready' directory
ready_dir = './'   # Update this to the actual path

# List all .py files in the 'ready' directory
py_files = glob.glob(os.path.join(ready_dir, '*.py'))

# Base URL and headers for the API
url = 'https://api.hyperliquid.xyz/info'
headers = {'Content-Type': 'application/json'}

# Iterate over the Python files to extract coin names
for file_path in py_files:
    # Extract the coin name from the file name (assuming the file name is the coin name)
    coin = os.path.basename(file_path).split('.')[0].upper()
    
    # Calculate start time and end time
    current_time = int(time.time()) * 1000  # in milliseconds
    interval = '5m'  # desired interval
    num_intervals = 17280  # number of intervals in 24 hours (24 * 60 / 5)
    start_time = current_time - num_intervals * int(interval[:-1]) * 60 * 1000  # in milliseconds
    end_time = current_time

    # Build request body
    data = {
      "type": "candleSnapshot",
      "req": {
        "coin": coin,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time
      }
    }

    # Send HTTP POST request and retrieve candle data
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        candles_data = response.json()
        print(f"Received data for {coin}: {candles_data}")
        if candles_data and isinstance(candles_data, list) and isinstance(candles_data[0], dict):
            # Parse candle data into dataframe with datetime index
            candles = []
            for candle in candles_data:
                c = {
                    'Timestamp': candle['t'],
                    'Open': candle['o'],
                    'High': candle['h'],
                    'Low': candle['l'],
                    'Close': candle['c'],
                    'Volume': candle['v'],
                }
                candles.append(c)
            df = pd.DataFrame(candles)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df = df.set_index('Timestamp')

            # Save data to CSV file with coin name in filename
            filename = f"{coin}.csv"
            print(f"Attempting to save candle data to {os.path.join(ready_dir, filename)}")
            df.to_csv(os.path.join(ready_dir, filename))
            print(f"Candle data saved to {filename}")
        else:
            print(f'Invalid candle data for {coin}:', candles_data)
    else:
        print(f"Error {response.status_code} retrieving candle data for {coin}: {response.reason}")


print("Done processing all coins.")
