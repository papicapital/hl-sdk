import asyncio

from hl.account import Account
from hl.types import (
    ActiveAssetCtxMsg,
    ActiveAssetCtxSubscription,
    ActiveAssetDataMsg,
    ActiveAssetDataSubscription,
    AllMidsMsg,
    AllMidsSubscription,
    BestBidOfferMsg,
    BestBidOfferSubscription,
    CandleInterval,
    CandleMsg,
    CandleSubscription,
    L2BookMsg,
    L2BookSubscription,
    NotificationMsg,
    NotificationSubscription,
    OrderUpdatesMsg,
    OrderUpdatesSubscription,
    TradesMsg,
    TradesSubscription,
    UserEventsMsg,
    UserEventsSubscription,
    UserFillsMsg,
    UserFillsSubscription,
    UserFundingsMsg,
    UserFundingsSubscription,
    UserNonFundingLedgerUpdatesMsg,
    UserNonFundingLedgerUpdatesSubscription,
    UserTwapHistoryMsg,
    UserTwapHistorySubscription,
    UserTwapSliceFillsMsg,
    UserTwapSliceFillsSubscription,
    WebData2Msg,
    WebData2Subscription,
)
from hl.universe import Universe
from hl.ws_transport import WsTransport


class Subscriptions:
    """The Subscriptions class provides methods to interact with the subscriptions endpoint."""

    def __init__(
        self,
        *,
        transport: WsTransport,
        universe: Universe | None = None,
        account: Account | None = None,
    ):
        """Initialize the Subscriptions class with the given transport.

        Args:
            transport: The WebSocket transport to use for subscriptions.
            universe: The universe to use for asset name resolution.
            account: The default account to use for authenticated subscriptions.
        """
        self.transport = transport
        self.universe = universe
        self.account = account

    def _resolve_address(
        self, address: str | None = None, account: "Account | None" = None
    ) -> str:
        """Resolve the effective address from the provided parameters."""
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
            raise ValueError("No account or address provided.")

    async def all_mids(
        self, *, queue: asyncio.Queue[AllMidsMsg] | None = None
    ) -> tuple[int, asyncio.Queue[AllMidsMsg]]:
        """Subscribe to all mids updates.

        Args:
            queue: Optional queue to receive messages. If None, a new queue will be created.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        subscription = AllMidsSubscription(type="allMids")
        return await self.transport.subscribe(subscription, queue)

    async def notification(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[NotificationMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[NotificationMsg]]:
        """Subscribe to notifications for a user.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = NotificationSubscription(type="notification", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def web_data2(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[WebData2Msg] | None = None,
    ) -> tuple[int, asyncio.Queue[WebData2Msg]]:
        """Subscribe to web data 2 updates for a user.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = WebData2Subscription(type="webData2", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def candle(
        self,
        *,
        asset: int | str,
        interval: CandleInterval,
        queue: asyncio.Queue[CandleMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[CandleMsg]]:
        """Subscribe to candle updates for a specific asset.

        Args:
            asset: Asset ID or name.
            interval: Candle interval.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = CandleSubscription(type="candle", coin=coin, interval=interval)
        return await self.transport.subscribe(subscription, queue)

    async def l2_book(
        self,
        *,
        asset: int | str,
        n_sig_figs: int | None = None,
        mantissa: int | None = None,
        queue: asyncio.Queue[L2BookMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[L2BookMsg]]:
        """Subscribe to L2 book updates for a specific asset.

        Args:
            asset: Asset ID or name.
            n_sig_figs: Optional number of significant figures.
            mantissa: Optional mantissa.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = L2BookSubscription(type="l2Book", coin=coin)
        if n_sig_figs is not None:
            subscription["nSigFigs"] = n_sig_figs
        if mantissa is not None:
            subscription["mantissa"] = mantissa
        return await self.transport.subscribe(subscription, queue)

    async def trades(
        self,
        *,
        asset: int | str,
        queue: asyncio.Queue[TradesMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[TradesMsg]]:
        """Subscribe to trades for a specific asset.

        Args:
            asset: Asset ID or name.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = TradesSubscription(type="trades", coin=coin)
        return await self.transport.subscribe(subscription, queue)

    async def order_updates(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[OrderUpdatesMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[OrderUpdatesMsg]]:
        """Subscribe to order updates for a user.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = OrderUpdatesSubscription(type="orderUpdates", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def user_events(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[UserEventsMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserEventsMsg]]:
        """Subscribe to user events.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserEventsSubscription(type="userEvents", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def user_fills(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        aggregate_by_time: bool | None = None,
        queue: asyncio.Queue[UserFillsMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserFillsMsg]]:
        """Subscribe to user fills.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            aggregate_by_time: Optional flag to aggregate fills by time.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserFillsSubscription(type="userFills", user=user)
        if aggregate_by_time is not None:
            subscription["aggregateByTime"] = aggregate_by_time
        return await self.transport.subscribe(subscription, queue)

    async def user_fundings(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[UserFundingsMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserFundingsMsg]]:
        """Subscribe to user fundings.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserFundingsSubscription(type="userFundings", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def user_non_funding_ledger_updates(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[UserNonFundingLedgerUpdatesMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserNonFundingLedgerUpdatesMsg]]:
        """Subscribe to user non-funding ledger updates.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserNonFundingLedgerUpdatesSubscription(
            type="userNonFundingLedgerUpdates", user=user
        )
        return await self.transport.subscribe(subscription, queue)

    async def active_asset_ctx(
        self,
        *,
        asset: int | str,
        queue: asyncio.Queue[ActiveAssetCtxMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[ActiveAssetCtxMsg]]:
        """Subscribe to active asset context updates.

        Args:
            asset: Asset ID or name.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = ActiveAssetCtxSubscription(type="activeAssetCtx", coin=coin)
        return await self.transport.subscribe(subscription, queue)

    async def active_asset_data(
        self,
        *,
        asset: int | str,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[ActiveAssetDataMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[ActiveAssetDataMsg]]:
        """Subscribe to active asset data for a user.

        Args:
            asset: Asset ID or name.
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = ActiveAssetDataSubscription(
            type="activeAssetData", user=user, coin=coin
        )
        return await self.transport.subscribe(subscription, queue)

    async def user_twap_slice_fills(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[UserTwapSliceFillsMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserTwapSliceFillsMsg]]:
        """Subscribe to user TWAP slice fills.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserTwapSliceFillsSubscription(
            type="userTwapSliceFills", user=user
        )
        return await self.transport.subscribe(subscription, queue)

    async def user_twap_history(
        self,
        *,
        address: str | None = None,
        account: "Account | None" = None,
        queue: asyncio.Queue[UserTwapHistoryMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[UserTwapHistoryMsg]]:
        """Subscribe to user TWAP history.

        Args:
            address: User address (mutually exclusive with account).
            account: Account object (mutually exclusive with address).
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        user = self._resolve_address(address, account)
        subscription = UserTwapHistorySubscription(type="userTwapHistory", user=user)
        return await self.transport.subscribe(subscription, queue)

    async def best_bid_offer(
        self,
        *,
        asset: int | str,
        queue: asyncio.Queue[BestBidOfferMsg] | None = None,
    ) -> tuple[int, asyncio.Queue[BestBidOfferMsg]]:
        """Subscribe to best bid offer data for a specific asset.

        Args:
            asset: Asset ID or name.
            queue: Optional queue to receive messages.

        Returns:
            tuple[int, asyncio.Queue]: Subscription ID and message queue.
        """
        coin = self.universe.to_asset_name(asset) if self.universe else str(asset)
        subscription = BestBidOfferSubscription(type="bbo", coin=coin)
        return await self.transport.subscribe(subscription, queue)

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe from a subscription.

        Args:
            subscription_id: The subscription ID returned by a subscription method.
        """
        await self.transport.unsubscribe(subscription_id)
