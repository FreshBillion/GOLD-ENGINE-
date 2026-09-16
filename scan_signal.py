import logging
import strategy
import trade_manager
import telegram_notifier
import config
from data_fetcher import get_exchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    exchange = get_exchange()
    signal = strategy.evaluate(exchange, config.SYMBOL)

    if signal is None:
        logging.info("No qualifying setup this run.")
        return

    if trade_manager.has_recent_open_or_recent_trade(signal["symbol"], signal["direction"]):
        logging.info("Signal found but blocked — open trade or still in cooldown.")
        return

    trade_id = trade_manager.add_trade(signal)
    telegram_notifier.send_new_signal(signal)
    logging.info(f"New {signal['grade']} {signal['direction']} signal saved as trade {trade_id}")


if __name__ == "__main__":
    main()
