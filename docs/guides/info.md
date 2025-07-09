# Info Endpoint

[Hyperliquid's Official Info Endpoint Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)

## Overview

The Info endpoint provides comprehensive access to market data, user information, and trading details for both perpetual and spot markets on Hyperliquid. This endpoint serves as the primary source for retrieving real-time and historical data about the exchange state, user positions, orders, and market conditions.

The `Info` class offers methods to interact with various aspects of the exchange, from basic market data like price feeds and order books to detailed user-specific information such as trading history, funding payments, and account states. All methods are asynchronous and designed to work seamlessly with both perpetual and spot trading functionalities.

## Key Features

- **Market Data**: Access real-time prices, order books, and candlestick data
- **User Information**: Retrieve account states, positions, and trading history
- **Order Management**: Check order statuses and open orders
- **Historical Data**: Access funding history, fill history, and ledger updates
- **Cross-Product Support**: Works with both perpetual and spot markets
- **Rate Limiting**: Built-in rate limit information for API usage
- **Flexible Authentication**: Support for both address strings and Account objects
- **Vault Support**: Access vault-specific information and equities
- **Delegation Features**: Query staking delegation information and rewards

## Authentication Methods

The Info class supports flexible authentication for user-specific methods:

1. **Class-level account** - Set during `Api.create()` and used automatically
2. **Method-level address** - Pass address string directly to methods
3. **Method-level account** - Pass different Account object for specific calls

```python
# Method 1: Class-level account (recommended)
api = await Api.create(account=account)
orders = await api.info.user_open_orders()  # Uses class account

# Method 2: Direct address
orders = await api.info.user_open_orders(address="0x...")

# Method 3: Different account per call
other_account = Account(address="0x...", secret_key="0x...")
orders = await api.info.user_open_orders(account=other_account)
```

## Methods Reference

### Convenience Methods
- [**`get_universe()`**](../reference/info.md#hl.Info.get_universe): Retrieve the complete universe of available assets for both perpetual and spot markets

### General Market & User Data
- [**`all_mids()`**](../reference/info.md#hl.Info.all_mids): Retrieve all mid prices for all actively traded coins
- [**`user_open_orders()`**](../reference/info.md#hl.Info.user_open_orders): Retrieve a user's open orders
- [**`user_frontend_open_orders()`**](../reference/info.md#hl.Info.user_frontend_open_orders): Retrieve a user's open orders with additional frontend information
- [**`user_historical_orders()`**](../reference/info.md#hl.Info.user_historical_orders): Retrieve a user's historical orders including filled, canceled, and other completed orders
- [**`user_fills()`**](../reference/info.md#hl.Info.user_fills): Retrieve a user's fill history
- [**`user_fills_by_time()`**](../reference/info.md#hl.Info.user_fills_by_time): Retrieve a user's fills within a specified time range with optional aggregation
- [**`user_twap_slice_fills()`**](../reference/info.md#hl.Info.user_twap_slice_fills): Retrieve a user's TWAP slice fills
- [**`user_rate_limit()`**](../reference/info.md#hl.Info.user_rate_limit): Retrieve a user's current rate limit status
- [**`order_status()`**](../reference/info.md#hl.Info.order_status): Check the status of a specific order by ID or client order ID
- [**`user_sub_accounts()`**](../reference/info.md#hl.Info.user_sub_accounts): Retrieve a user's subaccounts
- [**`l2_book()`**](../reference/info.md#hl.Info.l2_book): Retrieve the Level 2 order book for a given coin with optional aggregation
- [**`candle_snapshot()`**](../reference/info.md#hl.Info.candle_snapshot): Retrieve candlestick data for a coin within a time range
- [**`max_builder_fee()`**](../reference/info.md#hl.Info.max_builder_fee): Get the maximum builder fee for a user-builder pair
- [**`vault_details()`**](../reference/info.md#hl.Info.vault_details): Retrieve detailed information about a specific vault
- [**`user_vault_equities()`**](../reference/info.md#hl.Info.user_vault_equities): Retrieve a user's vault equity holdings
- [**`user_role()`**](../reference/info.md#hl.Info.user_role): Retrieve a user's role information
- [**`user_portfolio()`**](../reference/info.md#hl.Info.user_portfolio): Retrieve a user's complete portfolio information
- [**`user_referral()`**](../reference/info.md#hl.Info.user_referral): Retrieve a user's referral information and statistics
- [**`user_fees()`**](../reference/info.md#hl.Info.user_fees): Retrieve a user's fee structure and trading fee information
- [**`user_delegations()`**](../reference/info.md#hl.Info.user_delegations): Retrieve a user's staking delegations
- [**`user_delegator_summary()`**](../reference/info.md#hl.Info.user_delegator_summary): Retrieve summary of a user's delegation activities
- [**`user_delegator_history()`**](../reference/info.md#hl.Info.user_delegator_history): Retrieve historical delegation activities for a user
- [**`user_delegator_rewards()`**](../reference/info.md#hl.Info.user_delegator_rewards): Retrieve staking rewards information for a delegator

### Perpetual Markets
- [**`perpetual_dexs()`**](../reference/info.md#hl.Info.perpetual_dexs): Retrieve list of available perpetual DEXes
- [**`perpetual_meta()`**](../reference/info.md#hl.Info.perpetual_meta): Retrieve exchange metadata for perpetual assets
- [**`perpetual_meta_and_asset_ctxs()`**](../reference/info.md#hl.Info.perpetual_meta_and_asset_ctxs): Retrieve perpetual metadata along with asset contexts
- [**`user_state()`**](../reference/info.md#hl.Info.user_state): Get detailed trading information about a user's perpetual positions and margin
- [**`user_funding()`**](../reference/info.md#hl.Info.user_funding): Retrieve a user's funding payment history within a time range
- [**`user_non_funding_ledger_updates()`**](../reference/info.md#hl.Info.user_non_funding_ledger_updates): Get non-funding ledger updates (deposits, transfers, withdrawals)
- [**`funding_history()`**](../reference/info.md#hl.Info.funding_history): Retrieve funding rate history for a specific coin within a time range
- [**`predicted_fundings()`**](../reference/info.md#hl.Info.predicted_fundings): Retrieve predicted funding rates for all perpetual assets
- [**`perpetuals_at_open_interest_cap()`**](../reference/info.md#hl.Info.perpetuals_at_open_interest_cap): Retrieve perpetuals currently at their open interest cap
- [**`perpetual_deploy_auction_status()`**](../reference/info.md#hl.Info.perpetual_deploy_auction_status): Retrieve status of perpetual deployment auctions

### Spot Markets
- [**`spot_meta()`**](../reference/info.md#hl.Info.spot_meta): Retrieve exchange metadata for spot assets
- [**`spot_meta_and_asset_ctxs()`**](../reference/info.md#hl.Info.spot_meta_and_asset_ctxs): Retrieve spot metadata along with asset contexts
- [**`spot_user_state()`**](../reference/info.md#hl.Info.spot_user_state): Get detailed trading information about a user's spot balances and positions
- [**`spot_deploy_auction_status()`**](../reference/info.md#hl.Info.spot_deploy_auction_status): Retrieve status of spot asset deployment auctions
- [**`token_details()`**](../reference/info.md#hl.Info.token_details): Retrieve detailed information about a specific token by ID

## Usage Examples

### Basic Market Data

```python
from hl import Api

async def get_market_data():
    api = await Api.create()

    # Get all current mid prices
    result = await api.info.all_mids()
    if result.is_ok():
        mids = result.unwrap()
        print(f"BTC mid price: ${mids.get('BTC', 'N/A')}")

    # Get order book for a specific coin
    result = await api.info.l2_book(asset="BTC")
    if result.is_ok():
        book = result.unwrap()
        if book['levels']:
            best_bid = book['levels'][0][0]['px']
            print(f"Best bid: ${best_bid}")

asyncio.run(get_market_data())
```

### User Account Information

```python
from hl import Api, Account
import os

async def get_user_info():
    # Initialize with account for automatic authentication
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )
    api = await Api.create(account=account)

    # Get user's open orders (uses class account automatically)
    result = await api.info.user_open_orders()
    if result.is_ok():
        orders = result.unwrap()
        print(f"Open orders: {len(orders)}")

    # Get user's current state and positions
    result = await api.info.user_state()
    if result.is_ok():
        state = result.unwrap()
        print(f"Withdrawable balance: ${state['withdrawable']}")

    # Get trading fills
    result = await api.info.user_fills()
    if result.is_ok():
        fills = result.unwrap()
        print(f"Recent fills: {len(fills)}")

asyncio.run(get_user_info())
```

### Historical Data and Time-based Queries

```python
from datetime import datetime, timedelta

async def get_historical_data():
    api = await Api.create(account=account)

    # Get recent fills within last 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    result = await api.info.user_fills_by_time(
        start=start_time,
        end=end_time,
        aggregate_by_time=True  # Combine partial fills
    )
    if result.is_ok():
        fills = result.unwrap()
        print(f"Fills in last 7 days: {len(fills)}")

    # Get funding history for BTC over last 30 days
    result = await api.info.funding_history(
        asset="BTC",
        start=datetime.now() - timedelta(days=30)
    )
    if result.is_ok():
        funding = result.unwrap()
        print(f"BTC funding events: {len(funding)}")

asyncio.run(get_historical_data())
```

## Error Handling

All Info methods return `Result[T, ApiError]` types for explicit error handling:

```python
async def safe_info_call():
    api = await Api.create()

    result = await api.info.all_mids()
    if result.is_ok():
        mids = result.unwrap()
        # Handle successful response
        return mids
    else:
        error = result.unwrap_err()
        print(f"API Error: {error.message}")
        # Handle error case
        return None
```

## Advanced Features

### Asset Name/ID Conversion

The Info class automatically handles asset name/ID conversion through the Universe:

```python
# These are equivalent - SDK handles conversion automatically
book_by_name = await api.info.l2_book(asset="BTC")
book_by_id = await api.info.l2_book(asset=0)  # BTC has ID 0
```

## Best Practices

1. **Reuse Api instances** - Avoid creating multiple instances unnecessarily
2. **Handle Results properly** - Always check `is_ok()` before calling `unwrap()`
3. **Use appropriate authentication** - Class-level accounts for repeated calls, method-level for one-offs
4. **Cache Universe data** - The universe is automatically fetched and cached during `Api.create()`



