import talib
import logging

def calculate_rsi(data, window):
    if len(data) < window or data['Close'].isnull().any():
        logging.warning(f"Insufficient data for RSI calculation. Data length: {len(data)}")
        return None
    return talib.RSI(data['Close'], timeperiod=window)

def calculate_atr(data, window):
    if len(data) < window or data[['High', 'Low', 'Close']].isnull().values.any():
        logging.warning(f"Insufficient data for ATR calculation. Data length: {len(data)}")
        return None
    return talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=window)

def calculate_adx(data, window, ema_window):
    if len(data) < window or data[['High', 'Low', 'Close']].isnull().values.any():
        logging.warning(f"Insufficient data for ADX calculation. Data length: {len(data)}")
        return None, None

    adx = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=window)

    try:
        ema_adx = talib.EMA(adx, timeperiod=ema_window)
    except Exception as e:
        logging.warning(f"Failed to calculate EMA_ADX due to: {e}. Proceeding without EMA_ADX.")
        ema_adx = None

    return adx, ema_adx

def calculate_ema(data, window):
    if len(data) < window or data['Close'].isnull().any():
        logging.warning(f"Insufficient data for EMA calculation. Data length: {len(data)}")
        return None
    return talib.EMA(data['Close'], timeperiod=window)