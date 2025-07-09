from decimal import ROUND_HALF_EVEN, Decimal

from hl.types import AssetInfo, Meta, SpotMeta

NUM_SIGNIFICANT_FIGURES = 5
MAX_DECIMALS_PERPETUAL = 6
MAX_DECIMALS_SPOT = 8


class Universe:
    """The Universe class provides asset information and metadata for the exchange.

    The Universe contains mappings between asset names and IDs, along with detailed
    information about each asset including decimals, type (SPOT/PERPETUAL), and other
    metadata. It also provides utility methods for rounding prices and sizes according
    to each asset's rules.

    Warning: Do not instantiate Universe directly. Use Info.get_universe() instead.

    Example:
        Retrieve the universe from the Info class:

        >>> api = await Api.create(address="0x...", secret_key="0x...")
        ... universe = await api.info.get_universe()
        ... btc_id = universe.name_to_id["BTC"]  # Get BTC's asset ID
        ... btc_info = universe.id_to_info[btc_id]  # Get BTC's asset info
    """

    name_to_id: dict[str, int]
    """Mapping from asset names (e.g. "BTC", "ETH") to their numeric asset IDs."""

    id_to_name: dict[int, str]
    """Mapping from asset IDs to their names (e.g. "BTC", "ETH")."""

    id_to_info: dict[int, AssetInfo]
    """Mapping from asset IDs to detailed asset information including decimals and type."""

    def __init__(self, id_to_info: dict[int, AssetInfo] | None = None):
        """Initialize a Universe instance with a mapping from asset IDs to asset info.

        Warning: This constructor is for internal use only. Users should not
        have to instantiate Universe directly. Instead, retrieve the universe using:

            universe = await api.info.get_universe()

        or

            universe = Universe.from_meta_and_spot_meta(meta, spot_meta)

        Args:
            id_to_info (dict[int, AssetInfo] | None): Mapping from asset IDs to asset info.
        """
        if id_to_info is None:
            id_to_info = {}

        self.name_to_id = {
            asset_info["name"]: asset_info["id"] for asset_info in id_to_info.values()
        }
        self.id_to_name = {
            asset_info["id"]: asset_info["name"] for asset_info in id_to_info.values()
        }
        self.id_to_info = id_to_info

    @classmethod
    def from_perpetual_meta_and_spot_meta(
        cls, perpetual_meta: Meta, spot_meta: SpotMeta
    ) -> "Universe":
        """Create a Universe instance from perpetual and spot metadata.

        Args:
            perpetual_meta (hl.types.Meta): Perpetual assets metadata containing the universe of
                         perpetual trading pairs and their properties.
            spot_meta (hl.types.SpotMeta): Spot assets metadata containing the universe of
                                  spot trading pairs and token information.

        Returns:
            (hl.universe.Universe): A Universe instance with the asset information from the
                                    perpetual and spot metadata.
        """
        id_to_info = {
            asset_id: AssetInfo(
                id=asset_id,
                name=asset_meta["name"],
                type="PERPETUAL",
                pxDecimals=MAX_DECIMALS_PERPETUAL - asset_meta["szDecimals"],
                szDecimals=asset_meta["szDecimals"],
            )
            for asset_id, asset_meta in enumerate(perpetual_meta["universe"])
        }
        for spot_asset_meta in spot_meta["universe"]:
            # Spot assets are indexed from 10_000 onwards
            asset_id = spot_asset_meta["index"] + 10_000
            base, quote = spot_asset_meta["tokens"]
            id_to_info[asset_id] = AssetInfo(
                id=asset_id,
                name=spot_asset_meta["name"],
                type="SPOT",
                pxDecimals=MAX_DECIMALS_SPOT - spot_meta["tokens"][base]["szDecimals"],
                szDecimals=spot_meta["tokens"][base]["szDecimals"],
            )
        return cls(id_to_info)

    def to_asset_name(self, asset: int | str) -> str:
        """Convert an asset ID or name to an asset name.

        Args:
            asset (int | str): The asset ID or name to convert.

        Returns:
            str: The asset name.
        """
        if isinstance(asset, int):
            return self.id_to_name[asset]
        return asset

    def to_asset_id(self, asset: int | str) -> int:
        """Convert an asset ID or name to an asset ID.

        Args:
            asset (int | str): The asset ID or name to convert.

        Returns:
            int: The asset ID.
        """
        if isinstance(asset, int):
            return asset
        return self.name_to_id[asset]

    def round_price(
        self,
        asset: int | str,
        price: Decimal,
        rounding: str = ROUND_HALF_EVEN,
    ) -> Decimal:
        """Round *price* so it satisfies Hyperliquid’s tick-size rules.

        Rules (docs): ≤5 sig figs and ≤pxDecimals decimals.  Integers are always OK.

        Reference: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size

        Args:
            asset (int | str): The asset ID or name to round the price for.
            price (decimal.Decimal): The price to round.
            rounding (str): The rounding mode to use. Defaults to ROUND_HALF_EVEN.

        Returns:
            decimal.Decimal: The rounded price.
        """
        info = self.id_to_info[self.to_asset_id(asset)]
        price = price.normalize()

        # Integers already satisfy both rules
        if price == price.to_integral_value():
            return price

        # How many decimals does each rule allow?
        sigfig_exp = price.adjusted() - (NUM_SIGNIFICANT_FIGURES - 1)
        tick_exp = max(sigfig_exp, -info["pxDecimals"])  # “larger” tick dominates

        # Round and strip trailing zeros
        return price.quantize(Decimal(f"1e{tick_exp}"), rounding).normalize()

    def round_size(
        self,
        asset: int | str,
        size: Decimal,
        rounding: str = ROUND_HALF_EVEN,
    ) -> Decimal:
        """Round a size to an allowed value, respecting the coin's szDecimals.

        By default, we round to the nearest allowed size with ties going to the nearest even integer.

        Args:
            asset (int | str): The asset ID or name to round the size for.
            size (decimal.Decimal): The size to round.
            rounding (str): The rounding mode to use. Defaults to ROUND_HALF_EVEN.

        Returns:
            decimal.Decimal: The rounded size.
        """
        size_decimals = self.id_to_info[self.to_asset_id(asset)]["szDecimals"]
        return size.quantize(Decimal(f"1e-{size_decimals}"), rounding=rounding)
