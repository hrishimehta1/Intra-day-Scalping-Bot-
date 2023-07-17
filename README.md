# Crypto Trading Bot

The Crypto Trading Bot is an automated trading solution for the cryptocurrency market. It utilizes technical indicators and trading strategies to identify potential trading opportunities and execute trades on the Binance exchange.

## Installation

1. Clone the repository:
git clone https://github.com/your-username/crypto-trading-bot.git


2. Install the required dependencies:
pip install -r requirements.txt


3. Set up your Binance API credentials:

- Create a Binance account if you don't have one.
- Generate API keys with the necessary permissions.
- Update the `api_key` and `api_secret` variables in the `main.py` file with your API credentials.

## Usage

1. Configure the trading parameters:

- Open the `main.py` file and specify the trading symbol (e.g., BTCUSDT) in the `symbol` variable.
- Customize the trading strategy by modifying the indicators, timeframes, and risk management parameters.

2. Run the bot:
python main.py

3. Monitor the bot's output:

- The bot will provide real-time updates on executed trades, market conditions, and any error messages encountered.

## Code Explanation

The code consists of the following files:

- `main.py`: The entry point of the bot that initializes the Binance client, configures the trading strategy, and executes the trading logic.
    - `get_hourly_dataframe()`: Retrieves historical data from Binance and converts it into a DataFrame for further analysis.
    - `calculate_stop_loss(df, atr_period, multiplier)`: Calculates the stop-loss levels based on the Average True Range (ATR) indicator.
    - `calculate_factors(df)`: Calculates additional factors for adjusting the stop loss based on market data and indicators such as liquidity, volume, and trend analysis.
    - `plot_graph(df)`: Plots the price chart with buy/sell signals and stop-loss levels.
    - `calculate_rsi(df, period)`: Calculates the Relative Strength Index (RSI) indicator.
    - `calculate_macd(df, short_period, long_period, signal_period)`: Calculates the Moving Average Convergence Divergence (MACD) indicator.
    - `check_liquidity(symbol, timeframe, num_candles)`: Checks the liquidity metrics and presence of liquidity sweeps for a given symbol.
    - `check_sell_factors(df, index)`: Checks the sell conditions based on price, moving averages, RSI, MACD, and histogram.
    - `check_buy_factors(df, index)`: Checks the buy conditions based on price, moving averages, RSI, MACD, volume, candlestick patterns, and Bollinger Bands.
    - `buy_or_sell(buy_sell_list, df)`: Executes buy or sell orders based on the signals and additional factors.
    - `sma_trade_logic()`: Implements the trading logic based on the Simple Moving Average (SMA) strategy.

- `indicators.py`: Contains functions to calculate technical indicators such as moving averages, RSI, MACD, and more.

- `utils.py`: Includes utility functions for data preprocessing, plotting, and risk management calculations.

- `config.py`: Defines configurable parameters such as API credentials, trading symbol, timeframes, and risk management settings.

## Contributing

Contributions to the Crypto Trading Bot project are welcome! If you encounter any bugs, have feature requests, or would like to contribute enhancements, feel free to open an issue or submit a pull request.

## Disclaimer

Trading cryptocurrencies carries a risk of financial loss. The Crypto Trading Bot is provided for educational and informational purposes only. The developers and maintainers of this project are not responsible for any financial losses incurred while using the bot. Use it at your own risk.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

