# Authentication

The `hl-sdk` uses Ethereum-compatible wallet authentication for secure access to private endpoints. This guide covers everything you need to know about authentication.

## Overview

Hyperliquid uses cryptographic signatures to authenticate requests. The SDK handles all the complexity of signing requests - you just need to provide your wallet credentials.

## The Account Class

The `Account` class stores your authentication credentials:

```python
from hl import Account

account = Account(
    address="0x1234567890123456789012345678901234567890",
    secret_key="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    vault_address="0x9876543210987654321098765432109876543210"  # Optional
)
```

### Parameters

- **`address`** (required): Your wallet's Ethereum address (42 characters including '0x')
- **`secret_key`** (required): Your wallet's private key (64 characters hex + '0x' prefix)
- **`vault_address`** (optional): If you're using a vault for trading

## Creating an Account

### From Environment Variables (Recommended)

The most secure way is to load credentials from environment variables:

```python
import os
from hl import Account

account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"],
    vault_address=os.environ.get("HL_VAULT_ADDRESS")  # Optional
)
```

Set these environment variables in your shell:

```bash
export HL_ADDRESS="0x1234567890123456789012345678901234567890"
export HL_SECRET_KEY="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
export HL_VAULT_ADDRESS="0x9876543210987654321098765432109876543210"  # Optional
```

### From a Configuration File

You can load credentials from a secure configuration file:

```python
import json
from pathlib import Path
from hl import Account

# Load from JSON file
config_path = Path.home() / ".hl" / "config.json"
with open(config_path) as f:
    config = json.load(f)

account = Account(
    address=config["address"],
    secret_key=config["secret_key"],
    vault_address=config.get("vault_address")
)
```

### From Just a Secret Key

If you only have a secret key, the Account class can derive the address:

```python
from hl import Account

# The address will be derived from the secret key
account = Account.from_key(
    secret_key="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    vault_address=None  # Optional
)

print(f"Derived address: {account.address}")
```

## Using Authentication

### Authenticated API Instance

Pass the account when creating the API:

```python
from hl import Api, Account

account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"]
)

# All operations will use this account by default
api = await Api.create(account=account)

# Place an order (automatically signed with your account)
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=Decimal("0.001"),
    limit_price=Decimal("65000"),
    order_type="limit"
)
```

### Per-Method Authentication

You can also provide authentication per method call:

```python
# Create API without default account
api = await Api.create()

# Create multiple accounts
main_account = Account(address="0x...", secret_key="0x...")
trading_account = Account(address="0x...", secret_key="0x...")

# Use different accounts for different operations
result1 = await api.info.user_state(account=main_account)
result2 = await api.exchange.place_order(
    asset="ETH",
    is_buy=True,
    size=Decimal("0.1"),
    limit_price=Decimal("3000"),
    order_type="limit",
    account=trading_account  # Use specific account
)
```

## Agent Wallets

If you're using an agent wallet (where the signing address differs from the main address), the SDK handles this automatically:

```python
from hl import Account

# The SDK will detect if the derived address doesn't match
# and handle agent wallet signing appropriately
account = Account(
    address="0x1111111111111111111111111111111111111111",  # Main address
    secret_key="0x2222..."  # Agent wallet's secret key
)
```

## Vault Trading

For vault-based trading, provide the vault address:

```python
from hl import Account

account = Account(
    address="0x1234567890123456789012345678901234567890",
    secret_key="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    vault_address="0x9876543210987654321098765432109876543210"
)

api = await Api.create(account=account)

# Orders will be placed for the vault
result = await api.exchange.place_order(...)
```

## Security Best Practices

### 1. Never Hard-Code Credentials

```python
# ❌ NEVER DO THIS
account = Account(
    address="0x1234567890123456789012345678901234567890",
    secret_key="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
)

# ✅ Always use environment variables or secure storage
account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"]
)
```

### 2. Use Secure File Permissions

If storing credentials in files:

```bash
# Set restrictive permissions
chmod 600 ~/.hl/config.json
```

### 3. Use a Secrets Manager

For production environments, use a proper secrets manager:

```python
# Example with AWS Secrets Manager
import boto3
import json

def get_account_from_aws():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='hl-trading-credentials')
    secrets = json.loads(response['SecretString'])

    return Account(
        address=secrets['address'],
        secret_key=secrets['secret_key']
    )
```

### 4. Validate Addresses

Always validate address formats:

```python
def is_valid_address(address: str) -> bool:
    """Check if address is valid Ethereum format."""
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

# Validate before use
if not is_valid_address(my_address):
    raise ValueError("Invalid Ethereum address")
```

## Testing with Testnet

Always test with testnet first:

```python
from hl import Api, Account, TESTNET

account = Account(
    address=os.environ["HL_TESTNET_ADDRESS"],
    secret_key=os.environ["HL_TESTNET_SECRET_KEY"]
)

# Create API for testnet
api = await Api.create(account=account, network=TESTNET)

# Test your strategies safely
result = await api.exchange.place_order(...)
```

## Common Issues

### Address Mismatch Warning

If you see a warning about address mismatch:

```
WARNING: Address mismatch: provided 0x123..., using derived 0x456...
```

This happens when using an agent wallet. The SDK handles this automatically, but verify that the derived address is correct for your use case.

### Invalid Signature Errors

If you get signature validation errors:

1. Ensure your secret key is correct (64 hex characters + '0x' prefix)
2. Check that you're using the right network (mainnet vs testnet)
3. Verify your system clock is synchronized

## Next Steps

- Review [Security Best Practices](https://ethereum.org/en/developers/docs/smart-contracts/security/)
- Explore [Examples](examples.md) for real-world authentication patterns
