# Limit Order Book Matching Engine

I built a limit order book matching engine that replicates the core mechanics of how exchanges match buy and sell orders. The engine implements price-time priority matching and supports both limit and market orders. I simulated thousands of randomly generated orders arriving via a Poisson process to study how bid-ask spread and trade volume behave under continuous order flow.

## What It Does

Matches incoming buy and sell orders against the book using price-time priority Supports limit orders (rest on the book if unfilled) and market orders (execute immediately or cancel). Handles order cancellation and partial fills as orders are matched. Uses heap-based priority queues so best-price lookups and order insertion run in O(log n). Simulates random order flow and analyzes resulting spread and volume behavior

## Modeling Approach

The book is maintained as two heaps — a max-heap of bids and a min-heap of asks — ordered by price first and timestamp second, so the best-priced, earliest order is always matched first. An incoming order is matched against the opposite side of the book while its price crosses the best available price; any unfilled limit quantity rests on the book, while unfilled market order quantity is dropped (immediate-or-cancel), mirroring how market orders behave on real exchanges. Order flow in the simulation is generated as a Poisson arrival process, with each order randomly assigned a side, order type, and price offset from the current mid-price.

## Results

10,000-order simulation:
- 10,000 orders processed (limit and market, roughly 70/30 split)
- 8,683 trades executed
- 316,590+ total shares traded
- Mean bid-ask spread: $0.09 (median $0.07, stdev $0.07)
- Spread range: $0.01 – $0.43

Smoke test (4 resting orders + 1 crossing order):
- Best bid/ask correctly identified before the crossing order arrives
- Crossing buy order correctly matched against both resting asks in price priority, generating 2 trades
- Remaining book depth accurately reflects unfilled quantity after matching

## Tools

- Python
- heapq (priority queue implementation)
- Matplotlib
