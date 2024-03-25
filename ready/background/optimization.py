import itertools
import pandas as pd
import numpy as np
from background.backtest import backtest
from tqdm import tqdm
from multiprocessing import Pool
import os

def optimize_parameters_worker(params):
    # Unpack all parameters including the new EMAs and pass them to the backtest function
    result = backtest(*params)
    return result, params
def optimize_parameters(data, output_folder='optimized', crypto_name='crypto', top_n=5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    top_results_file = os.path.join(output_folder, f'{crypto_name}_top_results.csv')
    top_pnl_file = os.path.join(output_folder, f'{crypto_name}_top_pnls.csv')

    top_params = []
    
    param_ranges = {
        'rsi_entry_range': range(20, 40, 2),
        'rsi_exit_range': range(60, 80, 2),
        'atr_multiplier_range': np.arange(1, 3.0, 0.50),
        'reward_ratio_range': np.arange(0.50, 3, 0.25),
        'rsi_period': range(10, 15, 5),
        'atr_period': range(14, 15),
        'adx_period': range(5, 30, 5),
        'ema_close_period': range(5, 100, 5),
        'ema_adx_period': range(5, 100, 5),
    }

    # Generate all combinations of parameters
    param_combinations = [(data,) + p for p in itertools.product(*param_ranges.values())]

    with Pool() as pool:
        results = list(tqdm(pool.imap_unordered(optimize_parameters_worker, param_combinations), total=len(param_combinations), desc="Optimization Progress"))

        for result, params in results:
            try:
                win_rate, pnl = result[2], result[3]  # Assuming result structure includes win rate at index 2 and PnL at index 3
                params_without_data = params[1:]  # Exclude 'data' from params
                top_params.append((win_rate, pnl, params_without_data))
            except Exception as e:
                print(f"Error processing result: {e}")

    # Sort and write the top win rates to the file
    top_sorted_by_win_rate = sorted(top_params, key=lambda x: x[0], reverse=True)[:top_n]
    save_to_file(top_sorted_by_win_rate, top_results_file)

    # Sort and write the top PnLs to the file, including win rates
    top_sorted_by_pnl = sorted(top_params, key=lambda x: x[1], reverse=True)[:top_n]
    save_to_file(top_sorted_by_pnl, top_pnl_file, include_win_rate=True)

def save_to_file(sorted_data, file_path, include_win_rate=False):
    with open(file_path, 'w') as file:
        for win_rate, pnl, params in sorted_data:
            params_str = ', '.join([f"{name}: {value}" for name, value in zip(["RSI Entry", "RSI Exit", "ATR Multiplier", "Reward Ratio", "RSI Period", "ATR Period", "ADX Period", "EMA Period", "EMA"], params)])
            if include_win_rate:
                file.write(f'PnL: {pnl}, Win Rate: {win_rate}%, Parameters: ({params_str})\n')
            else:
                file.write(f'Win Rate: {win_rate}%, PnL: {pnl}, Parameters: ({params_str})\n')

    print(f"Data saved to {file_path}")

print("\nA new best paramater.")