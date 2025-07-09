"""Hyperliquid API client library."""

from importlib.metadata import version

from hl import errors, types
from hl.account import Account
from hl.api import Api
from hl.cloid import Cloid
from hl.constants import (
    GROUPING_NA,
    GROUPING_TRIGGER_NORMAL,
    GROUPING_TRIGGER_POSITION,
    LIMIT_ALO,
    LIMIT_GTC,
    LIMIT_IOC,
    SIDE_ASK,
    SIDE_BID,
    TRIGGER_STOP_LOSS,
    TRIGGER_TAKE_PROFIT,
)
from hl.exchange import Exchange
from hl.info import Info
from hl.network import MAINNET, TESTNET
from hl.subscriptions import Subscriptions
from hl.transport import BaseTransport, HttpTransport
from hl.universe import Universe
from hl.ws import Ws
from hl.ws_transport import WsTransport

__version__ = version("hl-sdk")

__all__ = [
    # API
    "Api",
    # Endpoints
    "Account",
    "Info",
    "Exchange",
    "Subscriptions",
    "Ws",
    # Transports
    "HttpTransport",
    "BaseTransport",
    "WsTransport",
    # Types
    "types",
    "errors",
    # Helper Classes
    "Account",
    "Cloid",
    "Universe",
    # Network
    "TESTNET",
    "MAINNET",
    # Constants
    "LIMIT_GTC",
    "LIMIT_IOC",
    "LIMIT_ALO",
    "TRIGGER_TAKE_PROFIT",
    "TRIGGER_STOP_LOSS",
    "SIDE_ASK",
    "SIDE_BID",
    "GROUPING_NA",
    "GROUPING_TRIGGER_NORMAL",
    "GROUPING_TRIGGER_POSITION",
]
