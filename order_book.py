import heapq
import itertools
from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass
class Order:
    order_id: int
    side: Side
    order_type: OrderType
    price: float  # ignored for market orders
    quantity: int
    timestamp: int  # used to break ties at the same price (lower = earlier)


@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: float
    quantity: int
    timestamp: int


@dataclass(order=True)
class _BookEntry:
    sort_key: tuple = field(compare=True)
    order: Order = field(compare=False)


class OrderBook:
    def __init__(self):
        # Bids: max-heap on price -> store negative price so heapq (min-heap) acts as max-heap
        self._bids: list[_BookEntry] = []
        # Asks: min-heap on price
        self._asks: list[_BookEntry] = []

        self._order_lookup: dict[int, Order] = {}
        self._cancelled_ids: set[int] = set()

        self.trade_log: list[Trade] = []
        self._clock = itertools.count()  # monotonically increasing timestamp
        self._next_order_id = itertools.count(1)
        self.total_orders_submitted = 0

    # public api
    def submit_limit_order(self, side: Side, price: float, quantity: int) -> int:
        order_id = next(self._next_order_id)
        order = Order(
            order_id=order_id,
            side=side,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
            timestamp=next(self._clock),
        )
        self._process_order(order)
        return order_id

    def submit_market_order(self, side: Side, quantity: int) -> int:
        order_id = next(self._next_order_id)
        order = Order(
            order_id=order_id,
            side=side,
            order_type=OrderType.MARKET,
            price=float("inf") if side == Side.BUY else float("-inf"),
            quantity=quantity,
            timestamp=next(self._clock),
        )
        self._process_order(order)
        return order_id

    def cancel_order(self, order_id: int) -> bool:
        #mark as cancelled, actually removed when popped from heap
        if order_id in self._order_lookup:
            self._cancelled_ids.add(order_id)
            del self._order_lookup[order_id]
            return True
        return False

    def best_bid(self) -> float | None:
        self._clean(self._bids)
        return -self._bids[0].sort_key[0] if self._bids else None

    def best_ask(self) -> float | None:
        self._clean(self._asks)
        return self._asks[0].sort_key[0] if self._asks else None

    def spread(self) -> float | None:
        bid, ask = self.best_bid(), self.best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid

    def depth_snapshot(self, levels: int = 5) -> dict:
        """Return top N price levels on each side with aggregated quantity."""
        return {
            "bids": self._aggregate_levels(self._bids, is_bid=True, levels=levels),
            "asks": self._aggregate_levels(self._asks, is_bid=False, levels=levels),
        }

    # Internal matching logic
    def _process_order(self, order: Order):
        self.total_orders_submitted += 1
        book = self._asks if order.side == Side.BUY else self._bids

        while order.quantity > 0 and book:
            self._clean(book)
            if not book:
                break

            best = book[0].order
            crosses = self._crosses(order, best)
            if not crosses:
                break

            trade_qty = min(order.quantity, best.quantity)
            trade_price = best.price  # resting order sets the trade price

            self.trade_log.append(
                Trade(
                    buy_order_id=order.order_id if order.side == Side.BUY else best.order_id,
                    sell_order_id=best.order_id if order.side == Side.BUY else order.order_id,
                    price=trade_price,
                    quantity=trade_qty,
                    timestamp=next(self._clock),
                )
            )

            order.quantity -= trade_qty
            best.quantity -= trade_qty

            if best.quantity == 0:
                heapq.heappop(book)
                self._order_lookup.pop(best.order_id, None)

        # Resting remainder (limit orders only; market orders that can't
        # fully filled are simply dropped
        if order.quantity > 0 and order.order_type == OrderType.LIMIT:
            self._add_to_book(order)

    def _crosses(self, incoming: Order, resting: Order) -> bool:
        if incoming.order_type == OrderType.MARKET:
            return True
        if incoming.side == Side.BUY:
            return incoming.price >= resting.price
        else:
            return incoming.price <= resting.price

    def _add_to_book(self, order: Order):
        self._order_lookup[order.order_id] = order
        if order.side == Side.BUY:
            entry = _BookEntry(sort_key=(-order.price, order.timestamp), order=order)
            heapq.heappush(self._bids, entry)
        else:
            entry = _BookEntry(sort_key=(order.price, order.timestamp), order=order)
            heapq.heappush(self._asks, entry)

    def _clean(self, book: list[_BookEntry]):
        #Pop cancelled or fully-filled orders sitting at the top of the heap
        while book and (
            book[0].order.order_id in self._cancelled_ids or book[0].order.quantity == 0
        ):
            heapq.heappop(book)

    def _aggregate_levels(self, book: list[_BookEntry], is_bid: bool, levels: int):
        self._clean(book)
        # heap isn't fully sorted beyond the root, so sort a copy for display purposes
        entries = sorted(
            (e for e in book if e.order.order_id not in self._cancelled_ids and e.order.quantity > 0),
            key=lambda e: e.sort_key,
        )
        agg: dict[float, int] = {}
        for e in entries:
            agg[e.order.price] = agg.get(e.order.price, 0) + e.order.quantity
        items = sorted(agg.items(), key=lambda x: x[0], reverse=is_bid)
        return items[:levels]


if __name__ == "__main__":
    #test
    book = OrderBook()
    book.submit_limit_order(Side.BUY, price=99.5, quantity=100)
    book.submit_limit_order(Side.BUY, price=99.0, quantity=200)
    book.submit_limit_order(Side.SELL, price=100.5, quantity=150)
    book.submit_limit_order(Side.SELL, price=100.0, quantity=50)

    print("Best bid:", book.best_bid())
    print("Best ask:", book.best_ask())
    print("Spread:", book.spread())

    # This crosses the book and should generate trades
    book.submit_limit_order(Side.BUY, price=100.5, quantity=180)

    print("\nTrades executed:")
    for t in book.trade_log:
        print(t)

    print("\nDepth snapshot:", book.depth_snapshot())
