import os 
from binance.client import Client
from binance import ThreadedWebsocketManager 
import pprint
import datetime      
import pandas as pd     
import numpy as np
import matplotlib.pyplot as plt
import talib   

def get_hourly_dataframe():
    # Retrieve historical data
    start_time = '1 week ago UTC'
    interval = '1h'
    bars = client.get_historical_klines(symbol, interval, start_time)

    # Parse the data into a DataFrame
    df = df.astype(float)
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    df.set_index('date', inplace=True)
    
    return df

def calculate_stop_loss(df, atr_period=14, multiplier=3.0):
    # Calculate Average True Range (ATR)
    df['HighLow'] = df['high'] - df['low']
    df['HighClose'] = np.abs(df['high'] - df['close'].shift())
    df['LowClose'] = np.abs(df['low'] - df['close'].shift())
    df['TR'] = df[['HighLow', 'HighClose', 'LowClose']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=atr_period).mean()

    # Calculate the Chandelier Exit long and short levels
    df['LongExit'] = df['high'].rolling(window=atr_period).max() - (df['ATR'] * multiplier)
    df['ShortExit'] = df['low'].rolling(window=atr_period).min() + (df['ATR'] * multiplier)

    # Adjust stop loss based on additional factors (e.g., liquidity, volume, trend analysis, etc.)
    df['AdjustedStopLoss'] = df['LongExit'] * (1.0 - df['liquidity_factor'])  # Adjust based on liquidity factor
    df['AdjustedStopLoss'] = df['AdjustedStopLoss'] * (1.0 - df['volume_factor'])  # Adjust based on volume factor
    df['AdjustedStopLoss'] = df['AdjustedStopLoss'] * df['trend_factor']  # Adjust based on trend factor

    # Remove unnecessary columns
    df.drop(['HighLow', 'HighClose', 'LowClose', 'TR'], axis=1, inplace=True)

    return df


def calculate_factors(df):
    '''
    I've used the bid-ask spread to calculate the liquidity factor. A tighter spread indicates higher liquidity. 
    The volume factor is calculated by dividing the trading volume for each period by the sum of the total volume. This provides a proportionate weight based on volume. 
    The trend factor is calculated using the Relative Strength Index (RSI), where values above 50 indicate bullishness and values below 50 indicate bearishness.
    '''
    # Calculate additional factors for adjusting stop loss based on market data and indicators
    
    # Calculate liquidity factor based on bid-ask spread
    df['spread'] = df['high'] - df['low']
    df['liquidity_factor'] = 1 - (df['spread'] / df['close'])
    
    # Calculate volume factor based on trading volume
    df['volume_factor'] = df['volume'] / df['volume'].sum()
    
    # Calculate trend factor based on a technical indicator such as the Relative Strength Index (RSI)
    rsi_period = 14
    df['rsi'] = talib.RSI(df['close'], timeperiod=rsi_period)
    df['trend_factor'] = np.where(df['rsi'] > 50, df['rsi'] / 100, 1 - (df['rsi'] / 100))
    
    # Remove intermediate columns
    df.drop(['spread', 'rsi'], axis=1, inplace=True)
    
    return df


def plot_graph(df):
    df[['close', 'stop_loss']].plot()

    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Price', fontsize=18)
    plt.scatter(df.index, df['Buy'], color='purple', label='Buy', marker='^', alpha=1)
    plt.scatter(df.index, df['Sell'], color='red', label='Sell', marker='v', alpha=1)
    plt.scatter(df.index, df['stop_loss'], color='orange', label='Stop Loss', marker='x', alpha=1)
    plt.legend()
    plt.show()


def calculate_rsi(df, period=14):
    close_prices = df['close']
    price_changes = close_prices.diff()

    # Calculate the average gain and average loss
    gains = price_changes.where(price_changes > 0, 0)
    losses = -price_changes.where(price_changes < 0, 0)

    avg_gain = gains.rolling(period).mean()
    avg_loss = losses.rolling(period).mean()

    # Calculate the relative strength (RS) and the relative strength index (RSI)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_macd(df, short_period=12, long_period=26, signal_period=9):
    close_prices = df['close']
    ema_short = close_prices.ewm(span=short_period, adjust=False).mean()
    ema_long = close_prices.ewm(span=long_period, adjust=False).mean()

    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram

def check_liquidity(symbol, timeframe='1m', num_candles=10):
    # Retrieve recent historical data
    historical_data = client.get_historical_klines(symbol=symbol, interval=timeframe, limit=num_candles)
    df = pd.DataFrame(historical_data, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time',
                                                'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Asset Volume',
                                                'Taker Buy Quote Asset Volume', 'Ignore'])

    # Calculate liquidity metrics
    average_volume = df['Volume'].astype(float).mean()
    last_volume = float(df.iloc[-1]['Volume'])
    volume_change = last_volume - average_volume

    taker_buy_volume = df['Taker Buy Base Asset Volume'].astype(float).sum()
    taker_buy_quote_volume = df['Taker Buy Quote Asset Volume'].astype(float).sum()
    taker_buy_ratio = taker_buy_volume / taker_buy_quote_volume

    # Check for liquidity sweeps
    liquidity_sweep = False
    if last_volume > average_volume and taker_buy_ratio > 0.5:
        liquidity_sweep = True

    return {
        'average_volume': average_volume,
        'last_volume': last_volume,
        'volume_change': volume_change,
        'taker_buy_ratio': taker_buy_ratio,
        'liquidity_sweep': liquidity_sweep
    }


