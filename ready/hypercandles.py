import requests
import time
import pandas as pd

url = 'https://api.hyperliquid.xyz/info'
headers = {'Content-Type': 'application/json'}

# replace "COIN_NAME" with your desired coin name

coin = "kPEPE"


# calculate start time and end time
current_time = int(time.time()) * 1000  # in milliseconds
interval = '5m'  # desired interval
num_intervals = 17280  # number of intervals in 24 hours (24 * 60 / )
start_time = current_time - num_intervals * int(interval[:-1]) * 60 * 1000  # in milliseconds
end_time = current_time

# build request body
data = {
  "type": "candleSnapshot",
  "req": {
    "coin": coin,
    "interval": interval,
    "startTime": start_time,
    "endTime": end_time
  }
}

# send HTTP POST request and retrieve candle data
response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
  candles_data = response.json()
  if candles_data and isinstance(candles_data[0], dict):
    # parse candle data into dataframe with datetime index
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

    # save data to CSV file with coin name in filename
    filename = f"{coin}.csv"
    df.to_csv(filename)
    print(f"Candle data saved to {filename}")
  else:
    print('Invalid candle data:', candles_data)
else:
  print(f"Error {response.status_code} retrieving candle data: {response.reason}")