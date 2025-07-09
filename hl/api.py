from hl.account import Account
from hl.exchange import Exchange
from hl.info import Info
from hl.network import MAINNET
from hl.transport import HttpTransport
from hl.types import Network
from hl.universe import Universe
from hl.ws import Ws


class Api:
    """The Api class provides access to the info, exchange, and ws endpoints.

    Warning: Do not instantiate Api directly. Use Api.create instead.

    Attributes:
        info (hl.info.Info): The info endpoint.
        exchange (hl.exchange.Exchange): The exchange endpoint.
        ws (hl.ws.Ws): The websocket endpoint.
        universe (hl.universe.Universe): The universe of assets available on the exchange.
        account (Account | None): The account to use for authentication.
    """

    def __init__(
        self,
        *,
        info: Info,
        exchange: Exchange,
        ws: Ws,
        universe: Universe,
        account: Account | None = None,
    ) -> None:
        """Warning: Do not instantiate Api directly. Use Api.create instead."""
        self.info = info
        self.exchange = exchange
        self.ws = ws
        self.universe = universe
        self.account = account

    @property
    def universe(self) -> Universe:
        """The universe of assets available on the exchange."""
        return self._universe

    @universe.setter
    def universe(self, universe: Universe) -> None:
        self._universe = universe
        self.exchange.universe = universe
        self.info.universe = universe
        self.ws.universe = universe

    @property
    def account(self) -> Account | None:
        """The account to use for authentication."""
        return self._account

    @account.setter
    def account(self, account: Account | None) -> None:
        self._account = account
        self.exchange.account = account
        self.info.account = account
        self.ws.account = account

    @classmethod
    async def create(
        cls, *, account: Account | None = None, network: Network = MAINNET
    ) -> "Api":
        """Create an Api instance.

        Args:
            account (Account): The account to use for authentication.
            network (Network): The network to use. Defaults to MAINNET.

        Returns:
            (hl.Api): The Api instance.
        """
        info = Info(transport=HttpTransport(network, "info"), account=account)
        universe = await info.get_universe()
        exchange = Exchange(
            transport=HttpTransport(network, "exchange"),
            universe=universe,
            account=account,
        )
        ws = Ws(network=network, universe=universe, account=account)
        return cls(
            info=info, exchange=exchange, ws=ws, universe=universe, account=account
        )
