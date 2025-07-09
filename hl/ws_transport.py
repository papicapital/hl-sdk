import asyncio
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from itertools import count
from typing import Any, AsyncGenerator, Literal, TypedDict, TypeVar, cast

import websockets

from hl.errors import ApiError
from hl.result import Result
from hl.transport import BaseTransport
from hl.types import (
    ExchangeRequest,
    InfoRequest,
    Msg,
    Network,
    Subscription,
)
from hl.validator import BASE_RULES, Rule

logger = logging.getLogger(__name__)


def subscription_to_identifier(subscription: Subscription) -> str:
    if subscription["type"] == "allMids":
        return "allMids"
    elif subscription["type"] == "notification":
        # NOTE: It would be ideal here to append the user address, however, it's not in the response message.
        return "notification"
    elif subscription["type"] == "webData2":
        return f"webData2:{subscription['user'].lower()}"
    elif subscription["type"] == "candle":
        return f"candle:{subscription['coin'].lower()},{subscription['interval']}"
    elif subscription["type"] == "l2Book":
        return f"l2Book:{subscription['coin'].lower()}"
    elif subscription["type"] == "trades":
        return f"trades:{subscription['coin'].lower()}"
    elif subscription["type"] == "orderUpdates":
        return "orderUpdates"
    elif subscription["type"] == "userEvents":
        # NOTE: It would be ideal here to append the user address, however, it's not in the response message.
        return "userEvents"
    elif subscription["type"] == "userFills":
        return f"userFills:{subscription['user'].lower()}"
    elif subscription["type"] == "userFundings":
        return f"userFundings:{subscription['user'].lower()}"
    elif subscription["type"] == "userNonFundingLedgerUpdates":
        return f"userNonFundingLedgerUpdates:{subscription['user'].lower()}"
    elif subscription["type"] == "activeAssetCtx":
        return f"activeAssetCtx:{subscription['coin'].lower()}"
    elif subscription["type"] == "activeAssetData":
        return f"activeAssetData:{subscription['user'].lower()},{subscription['coin'].lower()}"
    elif subscription["type"] == "userTwapSliceFills":
        return f"userTwapSliceFills:{subscription['user'].lower()}"
    elif subscription["type"] == "userTwapHistory":
        return f"userTwapHistory:{subscription['user'].lower()}"
    elif subscription["type"] == "bbo":
        return f"bbo:{subscription['coin'].lower()}"
    raise ValueError("Unknown subscription")


def msg_to_identifier(msg: Msg) -> str | None:
    if msg["channel"] == "pong":
        return "pong"
    elif msg["channel"] == "allMids":
        return "allMids"
    elif msg["channel"] == "notification":
        return "notification"
    elif msg["channel"] == "webData2":
        return f"webData2:{msg['data']['user'].lower()}"
    elif msg["channel"] == "candle":
        return f"candle:{msg['data']['s'].lower()},{msg['data']['i']}"
    elif msg["channel"] == "l2Book":
        return f"l2Book:{msg['data']['coin'].lower()}"
    elif msg["channel"] == "trades":
        trades = msg["data"]
        if len(trades) == 0:
            return None
        else:
            return f"trades:{trades[0]['coin'].lower()}"
    elif msg["channel"] == "orderUpdates":
        return "orderUpdates"
    elif msg["channel"] == "user":
        # NOTE: The response message uses the channel name `user`, however, the subscription method uses `userEvents`.
        return "userEvents"
    elif msg["channel"] == "userFills":
        return f"userFills:{msg['data']['user'].lower()}"
    elif msg["channel"] == "userFundings":
        return f"userFundings:{msg['data']['user'].lower()}"
    elif msg["channel"] == "userNonFundingLedgerUpdates":
        return f"userNonFundingLedgerUpdates:{msg['data']['user'].lower()}"
    elif msg["channel"] == "activeAssetCtx" or msg["channel"] == "activeSpotAssetCtx":
        return f"activeAssetCtx:{msg['data']['coin'].lower()}"
    elif msg["channel"] == "activeAssetData":
        return f"activeAssetData:{msg['data']['user'].lower()},{msg['data']['coin'].lower()}"
    elif msg["channel"] == "userTwapSliceFills":
        return f"userTwapSliceFills:{msg['data']['user'].lower()}"
    elif msg["channel"] == "userTwapHistory":
        return f"userTwapHistory:{msg['data']['user'].lower()}"
    elif msg["channel"] == "bbo":
        return f"bbo:{msg['data']['coin'].lower()}"
    elif msg["channel"] == "post":
        return f"post:{msg['data']['id']}"
    return None


