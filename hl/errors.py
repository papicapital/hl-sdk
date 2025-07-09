from __future__ import annotations

"""Error hierarchy for the Hyperliquid SDK.

This module defines a concise taxonomy that separates different types of API failures:
- HttpError: Network/HTTP-level failures (connection issues, 4xx, 5xx responses)
- NotFoundError: Expected data was not found
- UnexpectedSchemaError: Response structure doesn't match expectations
- StatusError: Status field has unexpected value (e.g. "err" instead of "ok")
"""

from typing import Any

__all__ = [
    "ApiError",
    "HttpError",
    "NotFoundError",
    "UnexpectedSchemaError",
    "StatusError",
]


class ApiError(Exception):
    """Base class for API errors."""

    def __init__(self, message: str, body: Any = None):
        """Initialize an API error.

        Args:
            message (str): The error message.
            body (Any, optional): The response body, if available.
        """
        self.message = message
        self.body = body
        super().__init__(message)


class HttpError(ApiError):
    """HTTP-level failures (network issues, 4xx, 5xx responses).

    Attributes:
        message (str): Error message
        status_code (int): HTTP status code
        headers (dict[str, str]): HTTP headers
        body (Any | None): Error response body, if available
        error_code (str | None): Error code from the response, if available
        error_message (str | None): Error message from the response, if available
        error_data (Any | None): Error data from the response, if available
    """

    def __init__(
        self,
        *,
        message: str,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
        error_data: Any | None = None,
    ):
        """Initialize an HTTP error.

        Args:
            message (str): Error message
            status_code (int): HTTP status code
            headers (dict[str, str] | None): HTTP headers
            body (Any): Error response body, if available
            error_code (str | None): Error code from the response, if available
            error_message (str | None): Error message from the response, if available
            error_data (Any | None): Error data from the response, if available
        """
        super().__init__(message, body)
        self.status_code = status_code
        self.headers = headers or {}
        self.error_code = error_code
        self.error_message = error_message
        self.error_data = error_data


class NotFoundError(ApiError):
    """Expected data was not found."""

    def __init__(self, *, message: str):
        """Initialize a not found error.

        Args:
            message (str): The error message.
        """
        super().__init__(message)


class UnexpectedSchemaError(ApiError):
    """The API returned an unexpected schema.

    For example, the body may contain a list when a dict was expected.
    """

    def __init__(self, *, message: str, body: Any):
        """Initialize an unexpected schema error.

        Args:
            message (str): The error message.
            body (Any): The body of the response.
        """
        super().__init__(message, body)


class StatusError(ApiError):
    """Status field has unexpected value.

    For example, "err" instead of "ok" or "unknownOid" instead of "order".

    Attributes:
        message (str): Error message
        expected (str): The expected status value
        actual (str): The actual status value received
        body (Any | None): The response body
    """

    def __init__(self, *, message: str, expected: str, actual: str, body: Any = None):
        """Initialize a status error.

        Args:
            message (str): The error message.
            expected (str): The expected status value.
            actual (str): The actual status value received.
            body (Any): The response body.
        """
        super().__init__(message, body)
        self.expected = expected
        self.actual = actual
