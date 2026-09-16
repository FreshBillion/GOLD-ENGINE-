import ccxt
import pandas as pd
import config


def get_exchange():
    exchange_class = getattr(ccxt, config.EXCHANGE_ID)
    return exchange_class()


def fetch_ohlcv(exchange, symbol, timeframe, limit=config.CANDLE_LIMIT):
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def fetch_last_price(exchange, symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]
