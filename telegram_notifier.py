import requests
import logging
import config

API_URL = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"


def _send(chat_id, text):
    resp = requests.post(
        API_URL,
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )
    if resp.status_code != 200:
        logging.error(f"Telegram send failed ({chat_id}): {resp.text}")
    return resp.status_code == 200


def send_new_signal(signal):
    emoji = "🟢" if signal["direction"] == "BUY" else "🔴"

    channel_text = (
        f"{emoji} *{signal['grade']} SETUP — {signal['symbol']} {signal['direction']}*\n\n"
        f"Entry: `{signal['entry']:.2f}`\n"
        f"Stop Loss: `{signal['stop_loss']:.2f}`\n"
        f"TP1: `{signal['tp1']:.2f}`\n"
        f"TP2: `{signal['tp2']:.2f}`\n"
        f"TP3: `{signal['tp3']:.2f}`\n\n"
        f"_Not financial advice. Manage your own risk._"
    )
    _send(config.TELEGRAM_CHANNEL_ID, channel_text)

    conditions_text = "\n".join(f"• {c}" for c in signal["conditions_met"])
    personal_text = (
        f"{emoji} *{signal['grade']} SETUP — {signal['symbol']} {signal['direction']}* "
        f"({signal['score']}/{signal['max_score']})\n\n"
        f"Entry: `{signal['entry']:.2f}`\n"
        f"Stop Loss: `{signal['stop_loss']:.2f}`\n"
        f"TP1: `{signal['tp1']:.2f}`\n"
        f"TP2: `{signal['tp2']:.2f}`\n"
        f"TP3: `{signal['tp3']:.2f}`\n\n"
        f"Conditions met:\n{conditions_text}"
    )
    _send(config.TELEGRAM_PERSONAL_CHAT_ID, personal_text)

def send_trade_update(trade, event, current_price):
    symbol = trade["symbol"]
    direction = trade["direction"]

    if event == "sl_hit":
        if trade["stop_loss"] == trade["entry"]:
            text = (
                f"⚖️ *Stopped at breakeven — Trade closed, no loss* — "
                f"{symbol} {direction} @ entry `{trade['entry']:.2f}`"
            )
        else:
            text = f"🛑 *Stop loss hit — trade closed* — {symbol} {direction} @ `{current_price:.2f}`"
    else:
        messages = {
            "tp1_hit": f"🎯 *TP1 hit* — {symbol} {direction} @ `{current_price:.2f}`",
            "tp2_hit": f"🎯 *TP2 hit* — {symbol} {direction} @ `{current_price:.2f}`\nStop moved to breakeven.",
            "tp3_hit": f"✅ *TP3 hit — trade closed* — {symbol} {direction} @ `{current_price:.2f}`\nFull target reached.",
        }
        text = messages.get(event, f"Update on {symbol} {direction}: {event}")

    _send(config.TELEGRAM_CHANNEL_ID, text)
    _send(config.TELEGRAM_PERSONAL_CHAT_ID, text)
