# Universe

The `Universe` class is central to asset management in `hl-sdk`. It provides mappings between asset names and IDs, detailed asset metadata, and utility methods for price and size rounding according to Hyperliquid's exchange rules.

!!! note "Automatic Universe Loading"
    When you create an `Api` instance using `Api.create()`, the SDK automatically makes two API requests to populate the Universe:

    1. **`perpetual_meta()`** - Fetches metadata for all perpetual trading pairs
    2. **`spot_meta()`** - Fetches metadata for all spot trading pairs

    This ensures the Universe is always up-to-date with the latest available assets and their properties.

!!! info "Official Hyperliquid Documentation"
    This page documents the `Universe` class which implements Python helpers for Hyperliquid's official asset and pricing rules:

    - **[Asset IDs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids)** - How asset identification works for perpetuals, spot, and builder-deployed assets
    - **[Tick and Lot Size](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size)** - Official price and size formatting rules (5 sig figs, decimal limits, etc.)

    The `Universe` class automatically handles these complex rules so you don't have to implement them manually.

## Overview

The Universe contains all the information you need about available assets on the exchange:

- **Asset Mappings**: Convert between asset names ("BTC") and IDs (0)
- **Asset Metadata**: Decimals, type (SPOT/PERPETUAL), and other properties
- **Rounding Utilities**: Automatically round prices and sizes to exchange requirements

## Accessing the Universe

The Universe is automatically loaded when you create an API instance and is accessible via `api.universe`:

```python
import asyncio
from hl import Api

async def main():
    api = await Api.create()

    # Universe is automatically available
    print(f"BTC asset ID: {api.universe.to_asset_id('BTC')}")
    print(f"Asset 0 name: {api.universe.to_asset_name(0)}")

asyncio.run(main())
```

!!! warning "Don't Create Universe Directly"
    Never instantiate `Universe` directly. It's automatically created and populated when you create an `Api` instance. The universe data comes from the exchange's metadata endpoints.

## Asset Name and ID Conversion

### Converting Between Names and IDs

```python
# Get asset ID from name
btc_id = api.universe.to_asset_id("BTC")  # Returns: 0
eth_id = api.universe.to_asset_id("ETH")  # Returns: 1

# Get asset name from ID
asset_name = api.universe.to_asset_name(0)  # Returns: "BTC"

# Works with both strings and integers
btc_id = api.universe.to_asset_id(0)      # Returns: 0 (no change)
btc_name = api.universe.to_asset_name("BTC")  # Returns: "BTC" (no change)
```

### Direct Access to Mappings

```python
# Access the mapping dictionaries directly
name_to_id = api.universe.name_to_id
id_to_name = api.universe.id_to_name
id_to_info = api.universe.id_to_info

print(f"All asset names: {list(name_to_id.keys())}")
print(f"BTC info: {id_to_info[0]}")
```

## Price and Size Rounding

Hyperliquid has specific rules for valid prices and sizes. The Universe automatically handles rounding to comply with these rules.

### Price Rounding

Prices must satisfy two rules:
- ≤5 significant figures
- ≤`pxDecimals` decimal places

```python
from decimal import Decimal

# Round a price to exchange requirements
price = Decimal("65432.123456789")
rounded_price = api.universe.round_price("BTC", price)
print(f"Rounded price: {rounded_price}")  # e.g., "65432"

# The method chooses the more restrictive rule
precise_price = Decimal("1.123456789")
rounded = api.universe.round_price("BTC", precise_price)
print(f"Rounded precise price: {rounded}")  # e.g., "1.1235"
```

### Size Rounding

Sizes must respect the asset's `szDecimals` property:

```python
# Round size to valid increments
size = Decimal("0.123456789")
rounded_size = api.universe.round_size("BTC", size)
print(f"Rounded size: {rounded_size}")  # e.g., "0.001235" (depends on asset)

# Different assets have different size decimals
eth_size = api.universe.round_size("ETH", Decimal("1.123456789"))
print(f"ETH rounded size: {eth_size}")
```

### Custom Rounding Modes

Both methods support custom rounding modes:

```python
from decimal import ROUND_DOWN, ROUND_UP

# Round down (conservative for buys)
conservative_price = api.universe.round_price(
    "BTC",
    Decimal("65432.7"),
    rounding=ROUND_DOWN
)

# Round up (conservative for sells)
conservative_size = api.universe.round_size(
    "BTC",
    Decimal("0.0015"),
    rounding=ROUND_UP
)
```

## Asset Information

### Asset Types

Assets can be either perpetual futures or spot pairs:

