from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

__all__ = ["Result"]

T = TypeVar("T")  # success value type
E = TypeVar("E", bound=BaseException)  # error type
U = TypeVar("U")  # new success value type after map
F = TypeVar("F", bound=BaseException)  # new error type after map_err


@dataclass(frozen=True, slots=True)
class Result(Generic[T, E]):
    """A minimal Rust-style Result monad."""

    _value: T | None = None
    _error: E | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Create a *success* result."""
        return cls(_value=value)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """Create a *failure* result."""
        return cls(_error=error)

    def is_ok(self) -> bool:
        """Return *True* if the result is Ok."""
        return self._error is None

    def is_err(self) -> bool:
        """Return *True* if the result is Err."""
        return self._error is not None

    def unwrap(self) -> T:
        """Return the contained *Ok* value or raise the *Err* exception."""
        if self.is_err():
            assert self._error is not None  # Type narrowing
            raise self._error
        return self._value  # type: ignore

    def unwrap_err(self) -> E:
        """Return the contained *Err* or raise if *Ok*."""
        if self.is_ok():
            raise RuntimeError("Called unwrap_err() on an Ok value")
        assert self._error is not None  # Type narrowing
        return self._error

    def expect(self, msg: str) -> T:
        """Return the *Ok* value or raise *RuntimeError* with *msg*."""
        if self.is_err():
            assert self._error is not None  # Type narrowing
            raise RuntimeError(msg) from self._error
        return self._value  # type: ignore

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        """Apply *fn* to the contained value if *Ok*, otherwise propagate *Err*."""
        if self.is_ok():
            return Result.ok(fn(self._value))  # type: ignore
        assert self._error is not None  # Type narrowing
        return Result.err(self._error)

    def map_err(self, fn: Callable[[E], F]) -> "Result[T, F]":
        """Apply *fn* to the contained error if *Err*, otherwise propagate value."""
        if self.is_err():
            assert self._error is not None  # Type narrowing
            return Result.err(fn(self._error))
        return Result.ok(self._value)  # type: ignore

    @staticmethod
    async def wrap(awaitable: Awaitable[T]) -> "Result[T, BaseException]":
        """Convert *awaitable* into *Result* capturing any exception."""
        try:
            value = await awaitable
            return Result.ok(value)
        except BaseException as exc:
            return Result.err(exc)

    def __repr__(self) -> str:
        """Return a string representation of the result."""
        if self.is_ok():
            return f"Ok({self._value!r})"
        return f"Err({self._error!r})"
