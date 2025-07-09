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

    # Get market data
    result = await api.info.perpetual_meta()
    if result.is_ok():
        meta = result.unwrap()
        print(meta)
    else:
        print(result.unwrap_err())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
