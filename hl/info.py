from datetime import date, datetime
from typing import cast

from hl._lib import to_ms
from hl.account import Account
from hl.cloid import Cloid
from hl.errors import ApiError
from hl.result import Result
from hl.transport import BaseTransport
from hl.types import (
    AllMidsRequest,
    AllMidsResponse,
    CandleInterval,
    CandleSnapshotRequest,
    CandleSnapshotRequestPayload,
    CandleSnapshotResponse,
    DelegationsRequest,
    DelegationsResponse,
    DelegatorHistoryRequest,
    DelegatorHistoryResponse,
    DelegatorRewardsRequest,
    DelegatorRewardsResponse,
    DelegatorSummaryRequest,
    DelegatorSummaryResponse,
    FrontendOpenOrdersRequest,
    FrontendOpenOrdersResponse,
    FundingHistoryRequest,
    FundingHistoryResponse,
    HistoricalOrdersRequest,
    HistoricalOrdersResponse,
    L2BookRequest,
    L2BookResponse,
    MaxBuilderFeeRequest,
    MaxBuilderFeeResponse,
    MetaAndAssetCtxsRequest,
    MetaAndAssetCtxsResponse,
    MetaRequest,
    MetaResponse,
    OpenOrdersRequest,
    OpenOrdersResponse,
    OrderStatusRequest,
    OrderStatusResponse,
    PerpDeployAuctionStatusRequest,
    PerpDeployAuctionStatusResponse,
    PerpDexsRequest,
    PerpDexsResponse,
    PerpsAtOpenInterestCapRequest,
    PerpsAtOpenInterestCapResponse,
    PortfolioRequest,
    PortfolioResponse,
    PredictedFundingsRequest,
    PredictedFundingsResponse,
    ReferralRequest,
    ReferralResponse,
    SpotDeployAuctionStatusRequest,
    SpotDeployAuctionStatusResponse,
    SpotMetaAndAssetCtxsRequest,
    SpotMetaAndAssetCtxsResponse,
    SpotMetaRequest,
    SpotMetaResponse,
    SpotUserStateRequest,
    SpotUserStateResponse,
    SubAccountsRequest,
    SubAccountsResponse,
    TokenDetailsRequest,
    TokenDetailsResponse,
    UserFeesRequest,
    UserFeesResponse,
    UserFillsByTimeRequest,
    UserFillsRequest,
    UserFillsResponse,
    UserFundingRequest,
    UserFundingResponse,
    UserNonFundingLedgerUpdatesRequest,
    UserNonFundingLedgerUpdatesResponse,
    UserRateLimitRequest,
    UserRateLimitResponse,
    UserRoleRequest,
    UserRoleResponse,
    UserStateRequest,
    UserStateResponse,
    UserTwapSliceFillsRequest,
    UserTwapSliceFillsResponse,
    UserVaultEquitiesRequest,
    UserVaultEquitiesResponse,
    VaultDetailsRequest,
    VaultDetailsResponse,
)
from hl.universe import Universe
from hl.validator import (
    RULE_EXPECT_DICT,
    RULE_EXPECT_LIST,
    RULE_EXPECT_STATUS_ORDER_STATUS,
)


