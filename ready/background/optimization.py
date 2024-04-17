import json
import redis
import pickle
import optuna
from optuna.storages import JournalRedisStorage, JournalStorage
from optuna.visualization import plot_optimization_history
from dask.distributed import Client, as_completed
from .trials.backtest import CryptoBacktester
import sys
import cProfile
import logging
import warnings
import argparse
import cloudpickle
from distributed.protocol import serialize, deserialize
import os
import hashlib
from optuna.pruners import HyperbandPruner
from tqdm import tqdm 
import os
import sys



output_directory = '../optimization'
os.makedirs(output_directory, exist_ok=True)

warnings.filterwarnings('ignore', category=optuna.exceptions.ExperimentalWarning)
pruner = HyperbandPruner(min_resource=1, reduction_factor=3, max_resource='auto')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
redis_client = redis.Redis(host='10.0.0.201', port=6379, db=0, decode_responses=True)
redis_url = "redis://10.0.0.201:6379/0"
storage = JournalStorage(JournalRedisStorage("redis://10.0.0.201:6379"))

def test_serialization(obj, obj_name):
    try:
        cloudpickle.dumps(obj)
        logger.info(f"Serialization check passed for: {obj_name}")
    except Exception as e:
        logger.error(f"Failed to serialize {obj_name}: {str(e)}")


# Suppress experimental warnings
warnings.filterwarnings('ignore', category=optuna.exceptions.ExperimentalWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Redis client for caching
redis_client = redis.Redis(host='10.0.0.201', port=6379, db=0, decode_responses=True)

def safe_filename(params):
    """
    Generate a safe filename by hashing the input parameters.

    Parameters:
    - params (dict): The parameters used to generate the filename.

    Returns:
    - str: A hashed filename ensuring no conflicts or invalid characters.
    """
    params_string = json.dumps(params, sort_keys=True)
    filename_hash = hashlib.md5(params_string.encode()).hexdigest()
    return f"{filename_hash}_results.json"


def objective(params, redis_url, csv_path, symbol):
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    params_key = json.dumps(params, sort_keys=True)
    cached_results = redis_client.get(params_key)
    if cached_results:
        return json.loads(cached_results)
    
    backtester = CryptoBacktester(csv_path, symbol, params)
    results = backtester.run_backtest()
    redis_client.set(params_key, json.dumps(results))
    return results

def run_optimization(client, n_trials=100):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    storage = JournalStorage(JournalRedisStorage(redis_url))
    csv_directory = os.path.join(script_dir, '../')
    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]

    for csv_file in csv_files:
        symbol = csv_file.replace('.csv', '').upper()
        study = optuna.create_study(direction="minimize", storage=storage, pruner=pruner, study_name=symbol, load_if_exists=True)
        futures = []

        for _ in tqdm(range(n_trials), desc=f"Optimizing {symbol}", unit="trial"):
            trial = study.ask()
            params = {
                'rsi_entry': trial.suggest_int('rsi_entry', 10, 40, step=2),
                'rsi_exit': trial.suggest_int('rsi_exit', 60, 80, step=2),
                'atr_multiplier': trial.suggest_float('atr_multiplier', 2, 3, step=0.50),
                'reward_risk_ratio': trial.suggest_float('reward_risk_ratio', 0.5, 3, step=0.25),
                'adx_period': trial.suggest_int('adx_period', 5, 35, step=10),
                'ema_adx': trial.suggest_int('ema_adx', 10, 40, step=10),
                'ema_close': trial.suggest_int('ema_close', 10, 100, step=10),
                'volume_ema_period': trial.suggest_int('volume_ema_period', 5, 30, step=1),
            }
            csv_path = os.path.join(csv_directory, csv_file)
            future = client.submit(objective, params, redis_url, csv_path=csv_path, symbol=symbol)
            futures.append(future)

        # Gather results from all futures
        results = client.gather(futures)
        all_results = {f"trial_{i}": result for i, result in enumerate(results)}
        best_trial = max(all_results.items(), key=lambda x: x[1]['total_pnl'], default=(None, {'total_pnl': float('-inf')}))

        ordered_results = {}
        if best_trial[0]:
            ordered_results['best_trial'] = best_trial
            del all_results[best_trial[0]]  # Avoid duplication

        ordered_results.update(all_results)

        # Save the ordered results to a JSON file
        symbol_output_directory = os.path.join(output_directory, symbol)
        os.makedirs(symbol_output_directory, exist_ok=True)
        with open(os.path.join(symbol_output_directory, f'{symbol}_results.json'), 'w') as f:
            json.dump(ordered_results, f, indent=4)

    return ordered_results

def perform_analysis():
    """Load results and produce analysis plots."""
    from analyze_results import load_results, plot_pairplot, plot_heatmap
    results_df = load_results('../ETH_backtest_results.csv')
    plot_pairplot(results_df)
    plot_heatmap(results_df, 'rsi_entry', 'atr_multiplier', 'total_pnl')

def main():
    parser = argparse.ArgumentParser(description="Run optimization and analysis of crypto backtesting.")
    parser.add_argument("--optimize", action="store_true", help="Run optimization")
    args = parser.parse_args()
    client = Client('tcp://10.0.0.201:8786')
    pr = cProfile.Profile()
    pr.enable()
    if args.optimize:
        run_optimization(client, 400000)
    else:
        logger.info("No optimization flag provided, running a default function...")
        run_optimization(client, 10)
    pr.disable()
    pr.print_stats(sort='time')

if __name__ == "__main__":
    main()

    '''
    dask scheduler    
    dask worker tcp://10.0.0.201:8786 --nworkers 24 --nthreads 1 --memory-limit 3GB 
    dask worker tcp://10.0.0.201:8786 --nworkers 20 --nthreads 1 --memory-limit 3GB  

    python -m background.optimization --optimize   
    
    '''