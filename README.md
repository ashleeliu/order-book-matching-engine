# Limit Order Book Matching Engine

A Python implementation of a limit order book with price-time priority matching,
plus a simulation framework to analyze market behavior under random order flow.

## Features

- **Price-time priority matching**: orders are matched by best price first, then
  earliest timestamp (standard exchange matching logic)
- **Limit and market orders**: market orders execute immediately against the best
  available price(s); unfilled remainders of limit orders rest on the book
- **Order cancellation**: lazy deletion for O(log n) amortized cancel
- **Heap-based book**: bids/asks stored as heaps (`heapq`) for O(log n) insertion
  and best-price lookup, rather than re-sorting a list on every order
- **Order flow simulation**: generates random buy/sell limit and market orders and
  analyzes resulting spread behavior, trade volume, and price path

## Files

- `order_book.py` — core `OrderBook` class and matching engine
- `simulate.py` — runs a 10,000-order random simulation and prints summary stats
- `plot_results.py` — plots mid-price path and bid-ask spread over the simulation

## Usage

```bash
python order_book.py      # smoke test / example usage
python simulate.py        # run simulation, print stats, save simulation_output.json
python plot_results.py    # generate simulation_results.png from saved output
```

## Example output

```
Total orders processed: 10000
Total trades executed:  8683

Spread statistics:
  mean:   0.0881
  median: 0.0700
  stdev:  0.0699
  min:    0.0100
  max:    0.4300

Trade size statistics:
  mean quantity: 36.5
  total volume:  316590
```

## Design notes

- Trade price is set by the **resting** order's price (the order already on the
  book), which is standard behavior — the incoming order "takes" liquidity at the
  price the resting order was willing to trade at.
- Market orders are treated as IOC (immediate-or-cancel): any unfilled quantity
  is dropped rather than resting on the book, matching typical market order
  semantics on real exchanges.
- Cancellations are lazy: a cancelled order is marked in a set and skipped over
  when encountered at the top of a heap, avoiding an O(n) heap rebuild on every
  cancel.
