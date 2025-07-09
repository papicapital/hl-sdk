import os

from hl import Account, Api

# Credentials also be e.g. loaded from a file instead
address = os.environ["HL_ADDRESS"]
secret_key = os.environ["HL_SECRET_KEY"]


async def main() -> None:
    account = Account(address=address, secret_key=secret_key)
    api = await Api.create(account=account)

    # Use class level authentication
    result0 = await api.info.user_open_orders()

    # Provide address as argument
    result1 = await api.info.user_open_orders(address=address)

    # Provide account as argument
    result2 = await api.info.user_open_orders(account=account)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
