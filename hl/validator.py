from __future__ import annotations

"""Centralised response validation rules.

Each rule receives the *path* (e.g. "/exchange/" or "/info/") and the parsed
JSON *payload* (or ``None`` if the body is empty) and may raise an
:pyclass:`hl.errors.ApiError` subtype.
"""

from typing import Any, Literal, Protocol, runtime_checkable

from hl.errors import ApiError, NotFoundError, StatusError, UnexpectedSchemaError

Json = dict[str, Any] | None


@runtime_checkable
class Rule(Protocol):
    """Validate *payload* for *path* or raise."""

    def __call__(
        self, endpoint: Literal["info", "exchange"], body: Json
    ) -> ApiError | None:
        """Validate *body* for *path* or raise."""
        pass


def RULE_INFO_NOT_FOUND(
    endpoint: Literal["info", "exchange"], body: Json
) -> ApiError | None:
    """Validate `/info` responses.

    * Empty / null → error.
    """
    if endpoint == "info":
        if body is None:
            return NotFoundError(message="Empty info response")
    return None


def RULE_EXCHANGE_ACTION_ERROR(
    endpoint: Literal["info", "exchange"], body: Json
) -> ApiError | None:
    """Validate `/exchange` responses.

    * Not a dict → error.
    * No `status` key → error.
    * `status != "ok"` → error.
    """
    if endpoint == "exchange":
        if not isinstance(body, dict):
            return UnexpectedSchemaError(
                message=f"Expected body to be of type dict: {body}",
                body=body,
            )
        if "status" not in body:
            return UnexpectedSchemaError(
                message=f"Expected body to contain 'status' key: {body}",
                body=body,
            )
        if body["status"] != "ok":
            return StatusError(
                message=f"status={body['status']} body={body}",
                expected="ok",
                actual=body["status"],
                body=body,
            )
    return None


def RULE_EXPECT_DICT(
    endpoint: Literal["info", "exchange"], body: Json
) -> ApiError | None:
    """Validate `/info` and `/exchange` responses.

    * Not a dict → error.
    """
    if not isinstance(body, dict):
        return UnexpectedSchemaError(
            message=f"Expected body to be of type dict: {body}",
            body=body,
        )
    return None


def RULE_EXPECT_LIST(
    endpoint: Literal["info", "exchange"], body: Json
) -> ApiError | None:
    """Validate `/info` and `/exchange` responses.

    * Not a list → error.
    """
    if not isinstance(body, list):
        return UnexpectedSchemaError(
            message=f"Expected body to be of type list: {body}",
            body=body,
        )
    return None


def RULE_EXPECT_STATUS_ORDER_STATUS(
    endpoint: Literal["info", "exchange"], body: Json
) -> ApiError | None:
    """Validate `/info` responses.

    * Not a dict → error.
    * Status not "order" → error.
    """
    if endpoint == "info":
        if not isinstance(body, dict):
            return UnexpectedSchemaError(
                message=f"Expected body to be of type dict: {body}",
                body=body,
            )
        if "status" not in body:
            return UnexpectedSchemaError(
                message=f"Expected body to contain 'status' key: {body}",
                body=body,
            )
        if body["status"] != "order":
            return StatusError(
                message=f"Expected status 'order' but got '{body['status']}'",
                expected="order",
                actual=body["status"],
                body=body,
            )
    return None


BASE_RULES: list[Rule] = [RULE_INFO_NOT_FOUND, RULE_EXCHANGE_ACTION_ERROR]
"""Base rules that are always applied to validation."""
