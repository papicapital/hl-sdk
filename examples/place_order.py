import os
from decimal import Decimal

from hl import LIMIT_GTC, TESTNET, Account, Api
from hl.types import is_error_status, is_filled_status, is_resting_status

# Get credentials from environment variables
address = os.environ["HL_ADDRESS"]
secret_key = os.environ["HL_SECRET_KEY"]


async def main() -> None:
    # Create account and API client
    account = Account(address=address, secret_key=secret_key)
    api = await Api.create(
        account=account,
        network=TESTNET,  # Using testnet for safety
    )

    # Get current BTC price to place order below market
    mids_result = await api.info.all_mids()
    if mids_result.is_err():
        print(f"Error getting prices: {mids_result.unwrap_err()}")
        return

    mids = mids_result.unwrap()
    btc_price = Decimal(mids["BTC"])
    order_price = api.universe.round_price("BTC", btc_price * Decimal("0.99"))
    order_size = Decimal("0.001")  # Small size for testing

    print(f"Placing order: Buy {order_size} BTC at ${order_price}")
    print(f"Current BTC price: ${btc_price}")

    # Place the order
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=order_size,
        limit_price=order_price,
        order_type=LIMIT_GTC,  # Good till canceled
        reduce_only=False,
    )

    # Handle the result
    if result.is_ok():
        response = result.unwrap()
        print(f"Order request sent successfully!")
        print(f"Response: {response}")

        # Check individual order statuses
        statuses = response["response"]["data"]["statuses"]
        for status in statuses:
            if is_resting_status(status):
                print(f"Order resting with ID: {status['resting']['oid']}")
            elif is_error_status(status):
                print(f"Order failed: {status['error']}")
            elif is_filled_status(status):
                fill = status["filled"]
                print(f"Order filled: {fill['totalSz']} at ${fill['avgPx']}")
    else:
        error = result.unwrap_err()
        print(f"Error placing order: {error}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
