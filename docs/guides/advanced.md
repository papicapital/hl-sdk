# Advanced Usage

While the `Api.create()` method abstracts away most complexity, understanding the underlying components can be helpful for advanced use cases, debugging, or extending the library. The Hyperliquid SDK is built on several key internal classes that work together to provide seamless trading functionality.

### Account Class

The `Account` class holds authentication credentials and is the foundation of all authenticated operations. It replaces the previous direct `address` and `secret_key` parameters.

#### What it does:
- **Credential Management**: Stores address, secret key, and optional vault address
- **Key Validation**: Validates that the address matches the derived address from the secret key
- **Local Account Integration**: Automatically creates an eth_account LocalAccount for signing

#### Key capabilities:
```python
from hl import Account

# Create account with explicit address
account = Account(
    address="0x...",
    secret_key="0x...",
    vault_address="0x..."  # optional
)

# Create account from just a secret key (address will be derived)
account = Account.from_key("0x...", vault_address="0x...")

# The account automatically handles address validation
# If provided address doesn't match derived address, a warning is logged
```

#### Using accounts with the API:
```python
# Create API with account
api = await Api.create(account=account)

# Or create without account for public endpoints only
api = await Api.create()  # No authenticated operations available
```

### Signer Class

The `Signer` class handles cryptographic authentication for all exchange operations. It's created internally and uses the `Account` class for credentials.

#### What it does:

- **Request Authentication**: Signs all exchange requests with the account's private key
- **Nonce Management**: Generates unique nonces to prevent replay attacks
- **Network Awareness**: Adjusts signing parameters based on mainnet vs testnet
- **Action Type Handling**: Uses different signing methods for L1 actions vs user actions

#### Key responsibilities:
```python
# The signer automatically handles:
# 1. Converting actions to signable messages
# 2. Generating cryptographic signatures
# 3. Managing nonce sequences
# 4. Ensuring network-appropriate formatting

# Example of what happens internally when you place an order:
order_action = {
    "type": "order",
    "orders": [...],
    "grouping": "na"
}

# Signer creates signature and nonce
signature, nonce = signer.sign(order_action, network)

# Final payload includes authentication
payload = {
    "action": order_action,
    "nonce": nonce,
    "signature": signature,
    "vaultAddress": account.vault_address
}
```

#### Accessing the signer:
```python
api = await Api.create(account=account)

# Signer is created on-demand within exchange methods
# You can create one manually if needed:
from hl.signer import Signer
signer = Signer(account)
print(f"Signer address: {signer.account.address}")
print(f"Vault address: {signer.account.vault_address}")
```

### Universe Class

The `Universe` class provides essential mappings and metadata about tradeable assets on Hyperliquid. It acts as a bridge between human-readable asset names and the internal identifiers used by the exchange.

#### What it does:

- **Name to ID Mapping**: Converts coin tickers (e.g., "BTC") to internal asset IDs
- **Asset Metadata**: Provides precision, tick sizes, and market parameters
- **Price/Size Rounding**: Ensures values conform to asset-specific precision rules
- **Market Information**: Contains details about perpetual and spot markets

#### Key capabilities:
```python
# The universe automatically handles:
# 1. Converting "BTC" to asset ID 0
# 2. Ensuring prices are rounded to valid tick sizes
# 3. Validating order sizes meet minimum requirements
# 4. Providing market-specific parameters

# Example of internal usage:
api = await Api.create(account=account)
universe = api.universe  # Direct access to universe

# Name to ID conversion
btc_id = universe.name_to_id["BTC"]  # Returns: 0
eth_id = universe.name_to_id["ETH"]  # Returns: 1

# Access market metadata
print(f"Available assets: {list(universe.name_to_id.keys())}")
```

#### Rounding and precision:
```python
# The universe ensures all prices and sizes are properly formatted

from decimal import Decimal

# When you specify:
order_response = await api.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=api.universe.round_size("BTC", Decimal("0.12345678")),      # May be rounded to valid precision
    limit_price=api.universe.round_price(Decimal("45000.123")), # May be rounded to valid tick size
    order_type={"type": "limit", "tif": "gtc"}
)

# The universe ensures these values conform to BTC's market rules
```

### Transport Classes

The SDK uses specialized transport classes to handle communication with different endpoints. These classes manage HTTP requests, websocket connections, and response handling.

#### HttpTransport

Handles HTTP communication with the `/info` and `/exchange` endpoints.

**Responsibilities:**
- **Request Management**: Formats and sends HTTP POST requests
- **Response Parsing**: Handles JSON response parsing and error detection
- **Network Configuration**: Manages base URLs and endpoint routing
- **Error Handling**: Provides consistent error reporting across endpoints

```python
# Internal structure (you typically don't need to access this directly)
api = await Api.create(account=account)

# Info endpoint uses an HttpTransport
info_transport = api.info.transport
print(f"Info transport URL: {info_transport.url}")

# Exchange endpoint uses an HttpTransport
exchange_transport = api.exchange.transport
print(f"Exchange transport URL: {exchange_transport.url}")
```

#### WebSocket Client (Ws class)

Manages real-time data streams and bidirectional communication.

**Responsibilities:**
- **Connection Management**: Establishes and maintains websocket connections
- **Subscription Handling**: Manages multiple data stream subscriptions
- **Message Routing**: Delivers messages to appropriate queues
- **Reconnection Logic**: Automatically reconnects on connection failures

```python
# The websocket client handles complex connection management
api = await Api.create(account=account)

# Access websocket internals (advanced usage)
ws_client = api.ws
print(f"WebSocket network: {ws_client._transport.network}")
```

## How Components Work Together

Understanding how these components interact helps explain the library's architecture:

```python
# High-level flow for placing an order:

# 1. Api.create() initializes all components
account = Account.from_key("0x...")
api = await Api.create(account=account)

# 2. Universe converts coin name to asset ID
coin = "BTC"
asset_id = api.universe.name_to_id[coin]  # "BTC" -> 0

# 3. Order parameters are validated and formatted
order_params = {
    "asset": coin,
    "is_buy": True,
    "size": Decimal("0.1"),
    "limit_price": Decimal("45000"),
    "order_type": {"type": "limit", "tif": "gtc"}
}

# 4. Exchange creates order wire format using universe data
order_wire = order_request_to_order_wire(order_params, asset_id)

# 5. Signer creates cryptographic signature
action = {"type": "order", "orders": [order_wire], "grouping": "na"}
signer = Signer(account)
signature, nonce = signer.sign(action, api.exchange.transport.network)

# 6. HttpTransport sends authenticated request
payload = {
    "action": action,
    "nonce": nonce,
    "signature": signature,
    "vaultAddress": account.vault_address
}
response = await api.exchange.transport.invoke(payload)
```