class _SubscribeCommand(TypedDict):
    method: Literal["subscribe"]
    subscription: Subscription
    message_queue: asyncio.Queue[Any]
    subscription_id: int


class _UnsubscribeCommand(TypedDict):
    method: Literal["unsubscribe"]
    subscription_id: int


class _PostCommand(TypedDict):
    method: Literal["post"]
    post_id: int
    endpoint: Literal["info", "exchange"]
    request: InfoRequest | ExchangeRequest


_Command = _SubscribeCommand | _UnsubscribeCommand | _PostCommand

T_Msg = TypeVar("T_Msg", bound=Msg)


class WsTransport(BaseTransport):
    """Client for the Hyperliquid websocket API."""

    def __init__(self, network: Network) -> None:
        """Client for the Hyperliquid websocket API.

        Args:
            network (hl.types.Network): The network to use.
        """
        self.network = network

        self._subscription_id_counter = count()
        self._post_id_counter = count()
        self._commands = asyncio.Queue[_Command]()
        self._subscriptions: dict[
            str,
            list[tuple[asyncio.Queue[Any], int]],
        ] = defaultdict(list)
        self._post_futures: dict[int, asyncio.Future[Any]] = {}
        self._subscription_id_info: dict[int, tuple[str, Subscription]] = {}
        self._last_ping: float | None = None
        self._tasks: list[asyncio.Task[Any]] = []

    async def invoke(
        self, payload: Any, validators: list[Rule] | None = None
    ) -> Result[Any, ApiError]:
        """Send a request to the websocket API.

        Args:
            payload (dict): The payload to send to the websocket API.
            validators (list[Rule] | None): The validators to apply to the response.
        """
        # Handle Info and Exchange requests
        # InfoRequest types all have a "type" field
        if isinstance(payload, dict) and "type" in payload:
            response = await self.post("info", cast(InfoRequest, payload))
            response = response["data"]["response"]["payload"]["data"]
            for validator in BASE_RULES + (validators or []):
                if error := validator("info", response):
                    return Result.err(error)
            return Result.ok(response)

        # Handle Exchange requests (they have an "action" field)
        if isinstance(payload, dict) and "action" in payload:
            response = await self.post("exchange", cast(ExchangeRequest, payload))
            response = response["data"]["response"]["payload"]
            for validator in BASE_RULES + (validators or []):
                if error := validator("exchange", response):
                    return Result.err(error)
            return Result.ok(response)

        raise ValueError(f"Unknown payload type: {payload}")

    async def _handle_ping(self, ws_client: websockets.ClientConnection) -> None:
        """Send a ping to the server if it has been more than 50 seconds since the last ping.

        Args:
            ws_client (websockets.ClientConnection): The websocket connection.
        """
        should_send = (time.time() - self._last_ping) > 50 if self._last_ping else True
        if should_send:
            await ws_client.send(json.dumps({"method": "ping"}))
            self._last_ping = time.time()

    async def _perform_subscribe(
        self,
        ws_client: websockets.ClientConnection,
        command: _SubscribeCommand,
    ) -> None:
        data = json.dumps(
            {"method": "subscribe", "subscription": command["subscription"]}
        )
        await ws_client.send(data)
        identifier = subscription_to_identifier(command["subscription"])
        self._subscription_id_info[command["subscription_id"]] = (
            identifier,
            command["subscription"],
        )
        self._subscriptions[identifier].append(
            (command["message_queue"], command["subscription_id"])
        )

    async def _perform_unsubscribe(
        self,
        ws_client: websockets.ClientConnection,
        command: _UnsubscribeCommand,
    ) -> None:
        identifier, subscription = self._subscription_id_info[
            command["subscription_id"]
        ]
        remaining = [
            (message_queue, sid)
            for message_queue, sid in self._subscriptions[identifier]
            if sid != command["subscription_id"]
        ]
        if len(remaining) == 0:
            data = json.dumps({"method": "unsubscribe", "subscription": subscription})
            await ws_client.send(data)
        self._subscriptions[identifier] = remaining

    async def _perform_post(
        self,
        ws_client: websockets.ClientConnection,
        command: _PostCommand,
    ) -> None:
        data = json.dumps(
            {
                "method": "post",
                "id": command["post_id"],
                "request": {
                    "type": "action" if command["endpoint"] == "exchange" else "info",
                    "payload": command["request"],
                },
            }
        )
        await ws_client.send(data)

    async def _pinger(self, ws_client: websockets.ClientConnection) -> None:
        try:
            while True:
                await self._handle_ping(ws_client)
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            raise

    async def _producer(self, ws_client: websockets.ClientConnection) -> None:
        try:
            while True:
                command = await self._commands.get()
                if command["method"] == "subscribe":
                    await self._perform_subscribe(ws_client, command)
                elif command["method"] == "unsubscribe":
                    await self._perform_unsubscribe(ws_client, command)
                elif command["method"] == "post":
                    await self._perform_post(ws_client, command)
        except asyncio.CancelledError:
            raise

    async def _consumer(self, ws_client: websockets.ClientConnection) -> None:
        try:
            while True:
                data = await ws_client.recv()
                message = cast(Msg, json.loads(data))
                identifier = msg_to_identifier(message)
                if identifier and identifier.startswith("post:"):
                    post_id = int(identifier.split(":")[1])
                    fut = self._post_futures.pop(post_id)
                    fut.set_result(message)
                elif identifier:
                    for message_queue, _subscription_id in self._subscriptions[
                        identifier
                    ]:
                        # Note: since we don't specify a queue size, this should never block
                        message_queue.put_nowait(message)
        except asyncio.CancelledError:
            raise

    async def run_forever(self) -> None:
        """Run the websocket manager main loop forever or until it is cancelled."""
        # Connect to the websocket API. Using an async for loop allows for reconnection if connection drops.
        async for ws in websockets.connect(
            self.network["ws_url"],
            ssl=self.network["ws_url"].startswith("wss") or None,
            user_agent_header="hl-sdk",
            open_timeout=2,
        ):
            try:
                try:
                    async with asyncio.TaskGroup() as tasks:
                        self._tasks = [
                            tasks.create_task(self._pinger(ws)),
                            tasks.create_task(self._producer(ws)),
                            tasks.create_task(self._consumer(ws)),
                        ]
                except* websockets.ConnectionClosed:
                    # TODO: Are subscriptions automatically re-established?
                    logger.warning("Websocket connection closed unexpectedly")
                    # Clear tasks since they will be recreated on reconnection
                    self._tasks.clear()
            except asyncio.CancelledError:
                raise

    @asynccontextmanager
    async def run(self) -> AsyncGenerator[None, None]:
        """Run the websocket client as a task until context exits."""
        async with asyncio.TaskGroup() as tasks:
            task = tasks.create_task(self.run_forever())
            try:
                yield
            finally:
                task.cancel()

    async def subscribe(
        self,
        subscription: Subscription,
        message_queue: asyncio.Queue[T_Msg] | None = None,
    ) -> tuple[int, asyncio.Queue[T_Msg]]:
        """Subscribe to a data stream using the websocket.

        Args:
            subscription (hl.types.Subscription): The details of what data to subscribe to.
            message_queue (asyncio.Queue | None): The queue to send received messages to.
                If None, a new queue will be created. The queue will be returned to the caller.

        Returns:
            tuple[int, asyncio.Queue]: A tuple containing the subscription ID and the message queue
                that will receive messages from the subscription. The subscription ID can be used to unsubscribe.
        """
        if message_queue is None:
            message_queue = asyncio.Queue()
        subscription_id = next(self._subscription_id_counter)
        await self._commands.put(
            _SubscribeCommand(
                method="subscribe",
                subscription=subscription,
                message_queue=message_queue,
                subscription_id=subscription_id,
            )
        )
        return subscription_id, message_queue

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe from a data stream using the websocket.

        Args:
            subscription_id (int): The subscription ID returned by :method:`subscribe`.
        """
        await self._commands.put(
            _UnsubscribeCommand(method="unsubscribe", subscription_id=subscription_id)
        )

    async def post(
        self,
        endpoint: Literal["info", "exchange"],
        request: Any,
    ) -> Any:
        """Send an info or exchange request to the websocket API.

        These requests are normally sent as an HTTP `POST` request to the `/info` or `/exchange` endpoints,
        but can also be sent via the websocket.

        Args:
            endpoint (Literal["info", "exchange"]): The endpoint to send the request to.
            request (Any): The request to send.

        Returns:
            Any: The response from the websocket API.
        """
        post_id = next(self._post_id_counter)
        self._post_futures[post_id] = asyncio.Future()
        await self._commands.put(
            _PostCommand(
                method="post", post_id=post_id, endpoint=endpoint, request=request
            )
        )
        return await self._post_futures[post_id]
