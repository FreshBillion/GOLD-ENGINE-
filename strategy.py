"""
Grading:
  The higher-timeframe trend filter (EMA50 vs EMA200 on 4H) is a hard gate,
  separate from the 5-point score. If price/EMA alignment doesn't confirm a
  clear trend, nothing is generated at all.

  The remaining 5 independent confluence checks are scored 0-5:
    5/5 -> A+
    4/5 -> A
    3/5 -> B
    2/5 -> C
    <2  -> no signal (skipped)
"""

from datetime import datetime, timezone
import config
from data_fetcher import fetch_ohlcv
from indicators import ema, rsi, macd, atr, bollinger


def grade_from_score(score):
    if score >= 5:
        return "A+"
    elif score == 4:
        return "A"
    elif score == 3:
        return "B"
    elif score == 2:
        return "C"
    return None


def evaluate(exchange, symbol=config.SYMBOL):
    trend_df = fetch_ohlcv(exchange, symbol, config.TREND_TIMEFRAME)
    entry_df = fetch_ohlcv(exchange, symbol, config.ENTRY_TIMEFRAME)

    trend_df["ema50"] = ema(trend_df["close"], 50)
    trend_df["ema200"] = ema(trend_df["close"], 200)
    last_trend = trend_df.iloc[-1]

    if last_trend["close"] > last_trend["ema50"] > last_trend["ema200"]:
        bias = "BUY"
    elif last_trend["close"] < last_trend["ema50"] < last_trend["ema200"]:
        bias = "SELL"
    else:
        return None  # trend gate failed

    entry_df["rsi"] = rsi(entry_df["close"])
    entry_df["macd"], entry_df["macd_signal"] = macd(entry_df["close"])
    entry_df["atr"] = atr(entry_df)
    entry_df["atr_avg"] = entry_df["atr"].rolling(50).mean()
    entry_df["vol_avg"] = entry_df["volume"].rolling(20).mean()
    entry_df["bb_upper"], entry_df["bb_lower"] = bollinger(entry_df["close"])

    last = entry_df.iloc[-1]
    prev = entry_df.iloc[-2]

    score = 0
    conditions_met = []

    if bias == "BUY":
        if prev["rsi"] < 40 <= last["rsi"]:
            score += 1; conditions_met.append("RSI reclaiming 40 from oversold")
        if prev["macd"] < prev["macd_signal"] and last["macd"] >= last["macd_signal"]:
            score += 1; conditions_met.append("MACD bullish cross")
        if last["atr"] > last["atr_avg"]:
            score += 1; conditions_met.append("Volatility expanding (ATR > average)")
        if last["volume"] > last["vol_avg"]:
            score += 1; conditions_met.append("Volume above average")
        if last["close"] > last["bb_upper"] or (prev["close"] <= prev["bb_upper"] < last["close"]):
            score += 1; conditions_met.append("Breaking upper Bollinger band")
    else:
        if prev["rsi"] > 60 >= last["rsi"]:
            score += 1; conditions_met.append("RSI losing 60 from overbought")
        if prev["macd"] > prev["macd_signal"] and last["macd"] <= last["macd_signal"]:
            score += 1; conditions_met.append("MACD bearish cross")
        if last["atr"] > last["atr_avg"]:
            score += 1; conditions_met.append("Volatility expanding (ATR > average)")
        if last["volume"] > last["vol_avg"]:
            score += 1; conditions_met.append("Volume above average")
        if last["close"] < last["bb_lower"] or (prev["close"] >= prev["bb_lower"] > last["close"]):
            score += 1; conditions_met.append("Breaking lower Bollinger band")

    if score < config.MIN_SCORE_TO_SEND:
        return None

    grade = grade_from_score(score)
    entry_price = float(last["close"])
    stop_distance = float(last["atr"]) * config.ATR_STOP_MULTIPLIER

    if bias == "BUY":
        stop_loss = entry_price - stop_distance
        tp1, tp2, tp3 = [entry_price + stop_distance * r for r in config.TP_R_MULTIPLES]
    else:
        stop_loss = entry_price + stop_distance
        tp1, tp2, tp3 = [entry_price - stop_distance * r for r in config.TP_R_MULTIPLES]

    return {
        "symbol": symbol,
        "direction": bias,
        "grade": grade,
        "score": score,
        "max_score": 5,
        "conditions_met": conditions_met,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "tp1": tp1, "tp2": tp2, "tp3": tp3,
        "tp1_hit": False, "tp2_hit": False, "tp3_hit": False,
        "status": "open",
        "opened_at": datetime.now(timezone.utc).isoformat(),
      }
