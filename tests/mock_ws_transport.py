import asyncio
import importlib
import inspect
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from hl.errors import ApiError
from hl.result import Result
from hl.types import Msg, Network, Subscription
from hl.validator import Rule
from hl.ws_transport import WsTransport
from .value_replacer_mixin import ValueReplacerMixin


class MockWsTransportError(Exception):
    """Exception raised when MockWsTransport is used incorrectly."""

    pass


class MockWsTransport(WsTransport, ValueReplacerMixin):
    """Mock WebSocket transport that can capture and replay WebSocket interactions.

    This transport wraps another WsTransport instance and provides the ability to
    automatically capture requests and streaming responses to fixtures named after the test
    function, and replay captured responses from existing fixtures.

    The transport operates in two modes:
    - **Capture mode**: When a fixture doesn't exist, requests are passed through to the
      wrapped transport and responses are captured for later replay (10 seconds by default)
    - **Replay mode**: When a fixture exists, requests are matched and cached responses
      are returned without making real WebSocket connections.

    Key features:
    - Captures both immediate responses (post requests) and streaming data (subscriptions)
    - Automatically captures streaming data for a configurable duration (default 10 seconds)
    - Fixture names are automatically inferred from the callstack
    - Supports all WebSocket operations: subscribe, unsubscribe, post, invoke
    - Configurable message replay timing: can replay with original timing or immediately
    - Supports replacing dynamic values in requests using the replace_values context manager

    Usage:
        >>> # Create a mock transport wrapping a real transport
        >>> real_transport = WsTransport(Network.TESTNET)
        >>> mock = MockWsTransport(real_transport, fixture_dir="tests/fixtures")
        >>>
        >>> # For fast tests without timing delays:
        >>> mock = MockWsTransport(real_transport, replay_with_timing=False)
        >>>
        >>> # Start capturing/replaying
        >>> mock.start()
        >>>
        >>> # Make requests - fixture name is automatically inferred
        >>> async with mock.run():
        >>>     subscription_id, queue = await mock.subscribe({"type": "allMids"})
        >>>     # Messages will be captured for 10 seconds
        >>>
        >>> # Stop and save any captured fixtures
        >>> mock.stop()

    Using replace_values for dynamic data:
        >>> # Replace dynamic timestamps or other values that change between test runs
        >>> mock.start()
        >>> async with mock.run():
        >>>     # Replace timestamps in requests to ensure consistent fixtures
        >>>     with mock.replace_values(request={"action.time": 1750000000000}):
        >>>         # This request will have its time field normalized
        >>>         await mock.invoke({
        >>>             "action": {
        >>>                 "type": "order",
        >>>                 "time": 1234567890123,  # Will be replaced with 1750000000000
        >>>                 "coin": "BTC"
        >>>             }
        >>>         })
        >>>
        >>>     # Works with nested paths and subscriptions too
        >>>     with mock.replace_values(request={"metadata.timestamp": 9999999999}):
        >>>         await mock.subscribe({
        >>>             "type": "userEvents",
        >>>             "metadata": {"timestamp": 1111111111}  # Will be replaced
        >>>         })
        >>> await mock.stop()
    """

    def __init__(
        self,
        wrapped_transport: WsTransport,
        fixture_dir: str = "tests/fixtures/ws",
        capture_duration: float = 10.0,
        replay_with_timing: bool = False,
    ):
        """Initialize the mock WebSocket transport.

        Args:
            wrapped_transport: The real WsTransport instance to wrap
            fixture_dir: Directory where fixture files will be stored
            capture_duration: How long to capture streaming messages in seconds
            replay_with_timing: If True, replay messages with original timing intervals.
                               If False, send all messages immediately.
        """
        self.wrapped_transport = wrapped_transport

        # Initialize parent WsTransport with the same network
        super().__init__(wrapped_transport.network)

        # Initialize ValueReplacerMixin
        ValueReplacerMixin.__init__(self)

        self.fixture_dir = Path(fixture_dir)
        self.fixture_dir.mkdir(parents=True, exist_ok=True)
        self.capture_duration = capture_duration
        self.replay_with_timing = replay_with_timing

        # State for current capture session
        self._is_started = False
        self._current_fixture_name: Optional[str] = None
        self._captured_interactions: list[dict[str, Any]] = []

        # State for replay mode
        self._is_replay_mode = False
        self._fixture_interactions: list[dict[str, Any]] = []
        self._current_interaction_index = 0
        self._invoke_count = 0

        # Subscription tracking
        self._active_subscriptions: dict[int, dict[str, Any]] = {}
        self._subscription_message_queues: dict[int, asyncio.Queue[Any]] = {}
        self._capture_tasks: dict[int, asyncio.Task[Any]] = {}
        self._replay_tasks: dict[int, asyncio.Task[Any]] = {}

        # State for value replacements is handled by the mixin

    @property
    def network(self) -> Network:
        """The network of the wrapped transport."""
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
            raise MockWsTransportError("MockWsTransport is already started")

        self._current_fixture_name = self._get_fixture_name_from_callstack()
        if not self._current_fixture_name:
            raise MockWsTransportError("Could not infer fixture name from callstack")

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
            raise MockWsTransportError(f"Failed to load fixture {fixture_path}: {e}")

    def _setup_capture_mode(self) -> None:
        """Setup capture mode for new fixtures."""
        self._captured_interactions = []
        self._is_replay_mode = False
        self._invoke_count = 0

    async def stop(self) -> None:
        """Stop capturing and save any captured interactions to fixture file."""
        if not self._is_started:
            raise MockWsTransportError("MockWsTransport is not started")

        # Cancel and await any active capture tasks first
        if self._capture_tasks:
            for task in self._capture_tasks.values():
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete cancellation
            await asyncio.gather(*self._capture_tasks.values(), return_exceptions=True)
            self._capture_tasks.clear()

        # Cancel and await any active replay tasks
        if self._replay_tasks:
            for task in self._replay_tasks.values():
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete cancellation
            await asyncio.gather(*self._replay_tasks.values(), return_exceptions=True)
            self._replay_tasks.clear()

        # Try to clean up wrapped transport's internal tasks if they exist
        if not self._is_replay_mode and hasattr(self.wrapped_transport, "_tasks"):
            for task in self.wrapped_transport._tasks:
                if not task.done():
                    task.cancel()

            # Wait for wrapped transport tasks to complete
            if self.wrapped_transport._tasks:
                await asyncio.gather(
                    *self.wrapped_transport._tasks, return_exceptions=True
                )
                self.wrapped_transport._tasks.clear()

        # Give extra time for websockets library internal cleanup
        await asyncio.sleep(0.5)

        if self._is_replay_mode:
            # In replay mode, just validate we processed all expected interactions
            expected_count = len(self._fixture_interactions)
            if self._invoke_count < expected_count:
                # Allow fewer invokes than expected (some tests might not use all)
                pass
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
        self._active_subscriptions.clear()
        self._subscription_message_queues.clear()
        self._capture_tasks.clear()
        self._replay_tasks.clear()

    def _get_fixture_name_from_callstack(self) -> Optional[str]:
        """Get the fixture name by inspecting the callstack for the test function."""
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

        # Fallback: look for direct test function calls
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
        """Invoke the transport with the given payload."""
        if not self._is_started:
            raise MockWsTransportError(
                "MockWsTransport must be started before invoking. Call start() first."
            )

        if payload is None:
            payload = {}

        self._invoke_count += 1

        if self._is_replay_mode:
            return self._handle_replay_invoke(payload)
        else:
            return await self._handle_capture_invoke(payload, validators)

    def _handle_replay_invoke(self, payload: Any) -> Result[Any, ApiError]:
        """Handle invoke in replay mode."""
        # Apply replacements to the incoming payload before comparison
        replaced_payload = self._apply_replacements(payload, self._request_replacements)
        normalized_payload = self._normalize_payload(replaced_payload)

        # Find matching interaction
        for interaction in self._fixture_interactions:
            if (
                interaction["type"] == "invoke"
                and self._apply_replacements(
                    interaction["normalized_payload"], self._request_replacements
                )
                == normalized_payload
            ):
                result = self._deserialize_result(interaction["result"])
                if result.is_ok():
                    return Result.ok(
                        self._apply_replacements(
                            result.unwrap(), self._response_replacements
                        )
                    )
                else:
                    return result

        raise MockWsTransportError(
            f"No matching invoke interaction found for payload: {normalized_payload}"
        )

    async def _handle_capture_invoke(
        self, payload: Any, validators: list[Rule] | None
    ) -> Result[Any, ApiError]:
        """Handle invoke in capture mode."""
        # Make real API call
        result = await self.wrapped_transport.invoke(payload, validators)

        # Apply replacements to payload before capturing
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
            "type": "invoke",
            "normalized_payload": captured_normalized_payload,
            "result": serialized_result,
            "timestamp": time.time(),
        }
        self._captured_interactions.append(interaction)

        return result

    async def subscribe(
        self,
        subscription: Subscription,
        message_queue: asyncio.Queue[Any] | None = None,
    ) -> tuple[int, asyncio.Queue[Any]]:
        """Subscribe to a data stream using the websocket."""
        if not self._is_started:
            raise MockWsTransportError(
                "MockWsTransport must be started before subscribing. Call start() first."
            )

        if self._is_replay_mode:
            return self._handle_replay_subscribe(subscription, message_queue)
        else:
            return await self._handle_capture_subscribe(subscription, message_queue)

    def _handle_replay_subscribe(
        self,
        subscription: Subscription,
        message_queue: asyncio.Queue[Any] | None = None,
    ) -> tuple[int, asyncio.Queue[Any]]:
        """Handle subscribe in replay mode."""
        if message_queue is None:
            message_queue = asyncio.Queue()

        # Apply replacements to the subscription before comparison
        replaced_subscription = self._apply_replacements(
            subscription, self._request_replacements
        )

        # Find matching subscription interaction
        subscription_id = None
        messages = []

        for interaction in self._fixture_interactions:
            if (
                interaction.get("type") == "subscribe"
                and self._apply_replacements(
                    interaction.get("subscription"), self._request_replacements
                )
                == replaced_subscription
            ):
                subscription_id = interaction.get("subscription_id", 1)
                messages = interaction.get("messages", [])
                break

        if subscription_id is None:
            raise MockWsTransportError(
                f"No matching subscription found for: {replaced_subscription}"
            )

        # Schedule message replay and track the task
        replay_task = asyncio.create_task(
            self._replay_messages(message_queue, messages)
        )
        self._replay_tasks[subscription_id] = replay_task

        return subscription_id, message_queue

    async def _handle_capture_subscribe(
        self,
        subscription: Subscription,
        message_queue: asyncio.Queue[Any] | None = None,
    ) -> tuple[int, asyncio.Queue[Any]]:
        """Handle subscribe in capture mode."""
        # Make real subscription
        subscription_id, real_queue = await self.wrapped_transport.subscribe(
            subscription, message_queue
        )

        # Use the provided queue or create a new one if none provided
        if message_queue is None:
            test_queue: asyncio.Queue[Msg] = asyncio.Queue()
        else:
            test_queue = message_queue

        # Track subscription for message capture
        self._active_subscriptions[subscription_id] = {
            "subscription": self._apply_replacements(
                subscription, self._request_replacements
            ),
            "start_time": time.time(),
        }

        # Start capturing messages and forwarding them to the test queue
        capture_task = asyncio.create_task(
            self._capture_and_forward_messages(subscription_id, real_queue, test_queue)
        )
        self._capture_tasks[subscription_id] = capture_task

        return subscription_id, test_queue

    async def _capture_and_forward_messages(
        self,
        subscription_id: int,
        real_queue: asyncio.Queue[Any],
        test_queue: asyncio.Queue[Any],
    ) -> None:
        """Capture messages from a subscription until cancelled."""
        messages = []
        start_time = time.time()

        try:
            while True:
                try:
                    # Wait for message indefinitely until cancelled
                    message = await real_queue.get()
                    messages.append(
                        {
                            "message": message,
                            "timestamp": time.time() - start_time,
                        }
                    )
                    # Also put message in capture queue for any listening code
                    test_queue.put_nowait(message)
                except asyncio.CancelledError:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            # Save captured subscription data
            if subscription_id in self._active_subscriptions:
                subscription_data = self._active_subscriptions[subscription_id]
                interaction = {
                    "type": "subscribe",
                    "subscription": subscription_data["subscription"],
                    "subscription_id": subscription_id,
                    "messages": messages,
                    "capture_duration": self.capture_duration,
                    "timestamp": subscription_data["start_time"],
                }
                self._captured_interactions.append(interaction)

    async def _replay_messages(
        self, message_queue: asyncio.Queue[Any], messages: list[dict[str, Any]]
    ) -> None:
        """Replay captured messages with their original timing or immediately."""
        try:
            for msg_data in messages:
                if self.replay_with_timing:
                    # Wait for the original timestamp
                    await asyncio.sleep(msg_data["timestamp"])

                message_queue.put_nowait(msg_data["message"])
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe from a data stream."""
        if not self._is_started:
            raise MockWsTransportError(
                "MockWsTransport must be started before unsubscribing. Call start() first."
            )

        if self._is_replay_mode:
            # In replay mode, cancel replay task if active
            if subscription_id in self._replay_tasks:
                task = self._replay_tasks[subscription_id]
                if not task.done():
                    task.cancel()
                del self._replay_tasks[subscription_id]
        else:
            # Cancel capture task if active
            if subscription_id in self._capture_tasks:
                task = self._capture_tasks[subscription_id]
                if not task.done():
                    task.cancel()
                del self._capture_tasks[subscription_id]

            # Unsubscribe from real transport
            await self.wrapped_transport.unsubscribe(subscription_id)

        # Clean up local state
        self._active_subscriptions.pop(subscription_id, None)
        self._subscription_message_queues.pop(subscription_id, None)

    @asynccontextmanager
    async def run(self) -> AsyncGenerator[None, None]:
        """Run the websocket client as a task until context exits."""
        if self._is_replay_mode:
            # In replay mode, we don't need to run the real transport
            yield
        else:
            # In capture mode, run the real transport
            async with self.wrapped_transport.run():
                try:
                    yield
                finally:
                    # Idle for capture duration to let any ongoing captures complete
                    # This needs to happen BEFORE the wrapped transport context exits
                    await asyncio.sleep(self.capture_duration)

    async def run_forever(self) -> None:
        """Run the websocket manager main loop forever or until it is cancelled."""
        if self._is_replay_mode:
            # In replay mode, just wait until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
        else:
            # In capture mode, run the real transport
            try:
                await self.wrapped_transport.run_forever()
            except asyncio.CancelledError:
                # Idle for capture duration after cancellation
                await asyncio.sleep(self.capture_duration)
                raise

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
