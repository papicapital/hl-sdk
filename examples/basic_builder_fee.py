import os
from decimal import Decimal

from hl import TESTNET, Account, Api


async def main() -> None:
    # Get credentials from environment variables
    address = os.environ["HL_ADDRESS"]
    secret_key = os.environ["HL_SECRET_KEY"]

    # Create account and API client
    account = Account(address=address, secret_key=secret_key)
    api = await Api.create(
        account=account,
        network=TESTNET,  # Using testnet
    )

    # Only the main wallet has permission to approve a builder fee
    if api.exchange.account is None or api.exchange.account.address != address:
        raise Exception("Only the main wallet has permission to approve a builder fee")

    # Approve setting a builder fee
    # The max_fee_rate is a decimal percentage (e.g. 0.001 for 0.1%)
    approve_result = await api.exchange.approve_builder(
        builder="0x8c967E73E7B15087c42A10D344cFf4c96D877f1D",
        max_fee_rate=Decimal("0.001"),  # 0.1%
    )
    print("Builder fee approval:", approve_result)

    # Place a market order with builder fee set
    # Market orders in the new SDK use limit orders with IOC (immediate or cancel)
    # and a very favorable limit price
    order_result = await api.exchange.place_order(
        asset="ETH",
        is_buy=True,
        size=Decimal("0.05"),
        limit_price=Decimal("10000")
        if True
        else Decimal("0.01"),  # High price for buy, low for sell
        order_type={"limit": {"tif": "Ioc"}},  # IOC acts as a market order
        reduce_only=False,
        builder={
            "b": "0x8c967E73E7B15087c42A10D344cFf4c96D877f1D",
            "f": 10,
        },  # 10 = 1bp
    )
    print("Order result:", order_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
