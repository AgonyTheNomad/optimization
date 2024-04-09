import optuna
from tqdm import tqdm
from backtest import CryptoBacktester
from joblib import Parallel, delayed
from analyze_results import load_results, plot_pairplot, plot_heatmap
import pandas as pd
import sys
import json
import os

def objective(trial):
    # Define the parameter space using Optuna
    params = {
        'rsi_entry': trial.suggest_float('rsi_entry', 10, 40),
        'rsi_exit': trial.suggest_float('rsi_exit', 60, 80),
        'atr_multiplier': trial.suggest_float('atr_multiplier', 1, 5),
        'reward_risk_ratio': trial.suggest_float('reward_risk_ratio', 0.5, 3),
        'adx_period': trial.suggest_int('adx_period', 5, 30),
        'ema_adx': trial.suggest_int('ema_adx', 10, 50),
        'ema_close': trial.suggest_int('ema_close', 2, 100),
        'volume_ema_period': trial.suggest_int('volume_ema_period', 5, 30),
    }

    backtester = CryptoBacktester('../ETH.csv', 'ETH', params)
    total_pnl, win_rate, total_trades, max_drawdown = backtester.run_backtest()

    alpha, beta, gamma, delta = 0.5, 0.3, 100, 0.1
    expected_trades = 50000
    composite_score = (
        (total_pnl * alpha) -
        (max_drawdown * beta) +
        (win_rate * gamma) -
        (abs(expected_trades - total_trades) * delta)
    )

    # Set custom attributes for the trial
    trial.set_user_attr("total_pnl", total_pnl)
    trial.set_user_attr("win_rate", win_rate)
    trial.set_user_attr("total_trades", total_trades)
    trial.set_user_attr("max_drawdown", max_drawdown)
    trial.set_user_attr("composite_score", composite_score)

    return -composite_score


def run_optimization():
    study = optuna.create_study(direction='minimize', pruner=optuna.pruners.MedianPruner())
    n_trials = 50000
    # Use n_jobs=-1 to use all available CPU cores
    study.optimize(objective, n_trials=n_trials, n_jobs=50, show_progress_bar=True)

    best_params = study.best_params
    print(f"Best Parameters: {best_params}")
    save_trial_results(study)
    return best_params

def save_trial_results(study):
    results_path = "./optimization_results_detailed.json"
    detailed_results = []
    for trial in study.trials:
        detailed_results.append({
            "number": trial.number,
            "value": trial.value,
            "params": trial.params,
            "total_pnl": trial.user_attrs["total_pnl"],
            "win_rate": trial.user_attrs["win_rate"],
            "total_trades": trial.user_attrs["total_trades"],
            "max_drawdown": trial.user_attrs["max_drawdown"],
            "composite_score": trial.user_attrs["composite_score"],
        })
    
    with open(results_path, "w") as file:
        json.dump(detailed_results, file, indent=4)
    
    print(f"Saved detailed optimization results to {results_path}")


def perform_analysis():
    results_df = load_results('../ETH_backtest_results.csv')
    plot_pairplot(results_df)
    plot_heatmap(results_df, 'rsi_entry', 'atr_multiplier', 'total_pnl')

# At the end of your backtesting script
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "optimize":
            best_params = run_optimization()
            # Optionally, you can run a backtest with the best parameters found and save those results
            # Ensure best_params is formatted correctly to be accepted by set_trading_params
            backtester = CryptoBacktester('../ETH.csv', 'ETH', best_params)
            backtester.set_trading_params(best_params)
            backtester.run_backtest()
        elif sys.argv[1] == "analyze":
            perform_analysis()
        else:
            print("Invalid argument. Use 'optimize' or 'analyze'.")
    else:
        print("No argument provided. Please specify 'optimize' or 'analyze'.")
