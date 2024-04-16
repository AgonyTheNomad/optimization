import pandas as pd
import talib
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import json




# Example cryptocurrency - you might loop through or select based on your dataset

class CryptoBacktester:
    def __init__(self, candle_csv_path, crypto_symbol, params):
        self.set_trading_params(params)
        self.candle_csv_path = candle_csv_path
        self.load_data()
        self.initialize_state()
        self.equity_curve = [self.starting_balance]


    def load_config(self, config_path, crypto_symbol):
        with open(config_path, 'r') as file:
            config = json.load(file)
        params = config['cryptocurrencies'][crypto_symbol]
        self.set_trading_params(params)

    def set_trading_params(self, params):
        self.params = params
        self.RSI_ENTRY_THRESHOLD_LOW = params['rsi_entry']
        self.RSI_EXIT_THRESHOLD_HIGH = params['rsi_exit']
        self.ATR_MULTIPLIER = params['atr_multiplier']
        self.REWARD_RATIO = params['reward_risk_ratio']
        self.ADX_PERIOD = params['adx_period']
        self.EMA_PERIOD = params['ema_adx']
        self.EMA_CLOSE = params['ema_close']
        self.volume_ema_period = params['volume_ema_period']
        self.RSI_PERIOD = 10
        self.ATR_PERIOD = 14
        self.risk_percent = 0.003
        self.starting_balance = 1000
        self.tf = 0.00035
        self.mf = 0.0001
        self.slippage = .0002

    def initialize_state(self):
        self.balance = self.starting_balance
        self.peak_balance = self.balance
        self.position = 0
        self.total_trades = self.winning_trades = self.losing_trades = 0
        self.max_drawdown = 0
        self.pnl_list = []
        self.trades = []

    def calculate_rsi(self, data):
        return talib.RSI(data['Close'], timeperiod=self.RSI_PERIOD)

    def calculate_atr(self, data):
        return talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=self.ATR_PERIOD)

    def calculate_adx(self, data):
        adx = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=self.ADX_PERIOD)
        ema_adx = talib.EMA(adx, timeperiod=self.EMA_PERIOD)
        return adx, ema_adx

    def calculate_ema(self, data):
        if len(data) < self.EMA_CLOSE or data['Close'].isnull().any():
            return None
        return talib.EMA(data['Close'], timeperiod=self.EMA_CLOSE)
    
    def load_data(self):
        try:
            self.data = pd.read_csv(self.candle_csv_path, parse_dates=['Timestamp'], index_col='Timestamp')
            self.calculate_indicators()
        except FileNotFoundError:
            print(f"Error: The file {self.candle_csv_path} was not found.")
        except pd.errors.EmptyDataError:
            print("Error: The file is empty.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def calculate_indicators(self):
        # Directly use the attributes set in set_trading_params
        self.data['EMA'] = talib.EMA(self.data['Close'], timeperiod=self.EMA_CLOSE)
        self.data['RSI'] = talib.RSI(self.data['Close'], timeperiod=self.RSI_PERIOD)
        self.data['ATR'] = talib.ATR(self.data['High'], self.data['Low'], self.data['Close'], timeperiod=self.ATR_PERIOD)
        self.data['ADX'] = talib.ADX(self.data['High'], self.data['Low'], self.data['Close'], timeperiod=self.ADX_PERIOD)
        self.data['EMA_ADX'] = talib.EMA(self.data['ADX'], timeperiod=self.EMA_PERIOD)
        self.data['EMA_VOLUME'] = talib.EMA(self.data['Volume'], timeperiod=self.volume_ema_period)

    def calculate_total_pnl(self):
        """Calculate the total Profit and Loss from all closed trades."""
        return sum(trade['PnL'] for trade in self.trades if trade['PnL'] is not None)
    
    def calculate_total_trades(self):
        """Calculate the total number of trades."""
        return len(self.trades)

    def calculate_win_rate(self):
        """Calculate the win rate as the percentage of trades that were profitable."""
        if not self.trades:
            return 0
        winning_trades = sum(1 for trade in self.trades if trade['PnL'] and trade['PnL'] > 0)
        return winning_trades / len(self.trades)
    
    def calculate_max_drawdown(self):
        """Calculate the maximum drawdown of the equity curve."""
        peak = self.equity_curve[0]
        max_drawdown = 0
        for balance in self.equity_curve:
            if balance > peak: 
                peak = balance
            drawdown = (peak - balance) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown

    def backtest_logic(self):
        prev_rsi = None
        for i, row in self.data.iterrows():
            if prev_rsi is not None:  # Skip the first row since prev_rsi is not available
                self.evaluate_trade_entry(row, prev_rsi)
                self.evaluate_trade_exit(row)
            prev_rsi = row['RSI']


    def evaluate_trade_entry(self, row, prev_rsi):
        rsi = row['RSI']
        adx = row['ADX']
        ema_adx = row['EMA_ADX']
        close = row['Close']
        atr = row['ATR']
        current_volume = row['Volume']
        ema_volume = row['EMA_VOLUME']
        if current_volume > ema_volume:
            if adx > ema_adx and self.position == 0:
                if rsi < self.RSI_ENTRY_THRESHOLD_LOW and prev_rsi > self.RSI_ENTRY_THRESHOLD_LOW and close > self.data['EMA'].iloc[-1]:
                    # Long trade logic
                    self.enter_trade_logic(row, 'Long')
                elif rsi > self.RSI_EXIT_THRESHOLD_HIGH and prev_rsi < self.RSI_EXIT_THRESHOLD_HIGH and close < self.data['EMA'].iloc[-1]:
                    # Short trade logic
                    self.enter_trade_logic(row, 'Short')

    def enter_trade_logic(self, row, trade_type):
        close = row['Close']
        atr = row['ATR']
        # Determine stop_loss based on trade type
        stop_loss = close - atr * self.ATR_MULTIPLIER if trade_type == 'Long' else close + atr * self.ATR_MULTIPLIER
        trade_open_price = close
        diff = abs(trade_open_price - stop_loss)
        # Determine take_profit based on trade type and diff
        take_profit = trade_open_price + diff * self.REWARD_RATIO if trade_type == 'Long' else trade_open_price - diff * self.REWARD_RATIO

        # Calculate adjusted position size
        position_size = self.calculate_position_size(row)

        cost_of_entry = position_size * trade_open_price
        maker_fee = cost_of_entry * self.mf
        self.balance -= maker_fee
        self.equity_curve.append(self.balance)

        # Append the trade with all required keys
        new_trade = {
            'Open Timestamp': row.name,
            'Open Price': trade_open_price,
            'Stop Loss': stop_loss,
            'Take Profit': take_profit,
            'Trade Type': trade_type,
            'Position Size': position_size,
            'is_open': True,
            'PnL': None,
            'New Balance': None,
            'Maker Fee': maker_fee
        }

        # Append the new trade to self.trades
        self.trades.append(new_trade)

        # Increment position counter
        self.position += 1


    def calculate_position_size(self, row):
        # Assuming 'trade_open_price' and 'stop_loss' are already defined in your context. If not, they need to be calculated before this method.
        trade_open_price = row['Close']  # This is an example; adjust according to your entry strategy
        atr = row['ATR']
        stop_loss = trade_open_price - atr * self.ATR_MULTIPLIER  # Calculate stop loss based on ATR

        diff = trade_open_price - stop_loss
        risk_amount = self.balance * self.risk_percent  # Total amount willing to risk
        # Calculate the initial position size without considering fees and slippage
        initial_position_size = risk_amount / diff

        # Adjust the position size to account for trading fees and slippage
        leverage_amount = initial_position_size * stop_loss
        adjusted_leverage_amount = leverage_amount - (leverage_amount * self.tf) -(leverage_amount * self.slippage)/trade_open_price
        position_size = adjusted_leverage_amount / trade_open_price

        return position_size

    def evaluate_trade_exit(self, row):
        for index, trade in enumerate(self.trades):
            # Required keys for a valid trade object
            required_keys = ['Stop Loss', 'Take Profit', 'is_open']
            missing_keys = [key for key in required_keys if key not in trade]

            if missing_keys:
                continue  # Skip to the next trade if keys are missing

            if trade['is_open']:
                exit_trade = False
                if trade['Trade Type'] == 'Long':
                    # For a long trade, check if the day's high hit the take profit or the day's low hit the stop loss
                    if row['High'] >= trade['Take Profit'] or row['Low'] <= trade['Stop Loss']:
                        exit_trade = True
                elif trade['Trade Type'] == 'Short':
                    # For a short trade, check if the day's low hit the take profit or the day's high hit the stop loss
                    if row['Low'] <= trade['Take Profit'] or row['High'] >= trade['Stop Loss']:
                        exit_trade = True

                if exit_trade:
                    self.exit_trade(trade, row)





    def exit_trade(self, trade, row):
        if trade['is_open']:
            trade['Close Price'] = row['Close']
            trade['is_open'] = False
            trade['Close Timestamp'] = row.name  # Assuming row.name is the timestamp from your DataFrame index

            # Determine if the exit was due to stop loss or take profit to apply the correct fee
            exit_due_to_stop_loss = trade['Close Price'] <= trade['Stop Loss'] if trade['Trade Type'] == 'Long' else trade['Close Price'] >= trade['Stop Loss']
            fee_multiplier = self.tf if exit_due_to_stop_loss else self.mf

            # Calculate the cost of exit including the fee using the 'Position Size' from the trade
            cost_of_exit = trade['Position Size'] * trade['Close Price']
            fee = cost_of_exit * fee_multiplier

            # Adjust pnl calculation to account for the fee
            if trade['Trade Type'] == 'Long':
                pnl = (trade['Close Price'] - trade['Open Price']) * trade['Position Size'] - fee
            elif trade['Trade Type'] == 'Short':
                pnl = (trade['Open Price'] - trade['Close Price']) * trade['Position Size'] - fee
            else:
                raise ValueError(f"Unknown trade type: {trade['Trade Type']}")
            self.balance += pnl
            trade['PnL'] = pnl
            trade['Fee'] = fee
            trade['New Balance'] = self.balance
            self.equity_curve.append(self.balance)
            self.position -= 1

            # Log the trade exit with fee details

    def run_backtest(self):
        """Run the backtest and return performance metrics in a dictionary format."""
        self.backtest_logic()
        total_pnl = self.calculate_total_pnl()
        win_rate = self.calculate_win_rate()
        total_trades = self.calculate_total_trades()
        max_drawdown = self.calculate_max_drawdown()
        
        # Prepare the results in dictionary format
        results = {
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'max_drawdown': max_drawdown
        }
        
        # This can still save the trade data to a file
        
        return results


