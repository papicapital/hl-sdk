import os
from decimal import Decimal

from hl import TESTNET, Account, Api

# Get credentials from environment variables
address = os.environ["HL_ADDRESS"]
secret_key = os.environ["HL_SECRET_KEY"]


def analyze_orderbook_depth(levels: list, side_name: str) -> None:
    """Analyze and display order book depth for one side."""
    if not levels:
        print(f"  No {side_name} orders")
        return

    total_size = Decimal("0")
    total_value = Decimal("0")

    print(f"  {side_name} Orders (Top 10):")
    print(f"    {'Price':>12} {'Size':>12} {'Total Size':>12} {'Total Value':>15}")
    print(f"    {'-' * 12} {'-' * 12} {'-' * 12} {'-' * 15}")

    for i, level in enumerate(levels[:10]):
        price = Decimal(level["px"])
        size = Decimal(level["sz"])
        total_size += size
        total_value += price * size

        print(
            f"    ${price:>11.2f} {size:>12.4f} {total_size:>12.4f} ${total_value:>14.2f}"
        )

    print(f"    Total {side_name} Depth: {total_size:.4f} (${total_value:.2f})")


def calculate_spread_metrics(bids: list, asks: list) -> dict:
    """Calculate spread and related metrics."""
    if not bids or not asks:
        return {
            "spread": 0,
            "spread_pct": 0,
            "mid_price": 0,
            "best_bid": 0,
            "best_ask": 0,
        }

    best_bid = Decimal(bids[0]["px"])
    best_ask = Decimal(asks[0]["px"])
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    spread_pct = (spread / mid_price) * 100

    return {
        "spread": spread,
        "spread_pct": spread_pct,
        "mid_price": mid_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
    }


def find_liquidity_at_distance(
    levels: list, reference_price: Decimal, distance_pct: float
) -> dict:
    """Find liquidity within a certain percentage distance from reference price."""
    if not levels:
        return {"total_size": 0, "total_value": 0, "order_count": 0}

    total_size = Decimal("0")
    total_value = Decimal("0")
    order_count = 0

    for level in levels:
        price = Decimal(level["px"])
        size = Decimal(level["sz"])

        # Calculate distance from reference price
        distance = abs(price - reference_price) / reference_price * 100

        if distance <= distance_pct:
            total_size += size
            total_value += price * size
            order_count += 1
        else:
            break  # Orders are sorted by price, so we can stop here

    return {
        "total_size": total_size,
        "total_value": total_value,
        "order_count": order_count,
    }


async def main() -> None:
    # Create account and API client
    account = Account(address=address, secret_key=secret_key)
    api = await Api.create(
        account=account,
        network=TESTNET,  # Using testnet
    )

    # Assets to analyze
    assets = ["BTC", "ETH", "SOL"]

    print("=== Order Book Analysis ===")
    print()

    for asset in assets:
        print(f"📊 {asset} Order Book Analysis")
        print("=" * 40)

        # Get L2 order book
        book_result = await api.info.l2_book(asset=asset)
        if book_result.is_err():
            print(f"Error getting {asset} order book: {book_result.unwrap_err()}")
            continue

        book = book_result.unwrap()
        bids = book.get("levels", [[], []])[0]  # Buy orders
        asks = book.get("levels", [[], []])[1]  # Sell orders

        # Calculate basic metrics
        metrics = calculate_spread_metrics(bids, asks)

        print(f"📈 Market Metrics:")
        print(f"  Mid Price: ${metrics['mid_price']:.2f}")
        print(f"  Best Bid: ${metrics['best_bid']:.2f}")
        print(f"  Best Ask: ${metrics['best_ask']:.2f}")
        print(f"  Spread: ${metrics['spread']:.2f} ({metrics['spread_pct']:.3f}%)")
        print()

        # Analyze order book depth
        print(f"📚 Order Book Depth:")
        analyze_orderbook_depth(bids, "Bid")
        print()
        analyze_orderbook_depth(asks, "Ask")
        print()

        # Liquidity analysis at different distances
        print(f"💧 Liquidity Analysis:")
        distances = [0.1, 0.5, 1.0, 2.0]  # Percentage distances

        for distance in distances:
            bid_liq = find_liquidity_at_distance(bids, metrics["mid_price"], distance)
            ask_liq = find_liquidity_at_distance(asks, metrics["mid_price"], distance)

            print(f"  Within {distance}%:")
            print(
                f"    Bid: {bid_liq['total_size']:.4f} ({bid_liq['order_count']} orders, ${bid_liq['total_value']:.2f})"
            )
            print(
                f"    Ask: {ask_liq['total_size']:.4f} ({ask_liq['order_count']} orders, ${ask_liq['total_value']:.2f})"
            )

            total_liquidity = bid_liq["total_size"] + ask_liq["total_size"]
            imbalance = abs(bid_liq["total_size"] - ask_liq["total_size"]) / max(
                total_liquidity, Decimal("0.0001")
            )
            print(f"    Total: {total_liquidity:.4f}, Imbalance: {imbalance:.1%}")
            print()

        # Market depth analysis
        print(f"🎯 Market Impact Analysis:")
        impact_sizes = [Decimal("0.1"), Decimal("0.5"), Decimal("1.0"), Decimal("5.0")]

        for size in impact_sizes:
            # Calculate impact for buying
            buy_cost = Decimal("0")
            buy_size_remaining = size
            buy_levels_used = 0

            for level in asks:
                if buy_size_remaining <= 0:
                    break

                price = Decimal(level["px"])
                available = Decimal(level["sz"])
                take_size = min(buy_size_remaining, available)

                buy_cost += price * take_size
                buy_size_remaining -= take_size
                buy_levels_used += 1

            # Calculate impact for selling
            sell_value = Decimal("0")
            sell_size_remaining = size
            sell_levels_used = 0

            for level in bids:
                if sell_size_remaining <= 0:
                    break

                price = Decimal(level["px"])
                available = Decimal(level["sz"])
                take_size = min(sell_size_remaining, available)

                sell_value += price * take_size
                sell_size_remaining -= take_size
                sell_levels_used += 1

            if buy_size_remaining == 0 and sell_size_remaining == 0:
                buy_avg_price = buy_cost / size
                sell_avg_price = sell_value / size

                buy_impact = (
                    (buy_avg_price - metrics["mid_price"]) / metrics["mid_price"]
                ) * 100
                sell_impact = (
                    (metrics["mid_price"] - sell_avg_price) / metrics["mid_price"]
                ) * 100

                print(f"  {size} {asset} trade:")
                print(
                    f"    Buy: ${buy_avg_price:.2f} avg ({buy_impact:+.2f}% impact, {buy_levels_used} levels)"
                )
                print(
                    f"    Sell: ${sell_avg_price:.2f} avg ({sell_impact:+.2f}% impact, {sell_levels_used} levels)"
                )
            else:
                print(f"  {size} {asset} trade: Insufficient liquidity")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
