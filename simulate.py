"""
Order Flow Simulation: Generates stream of random limit/market orders (Poisson arrival process)
and feeds them into the OrderBook to analyze:
  - bid-ask spread behavior over time
  - fill-time distribution for limit orders
  - trade volume / price path
"""

import random
import statistics
from order_book import OrderBook, Side, OrderType

random.seed(42)


def run_simulation(n_orders: int = 10_000, mid_price: float = 100.0):
    book = OrderBook()

    spread_history = []
    mid_price_history = []

    current_mid = mid_price

    for i in range(n_orders):
        # 70% limit orders, 30% market orders (rough retail/market-maker mix)
        is_market = random.random() < 0.3
        side = Side.BUY if random.random() < 0.5 else Side.SELL

        if is_market:
            qty = random.choice([10, 20, 50, 100])
            book.submit_market_order(side, qty)
        else:
            # limit price drawn near the current mid, with some orders
            # placed inside the spread and some further out
            offset = random.gauss(0, 0.15)
            price = round(current_mid + offset if side == Side.BUY else current_mid - offset, 2)
            qty = random.choice([10, 20, 50, 100, 200])
            book.submit_limit_order(side, price, qty)

        bid, ask = book.best_bid(), book.best_ask()
        if bid is not None and ask is not None:
            current_mid = (bid + ask) / 2
            spread_history.append(ask - bid)
            mid_price_history.append(current_mid)

    return book, spread_history, mid_price_history


def summarize(book, spread_history, mid_price_history):
    print(f"Total orders processed: {book.total_orders_submitted}")
    print(f"Total trades executed:  {len(book.trade_log)}")
    print()

    if spread_history:
        print("Spread statistics:")
        print(f"  mean:   {statistics.mean(spread_history):.4f}")
        print(f"  median: {statistics.median(spread_history):.4f}")
        print(f"  stdev:  {statistics.stdev(spread_history):.4f}")
        print(f"  min:    {min(spread_history):.4f}")
        print(f"  max:    {max(spread_history):.4f}")
        print()

    if book.trade_log:
        trade_qtys = [t.quantity for t in book.trade_log]
        print("Trade size statistics:")
        print(f"  mean quantity: {statistics.mean(trade_qtys):.1f}")
        print(f"  total volume:  {sum(trade_qtys)}")
        print()

    print("Final depth snapshot (top 5 levels):")
    depth = book.depth_snapshot(levels=5)
    print("  Bids:", depth["bids"])
    print("  Asks:", depth["asks"])


if __name__ == "__main__":
    book, spreads, mids = run_simulation(n_orders=10_000)
    summarize(book, spreads, mids)

    #Save for plotting
    import json
    with open("simulation_output.json", "w") as f:
        json.dump({"spread_history": spreads, "mid_price_history": mids}, f)
    print("\nSaved simulation_output.json for plotting.")
