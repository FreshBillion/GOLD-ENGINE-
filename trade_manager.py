import json
import os
from datetime import datetime, timezone
import config


def load_trades():
    if not os.path.exists(config.TRADES_FILE):
        return []
    with open(config.TRADES_FILE, "r") as f:
        return json.load(f)


def save_trades(trades):
    with open(config.TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=2)


def get_open_trades():
    return [t for t in load_trades() if t["status"] == "open"]


def has_recent_open_or_recent_trade(symbol, direction):
    trades = [t for t in load_trades() if t["symbol"] == symbol and t["direction"] == direction]
    if not trades:
        return False
    last = trades[-1]
    if last["status"] == "open":
        return True
    opened_at = datetime.fromisoformat(last["opened_at"])
    minutes_since = (datetime.now(timezone.utc) - opened_at).total_seconds() / 60
    return minutes_since < config.COOLDOWN_MINUTES


def add_trade(signal):
    trades = load_trades()
    signal["id"] = len(trades) + 1
    trades.append(signal)
    save_trades(trades)
    return signal["id"]


def update_trade(trade_id, **fields):
    trades = load_trades()
    for t in trades:
        if t["id"] == trade_id:
            t.update(fields)
    save_trades(trades)


def close_trade(trade_id, reason):
    update_trade(trade_id, status=f"closed:{reason}", closed_at=datetime.now(timezone.utc).isoformat())


def check_trade_against_price(trade, current_price):
    """Returns a list of events: 'tp1_hit', 'tp2_hit', 'tp3_hit', or 'sl_hit'."""
    events = []
    is_buy = trade["direction"] == "BUY"

    def crossed(level):
        return current_price >= level if is_buy else current_price <= level

    def stop_crossed(level):
        return current_price <= level if is_buy else current_price >= level

    if stop_crossed(trade["stop_loss"]):
        events.append("sl_hit")
        return events

    if not trade["tp1_hit"] and crossed(trade["tp1"]):
        events.append("tp1_hit")
    if not trade["tp2_hit"] and crossed(trade["tp2"]):
        events.append("tp2_hit")
    if not trade["tp3_hit"] and crossed(trade["tp3"]):
        events.append("tp3_hit")

    return events
