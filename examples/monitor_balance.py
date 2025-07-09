import os
from decimal import Decimal

from hl import TESTNET, Account, Api

# Get credentials from environment variables
address = os.environ["HL_ADDRESS"]
secret_key = os.environ["HL_SECRET_KEY"]


async def main() -> None:
    # Create account and API client
    account = Account(address=address, secret_key=secret_key)
    api = await Api.create(
        account=account,
        network=TESTNET,  # Using testnet
    )

    print("=== Account Balance Monitoring ===")
    print(f"Address: {address}")
    print()

    # Get perpetual account state
    perp_result = await api.info.user_state()
    if perp_result.is_ok():
        perp_state = perp_result.unwrap()

        print("📊 Perpetual Account:")
        print(
            f"  Total Value: ${perp_state.get('marginSummary', {}).get('accountValue', 'N/A')}"
        )
        print(f"  Withdrawable: ${perp_state.get('withdrawable', 'N/A')}")
        print(
            f"  Cross Margin Used: ${perp_state.get('crossMarginSummary', {}).get('totalMarginUsed', 'N/A')}"
        )
        print(
            f"  Cross Maintenance Margin: ${perp_state.get('crossMarginSummary', {}).get('totalNtlPos', 'N/A')}"
        )

        # Show positions
        positions = perp_state.get("assetPositions", [])
        if positions:
            print("  Positions:")
            for pos in positions:
                if float(pos.get("position", {}).get("szi", 0)) != 0:
                    asset = pos.get("position", {}).get("coin", "Unknown")
                    size = pos.get("position", {}).get("szi", "0")
                    unrealized_pnl = pos.get("position", {}).get("unrealizedPnl", "0")
                    print(f"    {asset}: {size} (PnL: ${unrealized_pnl})")
        else:
            print("  No open positions")
    else:
        print(f"Error getting perpetual state: {perp_result.unwrap_err()}")

    print()

    # Get spot account state
    spot_result = await api.info.spot_user_state()
    if spot_result.is_ok():
        spot_state = spot_result.unwrap()

        print("💰 Spot Account:")
        total_usd_value = Decimal("0")
        balances = spot_state.get("balances", [])

        if balances:
            print("  Balances:")
            for balance in balances:
                coin = balance.get("coin", "Unknown")
                total = balance.get("total", "0")
                hold = balance.get("hold", "0")
                available = Decimal(total) - Decimal(hold)

                if Decimal(total) > 0:
                    print(f"    {coin}: {total} total, {available} available")

                    # Calculate USD value if possible
                    if coin == "USDC":
                        total_usd_value += Decimal(total)
                    else:
                        # Try to get mid price for conversion
                        mids_result = await api.info.all_mids()
                        if mids_result.is_ok():
                            mids = mids_result.unwrap()
                            if coin in mids:
                                coin_price = Decimal(mids[coin])
                                usd_value = Decimal(total) * coin_price
                                total_usd_value += usd_value
                                print(f"      (≈${usd_value:.2f} @ ${coin_price})")

            print(f"  Total USD Value: ≈${total_usd_value:.2f}")
        else:
            print("  No spot balances")
    else:
        print(f"Error getting spot state: {spot_result.unwrap_err()}")

    print()

    # Get open orders
    orders_result = await api.info.user_open_orders()
    if orders_result.is_ok():
        orders = orders_result.unwrap()

        print("📋 Open Orders:")
        if orders:
            for order in orders:
                asset = order.get("coin", "Unknown")
                side = "Buy" if order.get("side") == "B" else "Sell"
                size = order.get("sz", "0")
                price = order.get("limitPx", "0")
                order_id = order.get("oid", "Unknown")

                print(f"  {side} {size} {asset} @ ${price} (ID: {order_id})")
        else:
            print("  No open orders")
    else:
        print(f"Error getting open orders: {orders_result.unwrap_err()}")

    print()

    # Get recent fills
    fills_result = await api.info.user_fills()
    if fills_result.is_ok():
        fills = fills_result.unwrap()

        print("💸 Recent Fills (last 10):")
        if fills:
            for fill in fills[:10]:  # Show last 10 fills
                asset = fill.get("coin", "Unknown")
                side = "Buy" if fill.get("side") == "B" else "Sell"
                size = fill.get("sz", "0")
                price = fill.get("px", "0")
                time = fill.get("time", "Unknown")

                print(f"  {side} {size} {asset} @ ${price} ({time})")
        else:
            print("  No recent fills")
    else:
        print(f"Error getting fills: {fills_result.unwrap_err()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