```python
# Check asset type
btc_info = api.universe.id_to_info[api.universe.to_asset_id("BTC")]
print(f"BTC type: {btc_info['type']}")  # "PERPETUAL"

# Spot assets start from ID 10,000
usdc_info = api.universe.id_to_info[10000]  # First spot asset
print(f"Spot asset type: {usdc_info['type']}")  # "SPOT"
```

### Decimal Properties

Each asset has specific decimal configurations:

```python
btc_info = api.universe.id_to_info[0]

print(f"Price decimals: {btc_info['pxDecimals']}")  # Max decimal places for prices
print(f"Size decimals: {btc_info['szDecimals']}")   # Max decimal places for sizes
```

## Practical Usage Patterns

### Safe Order Placement

Always round values before placing orders:

```python
async def place_safe_order(api, asset, is_buy, size, price):
    # Round to exchange requirements
    safe_size = api.universe.round_size(asset, size)
    safe_price = api.universe.round_price(asset, price)

    return await api.exchange.place_order(
        asset=asset,
        is_buy=is_buy,
        size=safe_size,
        limit_price=safe_price,
        order_type={"limit": {"tif": "Gtc"}},
        reduce_only=False
    )
```

### Asset Validation

Check if an asset exists before using it:

```python
def is_valid_asset(api, asset):
    """Check if an asset exists in the universe."""
    try:
        api.universe.to_asset_id(asset)
        return True
    except KeyError:
        return False

# Validate before trading
if is_valid_asset(api, "BTC"):
    # Safe to proceed
    pass
else:
    print("Asset not found!")
```

## Asset Categories

### Perpetual Assets

Perpetual futures have IDs starting from 0:

```python
# Find all perpetual assets
perpetuals = []
for asset_id, info in api.universe.id_to_info.items():
    if info['type'] == 'PERPETUAL':
        perpetuals.append(info['name'])

print(f"Available perpetuals: {perpetuals}")
```

### Spot Assets

Spot pairs have IDs starting from 10,000:

```python
# Find all spot assets
spot_assets = []
for asset_id, info in api.universe.id_to_info.items():
    if info['type'] == 'SPOT':
        spot_assets.append(info['name'])

print(f"Available spot pairs: {spot_assets}")
```

## Advanced: Manual Universe Creation

!!! warning "Advanced Usage Only"
    This section is for advanced users who need to manually create a Universe instance. In most cases, the `Api` class handles this automatically and you should use `api.universe` instead.

### Creating Universe from Info Instance

If you need to manually retrieve the Universe (e.g., for custom transport implementations), you can use the `Info` class directly:

```python
from hl import Info
from hl.transport import HttpTransport
from hl.network import MAINNET

async def manual_universe_creation():
    # Create Info instance with custom transport
    transport = HttpTransport(MAINNET, "info")
    info = Info(transport=transport)

    # Manually fetch universe - this makes the same API calls as Api.create()
    universe = await info.get_universe()

    # Now you can use the universe
    btc_id = universe.to_asset_id("BTC")
    print(f"BTC asset ID: {btc_id}")

    return universe
```

### Creating Universe from Raw Metadata

For even more control, you can create a Universe from raw metadata responses:

```python
from hl.universe import Universe

async def create_from_raw_meta():
    # Fetch metadata manually
    perpetual_meta_result = await info.perpetual_meta()
    spot_meta_result = await info.spot_meta()

    if perpetual_meta_result.is_ok() and spot_meta_result.is_ok():
        perpetual_meta = perpetual_meta_result.unwrap()
        spot_meta = spot_meta_result.unwrap()

        # Create Universe from metadata
        universe = Universe.from_perpetual_meta_and_spot_meta(perpetual_meta, spot_meta)
        return universe
    else:
        raise Exception("Failed to fetch metadata")
```

### Use Cases for Manual Creation

Manual Universe creation might be useful for:

- **Custom caching strategies** - Cache Universe data locally
- **Offline analysis** - Work with saved metadata without live API calls
- **Custom transport layers** - Use alternative HTTP clients or proxies
- **Testing scenarios** - Mock Universe data for unit tests

```python
# Example: Caching Universe data
import json
from pathlib import Path

async def cached_universe():
    cache_file = Path("universe_cache.json")

    if cache_file.exists():
        # Load from cache
        with open(cache_file) as f:
            cached_data = json.load(f)
        universe = Universe(cached_data["id_to_info"])
    else:
        # Fetch fresh and cache
        universe = await info.get_universe()

        # Save to cache
        with open(cache_file, "w") as f:
            json.dump({"id_to_info": universe.id_to_info}, f)

    return universe
```

!!! tip "Stick to Api.create()"
    Unless you have specific advanced requirements, always use `Api.create()` which handles Universe creation automatically and ensures all components work together correctly.
