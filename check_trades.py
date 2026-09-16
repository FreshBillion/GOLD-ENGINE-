import logging
import trade_manager
import telegram_notifier
import config
from data_fetcher import get_exchange, fetch_last_price

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    exchange = get_exchange()
    open_trades = trade_manager.get_open_trades()

    if not open_trades:
        logging.info("No open trades.")
        return

    current_price = fetch_last_price(exchange, config.SYMBOL)

    for trade in open_trades:
        events = trade_manager.check_trade_against_price(trade, current_price)

        for event in events:
            if event == "tp1_hit":
                trade_manager.update_trade(trade["id"], tp1_hit=True)
                # notify only — stop stays where it is

            elif event == "tp2_hit":
                trade_manager.update_trade(trade["id"], tp2_hit=True, stop_loss=trade["entry"])
                # stop moved to breakeven

            elif event == "tp3_hit":
                trade_manager.update_trade(trade["id"], tp3_hit=True)
                trade_manager.close_trade(trade["id"], "tp3")

            elif event == "sl_hit":
                trade_manager.close_trade(trade["id"], "sl")

            telegram_notifier.send_trade_update(trade, event, current_price)
            logging.info(f"Trade {trade['id']}: {event} @ {current_price}")


if __name__ == "__main__":
    main()
