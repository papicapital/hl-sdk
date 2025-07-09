from contextlib import asynccontextmanager
from typing import AsyncGenerator

from hl.account import Account
from hl.exchange import Exchange
from hl.info import Info
from hl.subscriptions import Subscriptions
from hl.types import Network
from hl.universe import Universe
from hl.ws_transport import WsTransport


class Ws:
    """Main WebSocket interface for the Hyperliquid API.

    This class provides a unified interface for WebSocket operations including:
    - Subscriptions via ws.subscriptions
    - Info operations via ws.info
    - Exchange operations via ws.exchange
    - Direct WebSocket management (run, run_forever)
    """

    def __init__(
        self,
        *,
        network: Network,
        universe: Universe,
        account: Account | None = None,
    ) -> None:
        """Initialize the WebSocket interface.

        Args:
            network (hl.types.Network): The network to use.
            universe (hl.universe.Universe | None): The universe to use for the exchange.
            account (hl.account.Account | None): The default account to use for authenticated requests.
        """
        self._transport = WsTransport(network)
        self._universe = universe
        self._account = account

        # Lazy initialization of subscriptions, info, and exchange
        self._subscriptions: Subscriptions | None = None
        self._info: Info | None = None
        self._exchange: Exchange | None = None

    @property
    def universe(self) -> Universe:
        """The universe of assets available on the exchange."""
        return self._universe

    @universe.setter
    def universe(self, universe: Universe) -> None:
        self._universe = universe
        if self._subscriptions:
            self._subscriptions.universe = universe
        if self._info:
            self._info.universe = universe
        if self._exchange:
            self._exchange.universe = universe

    @property
    def account(self) -> Account | None:
        """The default account to use for authenticated requests."""
        return self._account

    @account.setter
    def account(self, account: Account | None) -> None:
        self._account = account
        if self._subscriptions:
            self._subscriptions.account = account
        if self._info:
            self._info.account = account
        if self._exchange:
            self._exchange.account = account

    @property
    def subscriptions(self) -> "Subscriptions":
        """Access subscription methods."""
        if self._subscriptions is None:
            from hl.subscriptions import Subscriptions

            self._subscriptions = Subscriptions(
                transport=self._transport,
                universe=self._universe,
                account=self._account,
            )
        return self._subscriptions

    @property
    def info(self) -> "Info":
        """Access info methods via WebSocket."""
        if self._info is None:
            from hl.info import Info

            self._info = Info(
                transport=self._transport,
                universe=self._universe,
                account=self._account,
            )
        return self._info

    @property
    def exchange(self) -> "Exchange":
        """Access exchange methods via WebSocket."""
        if self._exchange is None:
            from hl.exchange import Exchange

            self._exchange = Exchange(
                transport=self._transport,
                universe=self._universe,
                account=self._account,
            )
        return self._exchange

    # Direct WebSocket management methods
    async def run_forever(self) -> None:
        """Run the websocket manager main loop forever or until it is cancelled.

        The client will connect to the websocket API, continuously receive and process incoming messages,
        and send out outgoing messages.

        It is recommended to use the `run` contextual manager instead of this method since it will automatically
        close the underlying connection once the context exits.

        Examples:
            Run the websocket manager forever:

            >>> await api.ws.run_forever()

            Or run it as a cancellable task:

            >>> task = asyncio.create_task(api.ws.run_forever())
            ... # Do something
            ... sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")
            ... # Cancel the task to shut down the websocket client
            ... task.cancel()
            ... # Optionally, the task can be awaited to wait for it to shut down
            ... await task
        """
        return await self._transport.run_forever()

    @asynccontextmanager
    async def run(self) -> AsyncGenerator[None, None]:
        """Run the websocket client as a task until context exits.

        This is a convenience method that starts the websocket manager and ensures it is properly
        cancelled and cleaned up when the context exits.

        Examples:
            Use the `run` method in combination with the `async with` syntax to run the
            websocket manager and automatically close the underlying connection once the context exits.

            >>> async with api.ws.run():
            ...     # The websocket connection will automatically be closed when the async context manager exits
            ...     sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")
            ...     # Process the next 10 messages
            ...     for _ in range(10):
            ...         msg = await queue.get()
        """
        async with self._transport.run():
            yield
