import pandas as pd
import logging
from optimization.ready.background.optimization import optimize_parameters
from optimization.ready.background.backtest.backtest import backtest

# Configure the logging module
logging.basicConfig(filename='error.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        # Specify the cryptocurrency file you want to process
        crypto_file = 'BNB.csv'
        crypto_name = crypto_file.replace('.csv', '')  # Corrected for '.csv'
        data_file = f'{crypto_file}'

        data = pd.read_csv(data_file, parse_dates=['Timestamp']).set_index('Timestamp')
        

        logging.info(f"Data for {crypto_name.upper()} after dropping NaNs:\n{data}")


        logging.info(f"Starting optimization for {crypto_name.upper()}...")
        best_params = optimize_parameters(data, output_folder='optimized', crypto_name=crypto_name)
        logging.info(f"Optimization completed for {crypto_name.upper()}. Best Parameters: {best_params}")

        if best_params is not None and len(best_params) > 1:
            logging.debug(f"Calling backtest with parameters: {best_params[1:]}")
            sharpe_ratio, expectancy, win_rate, pnl, volatility, max_drawdown, trades_df = backtest(data, *best_params)
        else:
            logging.error("Invalid best parameters from optimization.")
            return

        print(f"Backtest Results for {crypto_name.upper()} - Sharpe Ratio: {sharpe_ratio}, Expectancy: {expectancy}, Win Rate: {win_rate}%, PnL: {pnl}, Volatility: {volatility}, Max Drawdown: {max_drawdown}%")

        # Optionally, save the backtest results to a separate file
        backtest_results_file = f'{crypto_name}_backtest_results_test.csv'
        trades_df.to_csv(backtest_results_file, index=False)
    except Exception as e:
        logging.error(f'Error occurred: {e}, Type: {type(e).__name__}')
        raise

if __name__ == "__main__":
    main()