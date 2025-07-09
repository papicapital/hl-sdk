import os
from contextlib import _GeneratorContextManager, contextmanager
from typing import Any, Callable, Generator, Protocol, TypeAlias
from unittest.mock import patch

import pytest

from hl.transport import BaseTransport
from tests.mock_http_transport import MockHttpTransport
from tests.mock_ws_transport import MockWsTransport


class ReplaceValues(Protocol):
    """Context manager for replacing dynamic values in captured interactions."""

    @contextmanager
    def __call__(
        self,
        transport: BaseTransport,
        *,
        request: dict[str, Any] | None = None,
        response: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        """Context manager for replacing dynamic values in captured interactions."""
        ...


@pytest.fixture(scope="function")
def replace_values() -> ReplaceValues:
    @contextmanager
    def _replace_values(
        transport: BaseTransport,
        *,
        request: dict[str, Any] | None = None,
        response: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        if not isinstance(transport, MockHttpTransport) and not isinstance(
            transport, MockWsTransport
        ):
            raise ValueError("Transport must be a MockHttpTransport or MockWsTransport")
        with transport.replace_values(
            request=request,
            response=response,
        ):
            yield

    return _replace_values


# Patch the weakref.finalize to prevent "Event loop is closed" errors
@pytest.fixture(scope="session", autouse=True)
def patch_httpx_cleanup() -> Generator[None, None, None]:
    """Patch httpx client cleanup to prevent 'Event loop is closed' errors."""
    # Keep a reference to the original finalize function
    import weakref

    original_finalize = weakref.finalize

    # Replace the weakref.finalize with a no-op function for httpx clients
    with patch("weakref.finalize") as mock_finalize:
        # When finalize is called for httpx cleanup, return a no-op callback
        def side_effect(*args: Any, **kwargs: Any) -> Any:
            # Check if this is a call to finalize an httpx client
            if args and hasattr(args[0], "aclose"):
                # Return a mock finalizer that does nothing
                class MockFinalizer:
                    def detach(self) -> None:
                        return None

                return MockFinalizer()
            # Otherwise, call the real finalize function
            return original_finalize(*args, **kwargs)

        # Set our side effect
        mock_finalize.side_effect = side_effect
        yield
