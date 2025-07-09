import json
import logging
import weakref
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Any, Literal

import httpx

from hl.errors import (
    ApiError,
    HttpError,
    UnexpectedSchemaError,
)
from hl.result import Result
from hl.types import Network
from hl.validator import BASE_RULES, Rule

logger = logging.getLogger(__name__)


BASE_HEADERS = {"Content-Type": "application/json", "User-Agent": "hl-sdk"}


class BaseTransport(ABC):
    """Abstract base class for transport implementations.

    BaseTransport defines the interface for all transport mechanisms used to
    communicate with the Hyperliquid API. Transport classes handle the low-level
    details of sending requests and receiving responses, abstracting away the
    underlying communication protocol (HTTP, WebSocket, etc.).

    Note: This is an internal class. Users typically don't interact with transport
    classes directly - they are used internally by Info and Exchange classes.

    Examples:
        Create an API instance and use the HttpTransport to make a request:

        >>> api = await Api.create(address="0x...", secret_key="0x...")
        ... # HttpTransport is used internally by api.info and api.exchange
        ... response = await api.info.all_mids()  # Uses HttpTransport.invoke()
    """

    network: Network

    @abstractmethod
    async def invoke(
        self, payload: Any, validators: list[Rule] | None = None
    ) -> Result[Any, ApiError]:
        """Send a request payload and return the response.

        This is the core method that all transport implementations must provide.
        It handles sending the payload to the appropriate endpoint and returning
        the parsed response, optionally applying validation.

        Args:
            payload (Any): The request payload to send.
            validators (list[Rule] | None): Optional validation functions
                that will be called on successful responses. The validators should
                return the validated/transformed response or raise an exception
                if validation fails. Raised exceptions will be caught and converted
                to Result.err().

        Returns:
            Result[Any, ApiError]: A Result containing either the validated response
                or an error (transport error, HTTP error, or validation error).
        """
        pass


class HttpTransport(BaseTransport):
    """HTTP transport implementation for request-response communication.

    HttpTransport handles communication over HTTP connections using POST requests
    to the Hyperliquid API endpoints. This is the primary transport mechanism for
    most API operations including trading, account management, and data retrieval.

    Note: This is an internal class. Users typically don't create HttpTransport
    instances directly - they are created automatically by the Api class.

    Attributes:
        network: The network to use.
        url: The complete URL for the target endpoint.
        endpoint: The API endpoint to target ("info" or "exchange").
    """

    def __init__(
        self,
        network: Network,
        endpoint: Literal["info", "exchange"],
    ):
        """Initialize an HTTP transport for the specified endpoint.

        Creates an HTTP client configured for optimal communication with the
        Hyperliquid API, including HTTP/2 support and proper headers.

        Args:
            network (hl.network.Network): The network to use.
            endpoint (Literal["info", "exchange"]): The API endpoint to target.

        Note:
            The HTTP client is automatically cleaned up when this transport
            instance is garbage collected, ensuring proper resource management.
        """
        self.network = network
        self.endpoint: Literal["info", "exchange"] = endpoint
        self.url = f"{network['api_url']}/{endpoint}"
        self._http_client = httpx.AsyncClient(headers=BASE_HEADERS, http2=True)

        # Register cleanup when THIS transport object is garbage collected
        def _cleanup(http_client: httpx.AsyncClient) -> None:
            """Clean up the HTTP client when transport is garbage collected."""
            try:
                # Try to close the client properly if there's an event loop
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running event loop, try to get one
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            raise RuntimeError("Event loop is closed")
                    except RuntimeError:
                        # No event loop available, log warning and skip cleanup
                        logger.warning(
                            "HttpTransport garbage collected but unable to close HTTP client properly "
                            "(no event loop available). This may leak resources."
                        )
                        return

                # Schedule the coroutine on the event loop
                if loop.is_running():
                    # If loop is running, schedule it
                    asyncio.run_coroutine_threadsafe(http_client.aclose(), loop)
                else:
                    # If loop exists but not running, run it
                    loop.run_until_complete(http_client.aclose())

            except Exception as e:
                logger.warning(f"Error closing HTTP client during cleanup: {e}")

        # Pass the client as an argument to avoid closure issues
        weakref.finalize(self, _cleanup, self._http_client)

    async def invoke(
        self, payload: Any, validators: list[Rule] | None = None
    ) -> Result[Any, ApiError]:
        """Send an HTTP POST request with the given payload.

        Performs a POST request to the configured endpoint with the payload
        serialized as JSON. Handles response parsing and error checking.

        Args:
            payload (Any, optional): The payload to send as JSON. If None,
                                   an empty dictionary will be sent. Defaults to None.
            validators (list[Rule] | None): Optional validation functions
                that will be called on successful responses. The validators should
                return an error if validation fails otherwise return None.
                Returned errors will be converted to Result.err().

        Returns:
            Result[Any, ApiError]: A Result containing either the validated response
                or an error (transport error, HTTP error, or validation error).

        Note:
            If JSON parsing fails, returns an UnexpectedSchemaError.
        """
        if payload is None:
            payload = {}

        try:
            response = await self._http_client.post(self.url, json=payload)
        except httpx.RequestError as e:
            return Result.err(
                HttpError(
                    message=str(e),
                    status_code=0,  # No status code available for request errors
                )
            )

        # Check for HTTP errors and return them as Result.err()
        error = self._handle_exception(response)
        if error:
            return Result.err(error)

        try:
            json_response = response.json()
        except ValueError:
            return Result.err(
                UnexpectedSchemaError(
                    message=f"Could not parse JSON: {response.text}",
                    body=response.text,
                )
            )

        # Apply validation if provided
        for validator in BASE_RULES + (validators or []):
            if error := validator(self.endpoint, json_response):
                return Result.err(error)
        return Result.ok(json_response)

    def _handle_exception(self, response: httpx.Response) -> ApiError | None:
        """Check for HTTP errors and return ApiError instead of raising.

        Returns:
            ApiError if there's an error, None if the response is successful.
        """
        status_code = response.status_code
        if status_code < 400:
            return None

        try:
            err = json.loads(response.text)
        except JSONDecodeError:
            return HttpError(
                message=f"Unable to parse error response: {response.text}",
                status_code=status_code,
                headers=dict(response.headers),
                body=response.text,
                error_code=None,
                error_message=None,
                error_data=None,
            )

        err = err or {}
        if 400 <= status_code < 500:
            return HttpError(
                message=f"Client error: {err.get('msg', 'Unknown client error')}",
                status_code=status_code,
                headers=dict(response.headers),
                body=response.text,
                error_code=err.get("code"),
                error_message=err.get("msg"),
                error_data=err.get("data"),
            )
        else:  # 500+ status codes
            return HttpError(
                message=f"Server error: {err.get('msg', response.text)}",
                status_code=status_code,
                headers=dict(response.headers),
                body=response.text,
                error_code=err.get("code"),
                error_message=err.get("msg"),
                error_data=err.get("data"),
            )
