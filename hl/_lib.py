import asyncio
import functools
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Coroutine, Literal, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def make_sync(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapper


def get_timestamp_ms() -> int:
    return int(time.time() * 1000)


def to_ms(dt: datetime | date | int, time_mode: Literal["min", "max"] = "min") -> int:
    if isinstance(dt, datetime):
        # If datetime is naive (no timezone), interpret it as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    elif isinstance(dt, date):
        # Convert date to UTC-aware datetime using min/max time
        time = datetime.min.time() if time_mode == "min" else datetime.max.time()
        dt_utc = datetime.combine(dt, time).replace(tzinfo=timezone.utc)
        return int(dt_utc.timestamp() * 1000)
    elif isinstance(dt, int):
        return dt
    raise ValueError(f"Invalid type: {type(dt)}")


TOKEN_DECIMAL_PLACES = {"USDC": 6, "HYPE": 8}


def to_minor_unit(amount: Decimal, token: Literal["USDC", "HYPE"]) -> int:
    """Convert major units to minor units of a token.

    Converts a Decimal amount representing major units of a token to an equivalent
    integer amount representing minor units of the same token.
    """
    power = TOKEN_DECIMAL_PLACES[token]
    with_decimals = amount * 10**power
    rounded = int(with_decimals)
    if abs(rounded - with_decimals) >= 1e-3:
        raise ValueError("decimal_to_int causes rounding", amount)
    return rounded
