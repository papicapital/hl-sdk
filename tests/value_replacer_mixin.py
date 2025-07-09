import copy
from contextlib import contextmanager
from typing import Any, Generator


class ValueReplacerMixin:
    """Mixin that provides value replacement functionality for nested data structures.

    This mixin allows replacing values in nested dictionaries and lists using dot notation
    with support for numeric indices for list access.

    Examples:
        - "user.name" -> obj["user"]["name"]
        - "items.0.price" -> obj["items"][0]["price"]
        - "0.user" -> obj[0]["user"]
    """

    def __init__(self) -> None:
        """Initialize the mixin with empty replacement dictionaries."""
        self._request_replacements: dict[str, Any] = {}
        self._response_replacements: dict[str, Any] = {}

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a value from a nested dictionary/list using dot notation.

        Args:
            obj: The object to traverse
            path: Dot-separated path, with numeric indices for list access

        Returns:
            The value at the path, or None if not found
        """
        keys = path.split(".")
        current = obj

        for key in keys:
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    return None
            elif isinstance(current, list):
                # Try to parse key as integer for list access
                try:
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    # Key is not a valid integer
                    return None
            else:
                # Current is neither dict nor list
                return None

        return current

    def _set_nested_value(self, obj: Any, path: str, value: Any) -> None:
        """Set a value in a nested dictionary/list using dot notation.

        Args:
            obj: The object to modify
            path: Dot-separated path, with numeric indices for list access
            value: The value to set
        """
        keys = path.split(".")
        current = obj

        # Navigate to the parent of the target key
        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if key not in current:
                    # Determine if next key is numeric to create list or dict
                    next_key = keys[i + 1]
                    try:
                        int(next_key)
                        current[key] = []
                    except ValueError:
                        current[key] = {}
                current = current[key]
            elif isinstance(current, list):
                try:
                    index = int(key)
                    # Extend list if necessary
                    while len(current) <= index:
                        current.append(None)

                    if current[index] is None:
                        # Determine if next key is numeric to create list or dict
                        next_key = keys[i + 1]
                        try:
                            int(next_key)
                            current[index] = []
                        except ValueError:
                            current[index] = {}

                    current = current[index]
                except ValueError:
                    # Can't traverse further with non-numeric key on list
                    return
            else:
                # Can't traverse further
                return

        # Set the final value
        final_key = keys[-1]
        if isinstance(current, dict):
            current[final_key] = value
        elif isinstance(current, list):
            try:
                index = int(final_key)
                # Extend list if necessary
                while len(current) <= index:
                    current.append(None)
                current[index] = value
            except ValueError:
                # Can't set non-numeric key on list
                pass

    def _apply_replacements(self, obj: Any, replacements: dict[str, Any]) -> Any:
        """Apply replacement values to an object using dot notation paths.

        Args:
            obj: The object to apply replacements to
            replacements: Dict mapping dot-notated paths to replacement values

        Returns:
            A deep copy of the object with replacements applied
        """
        if not replacements:
            return obj

        # Deep copy the object to avoid modifying the original
        modified_obj = copy.deepcopy(obj)

        for path, replacement_value in replacements.items():
            self._set_nested_value(modified_obj, path, replacement_value)

        return modified_obj

    @contextmanager
    def replace_values(
        self,
        request: dict[str, Any] | None = None,
        response: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        """Context manager for replacing dynamic values in captured interactions.

        Args:
            request: Dict mapping dot-notated paths to replacement values for request payload
            response: Dict mapping dot-notated paths to replacement values for response payload

        Usage:
            with transport.replace_values(
                request={"action.time": 1750180760107, "items.0.id": "fixed-id"},
                response={"data.0.timestamp": 1750180760107}
            ):
                response = await transport.invoke({"action": {"type": "order", "time": 123}})
        """
        # Store previous replacement values
        old_request_replacements = self._request_replacements
        old_response_replacements = getattr(self, "_response_replacements", {})

        # Set new replacement values
        self._request_replacements = request or {}
        if hasattr(self, "_response_replacements"):
            self._response_replacements = response or {}

        try:
            yield
        finally:
            # Restore previous replacement values
            self._request_replacements = old_request_replacements
            if hasattr(self, "_response_replacements"):
                self._response_replacements = old_response_replacements
