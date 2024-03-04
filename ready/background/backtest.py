import pandas as pd
import numpy as np
from background.indicators import calculate_rsi, calculate_atr, calculate_adx

def backtest(data, rsi_entry, rsi_exit, atr_multiplier, reward_ratio, rsi_period, atr_period, adx_period, ema_period):
    balance = 1000
    starting_balance = balance
    risk_percent = .03
    peak_balance = balance
    position = 0
    total_trades = winning_trades = losing_trades = stop_loss_count = take_profit_count = 0
    max_drawdown = 0
    sum_wins = sum_losses = 0
    prev_rsi = None
    pnl_list = []  # List to store the PnL of each trade
    risk_free_rate_annual = 0.05
    risk_free_rate_58_days = (1 + risk_free_rate_annual) ** (58 / 252) - 1
    taker_main_fee = .00025
    maker_main_fee = .00002
    total_maker = 0
    total_taker = 0
    slippage = .0002
    

    trades = [] 

    data['RSI'] = calculate_rsi(data, rsi_period)
    data['ATR'] = calculate_atr(data, atr_period)
    data['ADX'], data['EMA_ADX'] = calculate_adx(data, adx_period, ema_period)

    for i in range(len(data)):
        try:
            row = data.iloc[i]
            rsi, close, high, low, atr, adx, ema_adx = row['RSI'], row['Close'], row['High'], row['Low'], row['ATR'], row['ADX'], row['EMA_ADX']

            if pd.isna([rsi, close, high, low, atr, adx, ema_adx]).any():
                continue

            pnl = 0
            trade_closed = False


            # Long trade entry condition
            if adx > ema_adx and position == 0:
                if rsi < rsi_entry and prev_rsi > rsi_entry:
                    # Long trade
                    stop_loss = close - atr * atr_multiplier 
                    trade_open_price = close
                    dif=trade_open_price-stop_loss
                    risk_amount= balance * risk_percent
                    take_profit = dif * reward_ratio + trade_open_price 
                    first_position = risk_amount/dif
                    leverage_amount = first_position * stop_loss
                    position = (leverage_amount - ((leverage_amount * taker_main_fee) - (leverage_amount * slippage)))/trade_open_price
                    start_taker = abs(position) * close * taker_main_fee
                    start_maker = -1 * abs(position) * close * taker_main_fee

                    trade_open_index = i
                    trade_type = 'Long'

                elif rsi > rsi_exit and prev_rsi < rsi_exit:
                    # Short trade
                    trade_open_price = close
                    stop_loss = close + atr * atr_multiplier
                    dif=trade_open_price - stop_loss
                    take_profit = dif  * reward_ratio + trade_open_price
                    risk_amount= balance * risk_percent
                    first_position = risk_amount/dif
                    leverage_amount = first_position * stop_loss
                    position = (leverage_amount - (10*(leverage_amount * taker_main_fee) - (leverage_amount * slippage)))/trade_open_price
                    start_taker = abs(position) * close * taker_main_fee
                    start_maker = -1 * abs(position) * close * taker_main_fee
                    trade_open_index = i
                    trade_type = 'Short'

                        # Check for opposite signal when in a long position
            if position > 0 and rsi > 64 and prev_rsi < 64:
                # Close long position logic
                taker = abs(position) * close * taker_main_fee
                pnl = close - trade_open_price - taker - start_taker
                # Opening short position logic (similar to your existing short trade logic)
                position = 0
                total_maker += start_taker
                total_taker -= taker
                trade_closed = True
            # Check for opposite signal when in a short position
            elif position < 0 and rsi < 34 and prev_rsi > 34:
                # Close short position logic
                taker = abs(position) * close * taker_main_fee
                pnl = trade_open_price - close - taker - start_taker
                # Opening long position logic (similar to your existing long trade logic)
                position = 0
                trade_closed = True




            if position != 0:
                if position > 0:
                    if low <= stop_loss:
                        taker = abs(position) * close * taker_main_fee
                        pnl = (stop_loss - trade_open_price) * abs(position) - taker + start_maker
                        position = 0
                        trade_closed = True
                        stop_loss_count += 1
                        total_maker += start_taker
                        total_taker -= taker

                    elif high >= take_profit:  # Replaced 'else' with 'elif'
                        maker = abs(position) * close * maker_main_fee 
                        pnl = (take_profit - trade_open_price) * abs(position) + start_maker + maker
                        position = 0
                        trade_closed = True
                        take_profit_count += 1
                        total_maker += start_taker
                        total_maker += maker

                elif position < 0:
                    if high >= stop_loss:
                        taker = abs(position) * close * taker_main_fee
                        pnl = (trade_open_price - stop_loss) * abs(position) - taker + start_maker
                        position = 0
                        trade_closed = True
                        stop_loss_count += 1
                        total_maker += start_taker
                        total_taker -= taker

                    elif low <= take_profit:  # Replaced 'else' with 'elif'
                        maker = abs(position) * close * maker_main_fee
                        pnl = (trade_open_price - take_profit) * abs(position) + start_maker + maker
                        position = 0
                        trade_closed = True
                        stop_loss_count += 1  # Adjusted count logic
                        take_profit_count += 1
                        total_maker += start_taker
                        total_taker += maker


            if trade_closed:

                pnl_list.append(pnl)  # Add the PnL of the closed trade to the list
                total_trades += 1
                winning_trades += (pnl > 0)
                losing_trades += (pnl < 0)
                sum_wins += max(0, pnl)
                sum_losses += min(0, pnl)
                balance += pnl 
                current_balance = balance
                peak_balance = max(peak_balance, current_balance)
                drawdown = 100 * ((peak_balance - current_balance) / peak_balance)
                max_drawdown = max(max_drawdown, drawdown)

                trade = {
                    'Open Index': trade_open_index,
                    'Close Index': i,
                    'Open Price': trade_open_price,
                    'Close Price': close,
                    'Position': position,
                    'Trade Type': trade_type,
                    'PnL': pnl,
                    'New Balance': balance
                }
                trades.append(trade)

            prev_rsi = rsi

        except Exception as e:
            print(f"Error on index {i}: {e}")

    pnl = sum(pnl_list)
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    volatility = np.std(pnl_list) if pnl_list else 0
    sharpe_ratio = ((pnl/starting_balance)-(risk_free_rate_58_days))/volatility if volatility != 0 else np.nan

    average_win = sum_wins / winning_trades if winning_trades > 0 else 0
    average_loss = sum_losses / losing_trades if losing_trades > 0 else 0
    loss_rate = 100 - win_rate
    expectancy = ((win_rate / 100) * average_win) - ((loss_rate / 100) * average_loss)
    pnl_df = pd.DataFrame(pnl_list, columns=['PnL'])

    # Save trades to CSV
    trades_df = pd.DataFrame(trades)

    return sharpe_ratio, expectancy, win_rate, pnl, volatility, max_drawdown, trades_df