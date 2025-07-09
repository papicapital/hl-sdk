from typing import Literal

from hl.types import LimitOrderType

LIMIT_GTC = LimitOrderType(type="limit", tif="Gtc")
LIMIT_IOC = LimitOrderType(type="limit", tif="Ioc")
LIMIT_ALO = LimitOrderType(type="limit", tif="Alo")

TRIGGER_TAKE_PROFIT: Literal["tp"] = "tp"
TRIGGER_STOP_LOSS: Literal["sl"] = "sl"

SIDE_ASK: Literal["A"] = "A"
SIDE_BID: Literal["B"] = "B"

GROUPING_NA: Literal["na"] = "na"
GROUPING_TRIGGER_NORMAL: Literal["normalTpsl"] = "normalTpsl"
GROUPING_TRIGGER_POSITION: Literal["positionTpsl"] = "positionTpsl"
