import requests
import pandas as pd
import config

BASE_URL = "https://api.twelvedata.com"


def get_exchange():
    # Kept only so scan_signal.py / check_trades.py don't need changes.
    # Twelve Data is plain REST, no client object needed.
    return None


def fetch_ohlcv(exchange, symbol, timeframe, limit=config.CANDLE_LIMIT):
    resp = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": symbol,
            "interval": timeframe,
            "outputsize": limit,
            "apikey": config.TWELVE_DATA_API_KEY,
        },
        timeout=15,
    )
    data = resp.json()
    if "values" not in data:
        raise RuntimeError(f"Twelve Data error: {data}")

    df = pd.DataFrame(data["values"]).rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["volume"].astype(float) if "volume" in df.columns else 0.0
    return df.sort_values("timestamp").reset_index(drop=True)


def fetch_last_price(exchange, symbol):
    resp = requests.get(
        f"{BASE_URL}/price",
        params={"symbol": symbol, "apikey": config.TWELVE_DATA_API_KEY},
        timeout=15,
    )
    return float(resp.json()["price"])