def check_sell_factors(df, index):
    close_price = df['close'].iloc[index]
    sma_5 = df['5sma'].iloc[index]
    sma_15 = df['15sma'].iloc[index]
    rsi = calculate_rsi(df.iloc[:index+1])
    macd, signal, histogram = calculate_macd(df.iloc[:index+1])

    if close_price < sma_5 and sma_5 < sma_15 and rsi.iloc[-1] > 70 and macd.iloc[-1] < signal.iloc[-1] and histogram.iloc[-1] < 0:
        return True
    else:
        return False
    
def check_buy_factors(df, index):
    close_price = df['close'].iloc[index]
    sma_5 = df['5sma'].iloc[index]
    sma_15 = df['15sma'].iloc[index]
    rsi = calculate_rsi(df.iloc[:index+1])
    macd, signal, histogram = calculate_macd(df.iloc[:index+1])
    volume = df['volume'].iloc[index]

    # Additional factors to consider
    bullish_candle = df['close'].iloc[index] > df['open'].iloc[index]
    above_bollinger_band = close_price > df['upper_band'].iloc[index]
    volume_above_average = volume > df['volume_ma'].iloc[index]

    if close_price > sma_5 and sma_5 > sma_15 and rsi.iloc[-1] < 30 and macd.iloc[-1] > signal.iloc[-1] and histogram.iloc[-1] > 0 and bullish_candle and above_bollinger_band and volume_above_average:
        return True
    else:
        return False


def buy_or_sell(buy_sell_list, df):
    for index, value in enumerate(buy_sell_list):
        current_price = client.get_symbol_ticker(symbol=symbol)
        print(current_price['price'])  # Output is in json format, only price needs to be accessed
        
        if value == 1.0:  # Signal to buy
            if current_price['price'] < df['Buy'][index] and check_buy_factors(df, index):
                # Check additional factors for buy decision
                if check_buy_factors(df, index):
                    stop_loss = df['AdjustedStopLoss'][index]
                    risk = current_price['price'] - stop_loss
                    print("Buy order conditions met. Placing buy order...")
                    print(f"Coin: {symbol}")
                    print(f"Position: LONG")
                    print(f"Stop Loss: {stop_loss}")
                    print(f"Risk: {risk}")
                    print(f"Risk Amount: {risk * quantity}")
                    buy_order = client.order_market_buy(symbol=symbol, quantity=quantity)
                    print(buy_order)
        elif value == -1.0:  # Signal to sell
            if current_price['price'] > df['Sell'][index] and check_sell_factors(df, index):
                # Check additional factors for sell decision
                if check_sell_factors(df, index):
                    stop_loss = df['AdjustedStopLoss'][index]
                    risk = stop_loss - current_price['price']
                    print("Sell order conditions met. Placing sell order...")
                    print(f"Coin: {symbol}")
                    print(f"Position: SHORT")
                    print(f"Stop Loss: {stop_loss}")
                    print(f"Risk: {risk}")
                    print(f"Risk Amount: {risk * quantity}")
                    sell_order = client.order_market_sell(symbol=symbol, quantity=quantity)
                    print(sell_order)
        else:
            print("No action required.")



def sma_trade_logic():
    symbol_df = get_hourly_dataframe()
    symbol_df = calculate_factors(symbol_df)
    symbol_df = calculate_stop_loss(symbol_df)

    symbol_df['5sma'] = symbol_df['close'].rolling(5).mean()
    symbol_df['15sma'] = symbol_df['close'].rolling(15).mean()

    # Calculate RSI
    symbol_df['rsi'] = calculate_rsi(symbol_df)

    # Calculate MACD
    symbol_df['macd'], symbol_df['signal'], symbol_df['histogram'] = calculate_macd(symbol_df)

    symbol_df['Signal'] = np.where(symbol_df['5sma'] > symbol_df['15sma'], 1, 0)
    symbol_df['Position'] = symbol_df['Signal'].diff()

    symbol_df['Buy'] = np.where(symbol_df['Position'] == 1, symbol_df['close'], np.NaN)
    symbol_df['Sell'] = np.where(symbol_df['Position'] == -1, symbol_df['close'], np.NaN)

    # Plot the graph
    plot_graph(symbol_df)

    with open('output.txt', 'w') as f:
        f.write(symbol_df.to_string())

    buy_sell_list = symbol_df['Position'].tolist()
    buy_or_sell(buy_sell_list, symbol_df)


def main():
    sma_trade_logic()

if __name__ == "__main__":
    api_key = 'YOUR BINANCE API KEY HERE '
    api_secret = 'YOUR BINANCE API PASSWORD HERE '
    client = Client(api_key, api_secret, testnet=True)
    print("Using Binance TestNet Server")
    pprint.pprint(client.get_account())
    symbol = ''
    main()



