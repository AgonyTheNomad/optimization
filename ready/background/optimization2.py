import itertools
import pandas as pd
import numpy as np
from background.backtest2 import backtest
from tqdm import tqdm
from multiprocessing import Pool
import os

def optimize_parameters_worker(params):
    # Unpack all parameters including 'ema_1'
    data, rsi_entry, rsi_exit, atr_multiplier, reward_ratio, adx_period, ema_period, ema_close, ema_1 = params
    # Execute backtest
    result = backtest(data, rsi_entry, rsi_exit, atr_multiplier, reward_ratio, adx_period, ema_period, ema_close, ema_1)
    # Flatten the result and params into a single tuple
    return (*result, rsi_entry, rsi_exit, atr_multiplier, reward_ratio, adx_period, ema_period, ema_close, ema_1)



def optimize_parameters(data, output_folder='optimized', crypto_name='crypto', top_n=5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    top_results_file = os.path.join(output_folder, f'{crypto_name}_top_results_ema.csv')
    top_pnl_file = os.path.join(output_folder, f'{crypto_name}_top_pnls_ema.csv')

    param_ranges = {
        'rsi_entry': [30],  # Example range, replace with actual range if different
        'rsi_exit': [60],  # Example range, replace with actual range if different
        'atr_multiplier': [2.0],  # Example range, replace with actual range if different
        'reward_ratio': [2.0],  # Example range, replace with actual range if different
        'adx_period': [5],  # Example range, replace with actual range if different
        'ema_period': [20],  # Example range, replace with actual range if different
        'ema_close': range(2, 100, 1),  # Your specified range
        'ema_1': range(2, 100, 1),  # Your specified range for ema_1
    }

    # Generate all combinations of parameters, including 'data' at the start of each tuple
    param_combinations = [
    (data,) + combo
    for combo in itertools.product(
        param_ranges['rsi_entry'],
        param_ranges['rsi_exit'],
        param_ranges['atr_multiplier'],
        param_ranges['reward_ratio'],
        param_ranges['adx_period'],
        param_ranges['ema_period'],
        param_ranges['ema_close'],
        param_ranges['ema_1']
    )
]

    num_cpus = os.cpu_count() or 1
    num_processes = max(1, num_cpus // 3)

    with Pool(processes=num_processes) as pool:
        results = list(tqdm(pool.imap_unordered(optimize_parameters_worker, param_combinations), total=len(param_combinations), desc="Optimization Progress"))

    processed_results = []
    for result in results:
        processed_results.append(result)  # Assuming result is already a tuple with the required structure

    # Sort by win rate then by PnL and select top_n results
    top_by_win_rate = sorted(processed_results, key=lambda x: x[2], reverse=True)[:top_n]
    top_by_pnl = sorted(processed_results, key=lambda x: x[3], reverse=True)[:top_n]

    save_to_file(top_by_win_rate, top_results_file)
    save_to_file(top_by_pnl, top_pnl_file)

def save_to_file(sorted_data, file_path):
    with open(file_path, 'w') as file:
        for entry in sorted_data:
            # Unpack results, assuming the first 7 values are as described above, and the rest are parameters
            *results, rsi_entry, rsi_exit, atr_multiplier, reward_ratio, adx_period, ema_period, ema_close, ema_1 = entry
            sharpe_ratio, expectancy, win_rate, pnl, volatility, max_drawdown, total_trades = results
            # Now format the line including all parameters
            line = f"PnL: {pnl}, Win Rate: {win_rate}%, Total Trades: {total_trades}, Parameters: (RSI Entry: {rsi_entry}, RSI Exit: {rsi_exit}, ATR Multiplier: {atr_multiplier}, Reward Ratio: {reward_ratio}, ADX Period: {adx_period}, EMA Period: {ema_period}, EMA Close: {ema_close}, EMA_1: {ema_1})\n"
            file.write(line)
    print(f"Data successfully saved to {file_path}")




print("\nA new best paramater.")