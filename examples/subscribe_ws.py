import os

from hl import TESTNET, Account, Api

# Credentials also be e.g. loaded from a file instead
address = os.environ["HL_ADDRESS"]
secret_key = os.environ["HL_SECRET_KEY"]


async def main() -> None:
    account = Account(address=address, secret_key=secret_key)
    # Initialize the API client with your wallet credentials
    api = await Api.create(
        account=account,
        network=TESTNET,  # Using testnet
    )

    async with api.ws.run():
        # Subscribe to the L2 book for BTC
        sub_id, queue = await api.ws.subscriptions.l2_book(asset="BTC")

        # Process the next 10 messages
        for _ in range(10):
            msg = await queue.get()
            print(msg)

        # If the websocket connection remains in use, remember to unsubscribe
        # Unsubscribe so the queue can be removed for no longer being active
        await api.ws.subscriptions.unsubscribe(sub_id)

        # The websocket connection will be closed when the context manager exits


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
