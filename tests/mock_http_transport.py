import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Callable, Optional

from hl import BaseTransport
from hl.errors import ApiError
from hl.result import Result
from hl.types import Network
from hl.validator import Rule
from .value_replacer_mixin import ValueReplacerMixin


class MockHttpTransportError(Exception):
    """Exception raised when MockHttpTransport is used incorrectly."""

    pass


class MockHttpTransport(BaseTransport, ValueReplacerMixin):
    """Mock transport that can capture and replay HTTP requests.

    This transport wraps another transport instance and provides the ability to
    automatically capture requests and responses to fixtures named after the test
    function, and replay captured responses from existing fixtures.

    The transport operates in two modes:
    - **Capture mode**: When a fixture doesn't exist, requests are passed through to the
      wrapped transport and responses are captured for later replay
    - **Replay mode**: When a fixture exists, requests are matched sequentially against captured
      requests and cached responses are returned. Strict validation ensures requests match
      exactly and in the same order as captured.

    Fixture names are automatically inferred from the callstack in the format:
    {module_name}-{test_function_name}.json

    Usage:
        >>> # Create a mock transport wrapping a real transport
        >>> real_transport = HttpTransport("https://api.hyperliquid-testnet.xyz", "info")
        >>> mock = MockHttpTransport(real_transport, fixture_dir="tests/fixtures")
        >>>
        >>> # Start capturing/replaying
        >>> mock.start()
        >>>
        >>> # Make requests - fixture name is automatically inferred
        >>> # If called from test_info.py::test_all_mids, fixture will be test_info-test_all_mids.json
        >>> response = await mock.invoke({"type": "allMids"})
        >>>
        >>> # Stop and save any captured fixtures
        >>> mock.stop()
    """

    def __init__(
        self, wrapped_transport: BaseTransport, fixture_dir: str = "tests/fixtures/http"
    ):
        """Initialize the mock transport.

        Args:
            wrapped_transport: The real transport instance to wrap
            fixture_dir: Directory where fixture files will be stored
        """
        self.wrapped_transport = wrapped_transport

        # Initialize ValueReplacerMixin
        ValueReplacerMixin.__init__(self)

        self.fixture_dir = Path(fixture_dir)
        self.fixture_dir.mkdir(parents=True, exist_ok=True)

        # State for current capture session
        self._is_started = False
        self._current_fixture_name: Optional[str] = None
        self._captured_interactions: list[dict[str, Any]] = []

        # State for replay mode
        self._is_replay_mode = False
        self._fixture_interactions: list[dict[str, Any]] = []
        self._current_interaction_index = 0
        self._invoke_count = 0

        # State for value replacements is handled by the mixin

    @property
    def network(self) -> Network:
        """Get the network of the wrapped transport."""
        return self.wrapped_transport.network

    @network.setter
    def network(self, network: Network) -> None:
        self.wrapped_transport.network = network

    def _serialize_error(self, error: ApiError) -> dict[str, Any]:
        """Serialize an ApiError to a dict with import path and kwargs."""
        # Get the full import path of the error class
        error_class = error.__class__
        import_path = f"{error_class.__module__}.{error_class.__qualname__}"

        # Extract constructor arguments from the error instance
        # We need to map the error's attributes back to constructor parameters
        kwargs = {}

        # Get the constructor signature to know what parameters to extract
        sig = inspect.signature(error_class.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Try to get the attribute from the error instance
            if hasattr(error, param_name):
                kwargs[param_name] = getattr(error, param_name)

        return {"import_path": import_path, "kwargs": kwargs}

    def _deserialize_error(self, error_dict: dict[str, Any]) -> ApiError:
        """Deserialize an error dict back to an ApiError instance."""
        import_path = error_dict["import_path"]
        kwargs = error_dict["kwargs"]

        # Split the import path to get module and class name
        module_path, class_name = import_path.rsplit(".", 1)

        # Import the module and get the class
        module = importlib.import_module(module_path)
        error_class = getattr(module, class_name)

        # Create the error instance with the stored kwargs
        return error_class(**kwargs)  # type: ignore

    def _serialize_result(self, result: Result[Any, ApiError]) -> dict[str, Any]:
        """Serialize a Result object to a dict."""
        if result.is_ok():
            return {"type": "ok", "value": result.unwrap()}
        else:
            return {"type": "err", "error": self._serialize_error(result.unwrap_err())}

    def _deserialize_result(self, result_dict: dict[str, Any]) -> Result[Any, ApiError]:
        """Deserialize a result dict back to a Result object."""
        if result_dict["type"] == "ok":
            return Result.ok(result_dict["value"])
        else:
            error = self._deserialize_error(result_dict["error"])
            return Result.err(error)

    def start(self) -> None:
        """Start capturing/replaying requests.

        The fixture name is automatically inferred from the callstack.
        """
        if self._is_started:
            raise MockHttpTransportError("MockHttpTransport is already started")

        self._current_fixture_name = self._get_fixture_name_from_callstack()
        if not self._current_fixture_name:
            raise MockHttpTransportError("Could not infer fixture name from callstack")

        # Check if we're in replay mode (fixture exists)
        fixture_path = self._get_fixture_path(self._current_fixture_name)
        if fixture_path.exists():
            self._setup_replay_mode(fixture_path)
        else:
            self._setup_capture_mode()

        self._is_started = True

    def _setup_replay_mode(self, fixture_path: Path) -> None:
        """Setup replay mode by loading fixture interactions."""
        try:
            with open(fixture_path, "r") as f:
                fixture_data = json.load(f)

            self._fixture_interactions = fixture_data.get("interactions", [])
            self._is_replay_mode = True
            self._current_interaction_index = 0
            self._invoke_count = 0

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            raise MockHttpTransportError(f"Failed to load fixture {fixture_path}: {e}")

    def _setup_capture_mode(self) -> None:
        """Setup capture mode for new fixtures."""
        self._captured_interactions = []
        self._is_replay_mode = False
        self._invoke_count = 0

    def stop(self) -> None:
        """Stop capturing and save any captured interactions to fixture file.

        In replay mode, validates that the expected number of invokes occurred.
        """
        if not self._is_started:
            raise MockHttpTransportError("MockHttpTransport is not started")

        if self._is_replay_mode:
            # Validate that we made the expected number of invokes
            expected_count = len(self._fixture_interactions)
            if self._invoke_count != expected_count:
                raise MockHttpTransportError(
                    f"Expected {expected_count} invokes but got {self._invoke_count} "
                    f"for fixture {self._current_fixture_name}"
                )
        else:
            # Save fixtures if we have any captured interactions
            if self._captured_interactions and self._current_fixture_name:
                fixture_path = self._get_fixture_path(self._current_fixture_name)

                # Only save if fixture doesn't exist yet
                if not fixture_path.exists():
                    fixture_data = {
                        "fixture_name": self._current_fixture_name,
                        "interactions": self._captured_interactions,
                    }

                    with open(fixture_path, "w") as f:
                        json.dump(fixture_data, f, indent=2)

        # Reset state
        self._is_started = False
        self._current_fixture_name = None
        self._captured_interactions = []
        self._is_replay_mode = False
        self._fixture_interactions = []
        self._current_interaction_index = 0
        self._invoke_count = 0

    def _get_fixture_name_from_callstack(self) -> Optional[str]:
        """Get the fixture name by inspecting the callstack for the test function.

        Returns:
            Fixture name in format {module_name}-{test_function_name} or None if not found
        """
        # Get the current call stack
        stack = inspect.stack()

        # Look for pytest's request object or test node information in the stack
        for frame_info in stack:
            frame = frame_info.frame

            # Check local variables for pytest request object
            if "request" in frame.f_locals:
                request = frame.f_locals["request"]
                if hasattr(request, "node") and hasattr(request.node, "name"):
                    test_name = request.node.name
                    if test_name.startswith("test_"):
                        # Get module name from the request
                        if hasattr(request.node, "module"):
                            module_name = request.node.module.__name__
                            module_basename = module_name.split(".")[-1]
                            return f"{module_basename}-{test_name}"

            # Also check for test items in locals
            if "item" in frame.f_locals:
                item = frame.f_locals["item"]
                if hasattr(item, "name") and item.name.startswith("test_"):
                    if hasattr(item, "module"):
                        module_name = item.module.__name__
                        module_basename = module_name.split(".")[-1]
                        return f"{module_basename}-{item.name}"

        # Fallback: look for direct test function calls (original approach)
        for frame_info in stack:
            func_name = frame_info.function
            module_name = frame_info.frame.f_globals.get("__name__", "")

            # Check if this is a test function
            if func_name.startswith("test_") and module_name:
                # Extract just the module name (e.g., 'test_info' from 'tests.test_info')
                module_basename = module_name.split(".")[-1]
                return f"{module_basename}-{func_name}"

        return None

    async def invoke(
        self, payload: Any, validators: list[Rule] | None = None
    ) -> Result[Any, ApiError]:
        """Invoke the transport with the given payload.

        In replay mode, matches requests sequentially and validates they match exactly.
        In capture mode, passes through to wrapped transport and captures responses.

        Args:
            payload: The request payload to send
            validators: Optional list of validation functions (used in capture mode only)

        Returns:
            The response from either the fixture or the wrapped transport

        Raises:
            MockHttpTransportError: If called before start() or after stop(), or if
                               replay validation fails
        """
        if not self._is_started:
            raise MockHttpTransportError(
                "MockHttpTransport must be started before invoking. Call start() first."
            )

        if payload is None:
            payload = {}

        if not self._current_fixture_name:
            raise MockHttpTransportError("No fixture name available")

        self._invoke_count += 1

        if self._is_replay_mode:
            return self._handle_replay_invoke(payload)
        else:
            return await self._handle_capture_invoke(payload, validators)

    def _handle_replay_invoke(self, payload: Any) -> Result[Any, ApiError]:
        """Handle invoke in replay mode with strict sequential validation."""
        if self._current_interaction_index >= len(self._fixture_interactions):
            raise MockHttpTransportError(
                f"Too many invokes for fixture {self._current_fixture_name}. "
                f"Expected {len(self._fixture_interactions)} but this is invoke #{self._invoke_count}"
            )

        expected_interaction = self._fixture_interactions[
            self._current_interaction_index
        ]

        # Apply replacements to the incoming payload before comparison
        # This ensures the payload is normalized the same way as when it was captured
        replaced_payload = self._apply_replacements(payload, self._request_replacements)
        normalized_payload = self._normalize_payload(replaced_payload)

        # Get the expected normalized payload from the fixture
        expected_normalized = expected_interaction.get("normalized_payload")
        if expected_normalized is None:
            raise MockHttpTransportError(
                f"Fixture {self._current_fixture_name} is missing 'normalized_payload' field. "
                f"Please regenerate the fixture."
            )

        # Apply the same replacements to the expected fixture data for fair comparison
        # This allows replace_values to work correctly by normalizing both sides
        expected_with_replacements = self._apply_replacements(
            expected_normalized, self._request_replacements
        )
        expected_final = self._normalize_payload(expected_with_replacements)

        if normalized_payload != expected_final:
            raise MockHttpTransportError(
                f"Request mismatch for fixture {self._current_fixture_name} at invoke #{self._invoke_count}. "
                f"Expected: {expected_final}, Got: {normalized_payload}"
            )

        result_data = expected_interaction["result"]
        result = self._deserialize_result(result_data)
        if result.is_ok():
            result = Result.ok(
                self._apply_replacements(result.unwrap(), self._response_replacements)
            )

        self._current_interaction_index += 1
        return result

    async def _handle_capture_invoke(
        self, payload: Any, validators: list[Rule] | None = None
    ) -> Result[Any, ApiError]:
        """Handle invoke in capture mode."""
        # Make real API call - this now returns Result[Any, ApiError]
        result = await self.wrapped_transport.invoke(payload, validators)

        # Apply replacements to payload
        captured_payload = self._apply_replacements(payload, self._request_replacements)
        captured_normalized_payload = self._normalize_payload(captured_payload)

        # Apply replacements to result before serializing
        if result.is_ok():
            captured_response = self._apply_replacements(
                result.unwrap(), self._response_replacements
            )
            captured_result: Result[Any, ApiError] = Result.ok(captured_response)
        else:
            # For errors, we don't typically apply response replacements
            # but we could if needed
            captured_result = result

        # Serialize the result
        serialized_result = self._serialize_result(captured_result)

        # Capture the interaction
        interaction = {
            "normalized_payload": captured_normalized_payload,
            "result": serialized_result,
        }
        self._captured_interactions.append(interaction)

        return result

    def _get_fixture_path(self, fixture_name: str) -> Path:
        """Get the path to a fixture file."""
        # Sanitize fixture name for filesystem
        safe_name = fixture_name.replace(":", "_")
        return self.fixture_dir / f"{safe_name}.json"

    def _normalize_payload(self, payload: Any) -> Any:
        """Normalize payload for matching by removing or standardizing dynamic fields."""
        if not isinstance(payload, dict):
            return payload

        # For exchange endpoints, only match on the action, ignore dynamic fields
        if "action" in payload:
            normalized = {"action": payload.get("action")}
            # Keep vaultAddress as it's part of the logical request
            if "vaultAddress" in payload:
                normalized["vaultAddress"] = payload["vaultAddress"]
            return normalized
        else:
            # For info endpoints, use the full payload as it's typically static
            return payload