class Info:
    """The Info class provides methods to interact with the /info endpoint.

    The methods return information about the exchange and about specific users. It works for both Perpetuals and Spot.
    """

    def __init__(
        self,
        *,
        transport: BaseTransport,
        universe: Universe | None = None,
        account: Account | None = None,
    ):
        """Initialize the Info class with the given base URL.

        Args:
            transport (hl.transport.BaseTransport): The transport to use to make the requests.
            universe (hl.universe.Universe | None): The universe to use for the exchange.
            account (hl.account.Account | None): The default account to use for authenticated requests.
        """
        self.transport = transport
        self.universe = universe or Universe({})
        self.account = account

    def _resolve_address(
        self, address: str | None = None, account: Account | None = None
    ) -> str:
        """Resolve the effective address from the provided parameters.

        Args:
            address: Direct address string (mutually exclusive with account)
            account: Account object (mutually exclusive with address)

        Returns:
            The resolved address string

        Raises:
            ValueError: If both address and account are provided, or if none are available
        """
        if address is not None and account is not None:
            raise ValueError(
                "Cannot specify both 'address' and 'account'. Use one or the other."
            )

        if account:
            return account.address
        elif address:
            return address
        elif self.account:
            return self.account.address
        else:
            raise ValueError(
                "No account or address provided. Either initialize Info with an account or provide address/account parameter."
            )

    def _resolve_vault_address(
        self, vault_address: str | None = None, account: Account | None = None
    ) -> str:
        """Resolve the effective vault address from the provided parameters.

        Args:
            vault_address (str | None): Vault address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request must have vault address set (mutually exclusive with vault_address)

        Returns:
            The resolved vault address string

        Raises:
            ValueError: If both vault_address and account are provided, or if none are available
        """
        if vault_address is not None and account is not None:
            raise ValueError(
                "Cannot specify both 'vault_address' and 'account'. Use one or the other."
            )
        if account and account.vault_address:
            return account.vault_address
        elif vault_address:
            return vault_address
        elif self.account and self.account.vault_address:
            return self.account.vault_address
        else:
            raise ValueError(
                "No vault address or account with vault address provided. Either initialize Info with an account or provide vault_address/account parameter."
            )

    ##############
    # CONVENIENCE #
    ##############

    async def get_universe(self) -> Universe:
        """Retrieve the universe for the exchange."""
        perpetual_meta_result = await self.perpetual_meta()
        spot_meta_result = await self.spot_meta()

        if perpetual_meta_result.is_err():
            raise perpetual_meta_result.unwrap_err()
        if spot_meta_result.is_err():
            raise spot_meta_result.unwrap_err()

        return Universe.from_perpetual_meta_and_spot_meta(
            perpetual_meta_result.unwrap(), spot_meta_result.unwrap()
        )

    ###########
    # GENERAL #
    ###########

    async def all_mids(
        self, *, dex: str | None = None
    ) -> Result[AllMidsResponse, ApiError]:
        """Retrieve all mids for all actively traded coins.

        POST /info

        Args:
            dex (str | None): The dex to retrieve mids for. Defaults to Hyperliquid Perp Dex.

        Returns:
            (Result[hl.types.AllMidsResponse, ApiError]): A Result containing a dictionary mapping the coin name to the mid price.

        Examples:
            Retrieve all mids:

            >>> await api.info.all_mids()
            {'BTC': 110000.0, 'ETH': 1000.0, ...}
        """
        payload = AllMidsRequest(type="allMids")
        if dex is not None:
            payload["dex"] = dex

        response = await self.transport.invoke(payload, [RULE_EXPECT_DICT])
        return cast(Result[AllMidsResponse, ApiError], response)

    async def user_open_orders(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[OpenOrdersResponse, ApiError]:
        """Retrieve a user's open orders.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.OpenOrdersResponse, ApiError]): A Result containing a list of open orders.

        Examples:
            Using class-level account:
            >>> info = Info(transport, universe, account=my_account)
            >>> orders = await info.user_open_orders()

            Using specific address:
            >>> orders = await info.user_open_orders(address="0x...")

            Using different account:
            >>> orders = await info.user_open_orders(account=other_account)
        """
        effective_address = self._resolve_address(address, account)
        payload = OpenOrdersRequest(type="openOrders", user=effective_address)
        response = await self.transport.invoke(payload, [RULE_EXPECT_LIST])
        return cast(Result[OpenOrdersResponse, ApiError], response)

    async def user_frontend_open_orders(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[FrontendOpenOrdersResponse, ApiError]:
        """Retrieve a user's open orders with additional frontend info.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.FrontendOpenOrdersResponse, ApiError]): A Result containing a list of open orders with additional frontend info.
        """
        effective_address = self._resolve_address(address, account)
        payload = FrontendOpenOrdersRequest(
            type="frontendOpenOrders", user=effective_address
        )
        response = await self.transport.invoke(payload, [RULE_EXPECT_LIST])
        return cast(Result[FrontendOpenOrdersResponse, ApiError], response)

    async def user_historical_orders(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[HistoricalOrdersResponse, ApiError]:
        """Retrieve a user's historical orders.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.HistoricalOrdersResponse, ApiError]): A Result containing a list of historical orders.
        """
        effective_address = self._resolve_address(address, account)
        payload = HistoricalOrdersRequest(
            type="historicalOrders", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[HistoricalOrdersResponse, ApiError], response)

    async def user_fills(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserFillsResponse, ApiError]:
        """Retrieve a user's fills.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserFillsResponse, ApiError]): A Result containing a list of user fills.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserFillsRequest(type="userFills", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[UserFillsResponse, ApiError], response)

    async def user_fills_by_time(
        self,
        *,
        start: int | datetime | date,
        end: int | datetime | date | None = None,
        aggregate_by_time: bool | None = None,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[UserFillsResponse, ApiError]:
        """Retrieve a user's fills by time.

        POST /info

        Args:
            start (int | datetime | date): Start time in milliseconds or a datetime or date object.
            end (int | datetime | date | None): End time in milliseconds or a datetime or date object.
                Will default .
            aggregate_by_time (bool | None): When true, partial fills are combined when a crossing order gets filled by multiple different resting orders. Resting orders filled by multiple crossing orders will not be aggregated.
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserFillsResponse, ApiError]): A Result containing a list of user fills.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserFillsByTimeRequest(
            type="userFillsByTime",
            user=effective_address,
            startTime=to_ms(start),
            endTime=to_ms(end, "max") if end else None,
        )
        if aggregate_by_time is not None:
            payload["aggregateByTime"] = aggregate_by_time
        response = await self.transport.invoke(payload)
        return cast(Result[UserFillsResponse, ApiError], response)

    async def user_twap_slice_fills(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserTwapSliceFillsResponse, ApiError]:
        """Retrieve a user's TWAP slice fills.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserTwapSliceFillsResponse, ApiError]): A Result containing a list of user TWAP slice fills.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserTwapSliceFillsRequest(
            type="userTwapSliceFills", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[UserTwapSliceFillsResponse, ApiError], response)

    async def user_rate_limit(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserRateLimitResponse, ApiError]:
        """Retrieve a user's rate limit.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserRateLimitResponse, ApiError]): A Result containing the user rate limit dictionary.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserRateLimitRequest(type="userRateLimit", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[UserRateLimitResponse, ApiError], response)

    async def order_status(
        self,
        *,
        order_id: int | str | Cloid,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[OrderStatusResponse, ApiError]:
        """Retrieve the status of an order.

        POST /info

        Args:
            order_id (int | str | hl.types.Cloid): The order ID as int or the cloid as Cloid or as raw str.
            address (str): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.OrderStatusResponse, ApiError]): A Result containing the status of the order.
        """
        effective_address = self._resolve_address(address, account)
        payload = OrderStatusRequest(
            type="orderStatus",
            user=effective_address,
            oid=order_id.to_raw() if isinstance(order_id, Cloid) else order_id,
        )
        response = await self.transport.invoke(
            payload, [RULE_EXPECT_STATUS_ORDER_STATUS]
        )
        return cast(Result[OrderStatusResponse, ApiError], response)

    async def user_sub_accounts(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[SubAccountsResponse, ApiError]:
        """Retrieve a user's subaccounts.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.SubAccountsResponse, ApiError]): A Result containing a list of subaccounts.
        """
        effective_address = self._resolve_address(address, account)
        payload = SubAccountsRequest(type="subAccounts", user=effective_address)
        result = await self.transport.invoke(payload)
        # NOTE: If no subaccounts are found, the response is null, however, for consistency,
        # we return an empty list
        if result.is_ok():
            response = result.unwrap()
            normalized_response = [] if not response else response
            return Result.ok(cast(SubAccountsResponse, normalized_response))
        else:
            return cast(Result[SubAccountsResponse, ApiError], result)

    async def l2_book(
        self,
        *,
        asset: int | str,
        n_sig_figs: int | None = None,
        mantissa: int | None = None,
    ) -> Result[L2BookResponse, ApiError]:
        """Retrieve L2 book for a given coin.

        POST /info

        Args:
            asset (int | str): Asset ID or name to retrieve the L2 book for.
            n_sig_figs (int | None): Optional field to aggregate levels to nSigFigs significant figures.
                Valid values are 2, 3, 4, 5, and null, which means full precision.
            mantissa (int | None): Optional field to aggregate levels.
                This field is only allowed if nSigFigs is 5. Accepts values of 1, 2 or 5.

        Returns:
            (Result[hl.types.L2BookResponse, ApiError]): A Result containing the L2 book data.
        """
        coin = self.universe.to_asset_name(asset)
        payload = L2BookRequest(
            type="l2Book", coin=coin, nSigFigs=n_sig_figs, mantissa=mantissa
        )
        response = await self.transport.invoke(payload)
        return cast(Result[L2BookResponse, ApiError], response)

    async def candle_snapshot(
        self,
        *,
        asset: int | str,
        interval: CandleInterval,
        start: int | datetime | date,
        end: int | datetime | date | None = None,
    ) -> Result[CandleSnapshotResponse, ApiError]:
        """Retrieve a candle snapshot for a given coin.

        POST /info

        Args:
            asset (int | str): Asset ID or name to retrieve the candle snapshot for.
            interval (str): The interval of the candle snapshot.
            start (int | datetime | date): Start time in milliseconds or a datetime or date object.
            end (int | datetime | date | None): End time in milliseconds or a datetime or date object.
                Will default .

        Returns:
            (Result[hl.types.CandleSnapshotResponse, ApiError]): A Result containing a list of lists of candles.
        """
        payload = CandleSnapshotRequest(
            type="candleSnapshot",
            req=CandleSnapshotRequestPayload(
                coin=self.universe.to_asset_name(asset),
                interval=interval,
                startTime=to_ms(start),
                endTime=to_ms(end) if end else None,
            ),
        )
        response = await self.transport.invoke(payload)
        return cast(Result[CandleSnapshotResponse, ApiError], response)

    async def max_builder_fee(
        self,
        *,
        builder: str,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[MaxBuilderFeeResponse, ApiError]:
        """Retrieve the max builder fee for a given user and builder.

        POST /info

        Args:
            builder (str): Onchain address in 42-character hexadecimal format;
                            e.g. 0x0000000000000000000000000000000000000000.
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
           (Result[hl.types.MaxBuilderFeeResponse, ApiError]): A Result containing maximum builder fee approved in tenths of a basis point i.e. 1 means 0.001%
        """
        effective_address = self._resolve_address(address, account)
        payload = MaxBuilderFeeRequest(
            type="maxBuilderFee", user=effective_address, builder=builder
        )
        response = await self.transport.invoke(payload)
        return cast(Result[MaxBuilderFeeResponse, ApiError], response)

    async def vault_details(
        self,
        *,
        vault_address: str | None = None,
        account: Account | None = None,
    ) -> Result[VaultDetailsResponse, ApiError]:
        """Retrieve vault details for a given user.

        POST /info

        Args:
            vault_address (str | None): Vault address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request must have vault address set (mutually exclusive with vault_address)

        Returns:
            (Result[hl.types.VaultDetailsResponse, ApiError]): A Result containing the vault details dictionary.
        """
        vault_address = self._resolve_vault_address(vault_address, account)
        payload = VaultDetailsRequest(
            type="vaultDetails",
            vaultAddress=vault_address,
        )
        response = await self.transport.invoke(payload)
        return cast(Result[VaultDetailsResponse, ApiError], response)

    async def user_vault_equities(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserVaultEquitiesResponse, ApiError]:
        """Retrieve a user's vault equities.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserVaultEquitiesResponse, ApiError]): A Result containing a list of user vault equities.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserVaultEquitiesRequest(
            type="userVaultEquities", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[UserVaultEquitiesResponse, ApiError], response)

    async def user_role(
        self,
        *,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[UserRoleResponse, ApiError]:
        """Retrieve a user's role.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserRoleResponse, ApiError]): A Result containing the user role.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserRoleRequest(type="userRole", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[UserRoleResponse, ApiError], response)

    async def user_portfolio(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[PortfolioResponse, ApiError]:
        """Retrieve a user's portfolio.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.PortfolioResponse, ApiError]): A Result containing the user's portfolio.
        """
        effective_address = self._resolve_address(address, account)
        payload = PortfolioRequest(type="portfolio", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[PortfolioResponse, ApiError], response)

    async def user_referral(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[ReferralResponse, ApiError]:
        """Retrieve a user's referral.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.ReferralResponse, ApiError]): A Result containing the user's referral.
        """
        effective_address = self._resolve_address(address, account)
        payload = ReferralRequest(type="referral", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[ReferralResponse, ApiError], response)

    async def user_fees(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserFeesResponse, ApiError]:
        """Retrieve a user's fees.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserFeesResponse, ApiError]): A Result containing the user's fees.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserFeesRequest(type="userFees", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[UserFeesResponse, ApiError], response)

    async def user_delegations(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[DelegationsResponse, ApiError]:
        """Retrieve a user's delegations.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.DelegationsResponse, ApiError]): A Result containing the user's delegations.
        """
        effective_address = self._resolve_address(address, account)
        payload = DelegationsRequest(type="delegations", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[DelegationsResponse, ApiError], response)

    async def user_delegator_summary(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[DelegatorSummaryResponse, ApiError]:
        """Retrieve a user's delegator summary.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.DelegatorSummaryResponse, ApiError]): A Result containing the user's delegator summary.
        """
        effective_address = self._resolve_address(address, account)
        payload = DelegatorSummaryRequest(
            type="delegatorSummary", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[DelegatorSummaryResponse, ApiError], response)

    async def user_delegator_history(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[DelegatorHistoryResponse, ApiError]:
        """Retrieve a user's delegator history.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.DelegatorHistoryResponse, ApiError]): A Result containing the user's delegator history.
        """
        effective_address = self._resolve_address(address, account)
        payload = DelegatorHistoryRequest(
            type="delegatorHistory", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[DelegatorHistoryResponse, ApiError], response)

    async def user_delegator_rewards(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[DelegatorRewardsResponse, ApiError]:
        """Retrieve a user's delegator rewards.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.DelegatorRewardsResponse, ApiError]): A Result containing the user's delegator rewards.
        """
        # TODO: Should we really resolve the address here?
        # Delegator rewards are not typically associated with a specific account.
        effective_address = self._resolve_address(address, account)
        payload = DelegatorRewardsRequest(
            type="delegatorRewards", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[DelegatorRewardsResponse, ApiError], response)

    ##############
    # Perpetuals #
    ##############

    async def perpetual_dexs(self) -> Result[PerpDexsResponse, ApiError]:
        """Retrieve perpetual dexs.

        POST /info

        Returns:
            (Result[hl.types.PerpDexsResponse, ApiError]): A Result containing the perpetual dexs.
        """
        payload = PerpDexsRequest(type="perpDexs")
        response = await self.transport.invoke(payload)
        return cast(Result[PerpDexsResponse, ApiError], response)

    async def perpetual_meta(self) -> Result[MetaResponse, ApiError]:
        """Retrieve exchange perpetuals metadata.

        POST /info

        Returns:
            (Result[hl.types.MetaResponse, ApiError]): A Result containing the metadata dictionary for perpetual assets.
        """
        payload = MetaRequest(type="meta")
        response = await self.transport.invoke(payload)
        return cast(Result[MetaResponse, ApiError], response)

    async def perpetual_meta_and_asset_ctxs(
        self,
    ) -> Result[MetaAndAssetCtxsResponse, ApiError]:
        """Retrieve exchange perpetuals metadata and asset context.

        POST /info

        Returns:
            (Result[hl.types.MetaAndAssetCtxsResponse, ApiError]): A Result containing a tuple of the metadata dictionary and a list of asset contexts for perpetual assets.
        """
        payload = MetaAndAssetCtxsRequest(type="metaAndAssetCtxs")
        response = await self.transport.invoke(payload)
        return cast(Result[MetaAndAssetCtxsResponse, ApiError], response)

    async def user_state(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[UserStateResponse, ApiError]:
        """Retrieve trading details about a user.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserStateResponse, ApiError]): A Result containing the user state dictionary.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserStateRequest(type="clearinghouseState", user=effective_address)
        response = await self.transport.invoke(payload)
        return cast(Result[UserStateResponse, ApiError], response)

    async def user_funding(
        self,
        *,
        start: int | datetime | date,
        end: int | datetime | date | None = None,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[UserFundingResponse, ApiError]:
        """Retrieve a user's funding history.

        POST /info

        Args:
            start (int | datetime | date): Start time in milliseconds or a datetime or date object.
            end (int | datetime | date | None): End time in milliseconds or a datetime or date object.
                Will default to the current time.
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserFundingResponse, ApiError]): A Result containing a list of user funding history entries.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserFundingRequest(
            type="userFunding",
            user=effective_address,
            startTime=to_ms(start),
        )
        if end is not None:
            payload["endTime"] = to_ms(end, time_mode="max")
        response = await self.transport.invoke(payload)
        return cast(Result[UserFundingResponse, ApiError], response)

    async def user_non_funding_ledger_updates(
        self,
        *,
        start: int | datetime | date,
        end: int | datetime | date | None = None,
        address: str | None = None,
        account: Account | None = None,
    ) -> Result[UserNonFundingLedgerUpdatesResponse, ApiError]:
        """Retrieve a user's non-funding ledger updates.

        Note: Non-funding ledger updates include deposits, transfers, and withdrawals.

        POST /info

        Args:
            start (int | datetime | date): Start time in milliseconds or a datetime or date object.
            end (int | datetime | date | None): End time in milliseconds or a datetime or date object.
                Will default to the current time.
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.UserNonFundingLedgerUpdatesResponse, ApiError]): A Result containing a list of user funding history entries.
        """
        effective_address = self._resolve_address(address, account)
        payload = UserNonFundingLedgerUpdatesRequest(
            type="userNonFundingLedgerUpdates",
            user=effective_address,
            startTime=to_ms(start),
        )
        if end is not None:
            payload["endTime"] = to_ms(end, time_mode="max")
        response = await self.transport.invoke(payload)
        return cast(Result[UserNonFundingLedgerUpdatesResponse, ApiError], response)

    async def funding_history(
        self,
        *,
        asset: int | str,
        start: int | datetime | date,
        end: int | datetime | date | None = None,
    ) -> Result[FundingHistoryResponse, ApiError]:
        """Retrieve funding history for a given coin.

        POST /info

        Args:
            asset (int | str): Asset ID or name to retrieve funding history for.
            start (int | datetime | date): Start time in milliseconds or a datetime or date object.
            end (int | datetime | date | None): End time in milliseconds or a datetime or date object.
                Will default to the current time.

        Returns:
            (Result[hl.types.FundingHistoryResponse, ApiError]): A Result containing a list of funding history items.
        """
        payload = FundingHistoryRequest(
            type="fundingHistory",
            coin=self.universe.to_asset_name(asset),
            startTime=to_ms(start),
            endTime=to_ms(end) if end else None,
        )
        response = await self.transport.invoke(payload)
        return cast(Result[FundingHistoryResponse, ApiError], response)

    async def predicted_fundings(self) -> Result[PredictedFundingsResponse, ApiError]:
        """Retrieve predicted fundings for a given coin.

        POST /info

        Returns:
            (Result[hl.types.PredictedFundingsResponse, ApiError]): A Result containing a list of predicted funding items.
        """
        payload = PredictedFundingsRequest(
            type="predictedFundings",
        )
        response = await self.transport.invoke(payload)
        return cast(Result[PredictedFundingsResponse, ApiError], response)

    async def perpetuals_at_open_interest_cap(
        self,
    ) -> Result[PerpsAtOpenInterestCapResponse, ApiError]:
        """Retrieve perpetuals at open interest cap.

        POST /info

        Returns:
            (Result[hl.types.PerpsAtOpenInterestCapResponse, ApiError]): A Result containing a list of perpetuals at open interest cap items.
        """
        payload = PerpsAtOpenInterestCapRequest(type="perpsAtOpenInterestCap")
        response = await self.transport.invoke(payload)
        return cast(Result[PerpsAtOpenInterestCapResponse, ApiError], response)

    async def perpetual_deploy_auction_status(
        self,
    ) -> Result[PerpDeployAuctionStatusResponse, ApiError]:
        """Retrieve perpetual deploy auction status.

        POST /info

        Returns:
            (Result[hl.types.PerpDeployAuctionStatusResponse, ApiError]): A Result containing the perpetual deploy auction status.
        """
        payload = PerpDeployAuctionStatusRequest(type="perpDeployAuctionStatus")
        response = await self.transport.invoke(payload)
        return cast(Result[PerpDeployAuctionStatusResponse, ApiError], response)

    ########
    # SPOT #
    ########

    async def spot_meta(self) -> Result[SpotMetaResponse, ApiError]:
        """Retrieve spot metadata.

        POST /info

        Returns:
            (Result[hl.types.SpotMetaResponse, ApiError]): A Result containing the spot metadata dictionary.
        """
        payload = SpotMetaRequest(type="spotMeta")
        response = await self.transport.invoke(payload)
        return cast(Result[SpotMetaResponse, ApiError], response)

    async def spot_meta_and_asset_ctxs(
        self,
    ) -> Result[SpotMetaAndAssetCtxsResponse, ApiError]:
        """Retrieve spot metadata and asset context.

        POST /info

        Returns:
            (Result[hl.types.SpotMetaAndAssetCtxsResponse, ApiError]): A Result containing a tuple of the spot metadata dictionary and a list of asset contexts for spot assets.
        """
        payload = SpotMetaAndAssetCtxsRequest(type="spotMetaAndAssetCtxs")
        response = await self.transport.invoke(payload)
        return cast(Result[SpotMetaAndAssetCtxsResponse, ApiError], response)

    async def spot_user_state(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[SpotUserStateResponse, ApiError]:
        """Retrieve trading details about a user for spot assets.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.SpotUserStateResponse, ApiError]): A Result containing the user state dictionary for spot assets.
        """
        effective_address = self._resolve_address(address, account)
        payload = SpotUserStateRequest(
            type="spotClearinghouseState", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[SpotUserStateResponse, ApiError], response)

    async def spot_deploy_auction_status(
        self, *, address: str | None = None, account: Account | None = None
    ) -> Result[SpotDeployAuctionStatusResponse, ApiError]:
        """Retrieve spot deploy auction status.

        POST /info

        Args:
            address (str | None): Onchain address in 42-character hexadecimal format (mutually exclusive with account)
            account (Account | None): Account object to use for the request (mutually exclusive with address)

        Returns:
            (Result[hl.types.SpotDeployAuctionStatusResponse, ApiError]): A Result containing the spot deploy auction status.
        """
        effective_address = self._resolve_address(address, account)
        payload = SpotDeployAuctionStatusRequest(
            type="spotDeployState", user=effective_address
        )
        response = await self.transport.invoke(payload)
        return cast(Result[SpotDeployAuctionStatusResponse, ApiError], response)

    async def token_details(
        self, *, token_id: str
    ) -> Result[TokenDetailsResponse, ApiError]:
        """Retrieve token details.

        POST /info

        Args:
            token_id (str): The token onchain ID in 34-character hexadecimal format.

        Returns:
            (Result[hl.types.TokenDetailsResponse, ApiError]): A Result containing the token details.
        """
        payload = TokenDetailsRequest(type="tokenDetails", tokenId=token_id)
        response = await self.transport.invoke(payload)
        return cast(Result[TokenDetailsResponse, ApiError], response)
