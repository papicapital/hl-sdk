import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import AsyncGenerator, cast

import pytest

from hl import TESTNET, Account, Cloid, Exchange, HttpTransport, Universe
from hl.constants import LIMIT_GTC
from hl.errors import StatusError
from hl.types import AssetInfo, ModifyParams, OrderResponseDataStatusResting
from tests.conftest import ReplaceValues
from tests.mock_http_transport import MockHttpTransport

# Mock account info for tests

TEST_ACCOUNT = Account(
    address=os.getenv("HL_ADDRESS") or "0x0000000000000000000000000000000000000000",
    secret_key=os.getenv("HL_SECRET_KEY")
    or "0x0000000000000000000000000000000000000000000000000000000000000001",
)

MOCK_UNIVERSE = Universe(
    {
        3: AssetInfo(id=3, name="BTC", type="PERPETUAL", pxDecimals=1, szDecimals=5),
        78: AssetInfo(id=78, name="WIF", type="PERPETUAL", pxDecimals=2, szDecimals=0),
        10_001: AssetInfo(
            id=10_001, name="PURR", type="SPOT", pxDecimals=6, szDecimals=0
        ),
    }
)

SUB_ACCOUNT_ADDRESS = os.getenv(
    "SUB_ACCOUNT_ADDRESS", "0x0000000000000000000000000000000000000001"
)
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS", "0x0000000000000000000000000000000000000002")
AGENT_ADDRESS = os.getenv("AGENT_ADDRESS", "0x0000000000000000000000000000000000000003")
SECOND_ADDRESS = os.getenv(
    "SECOND_ADDRESS", "0x0000000000000000000000000000000000000004"
)
VALIDATOR_ADDRESS = os.getenv(
    "VALIDATOR_ADDRESS", "0x0000000000000000000000000000000000000005"
)


@pytest.fixture
async def exchange_client() -> AsyncGenerator[Exchange, None]:
    """Create an Exchange client for testing."""
    real_transport = HttpTransport(TESTNET, "exchange")
    mock_transport = MockHttpTransport(real_transport)
    client = Exchange(
        transport=mock_transport,
        universe=MOCK_UNIVERSE,
        account=TEST_ACCOUNT,
    )
    mock_transport.start()
    yield client
    mock_transport.stop()


async def test_place_order(exchange_client: Exchange) -> None:
    """Test placing an order."""
    response = await exchange_client.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.01"),
        limit_price=Decimal("105_000"),
        order_type=LIMIT_GTC,
    )

    assert response.is_ok()
    response_data = response.unwrap()
    assert isinstance(response_data, dict)
    assert "status" in response_data
    assert response_data["status"] == "ok"

    # Verify response structure
    assert "response" in response_data
    assert "type" in response_data["response"]
    assert response_data["response"]["type"] == "order"

    # Verify order data
    order_data = response_data["response"]["data"]
    assert isinstance(order_data, dict)
    assert "statuses" in order_data
    assert len(order_data["statuses"]) == 1

    status = order_data["statuses"][0]
    assert isinstance(status, dict)
    resting_data = cast(OrderResponseDataStatusResting, status)
    assert resting_data["resting"]["oid"] is not None


async def test_place_order_custom_cloid(exchange_client: Exchange) -> None:
    """Test placing an order with a custom cloid."""
    cloid = Cloid.from_int(1337)
    response = await exchange_client.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.01"),
        limit_price=Decimal("105_000"),
        order_type=LIMIT_GTC,
        cloid=cloid,
    )

    assert response.is_ok()
    response_data = response.unwrap()
    assert isinstance(response_data, dict)
    assert "status" in response_data
    assert response_data["status"] == "ok"

    # Verify response structure
    assert "response" in response_data
    assert "type" in response_data["response"]
    assert response_data["response"]["type"] == "order"

    # Verify order data
    order_data = response_data["response"]["data"]
    assert isinstance(order_data, dict)
    assert "statuses" in order_data
    assert len(order_data["statuses"]) == 1

    status = order_data["statuses"][0]
    assert isinstance(status, dict)
    resting_data = cast(OrderResponseDataStatusResting, status)
    assert resting_data["resting"]["oid"] is not None
    assert "cloid" in resting_data["resting"]
    assert cloid == Cloid.from_str(resting_data["resting"]["cloid"])


async def test_cancel_order(exchange_client: Exchange) -> None:
    response = await exchange_client.cancel_order(
        asset="BTC",
        order_id=33753639142,
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "cancel"
    assert len(response_data["response"]["data"]["statuses"]) == 1
    order_status = response_data["response"]["data"]["statuses"][0]
    assert order_status == "success"


async def test_cancel_order_by_id(exchange_client: Exchange) -> None:
    cloid = Cloid.from_int(1337)
    response = await exchange_client.cancel_order_by_id(
        asset="BTC",
        client_order_id=cloid,
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "cancel"
    assert len(response_data["response"]["data"]["statuses"]) == 1
    order_status = response_data["response"]["data"]["statuses"][0]
    assert order_status == "success"


@pytest.mark.skip(reason="Need 1 mn trading volume before testing this")
async def test_schedule_cancellation(exchange_client: Exchange) -> None:
    response = await exchange_client.schedule_cancellation(
        time=datetime(2025, 6, 17, 12, 5, 0, tzinfo=UTC)
    )


async def test_modify_order(exchange_client: Exchange) -> None:
    response = await exchange_client.modify_order(
        asset="BTC",
        order_id=33961768362,
        limit_price=Decimal("105_000"),
        is_buy=True,
        size=Decimal("0.01"),
        order_type=LIMIT_GTC,
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_modify_order_with_cloid(exchange_client: Exchange) -> None:
    response = await exchange_client.modify_order(
        asset="BTC",
        order_id=Cloid.from_int(1338),
        limit_price=Decimal("103_000"),
        is_buy=True,
        size=Decimal("0.004"),
        order_type=LIMIT_GTC,
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_modify_orders(exchange_client: Exchange) -> None:
    response = await exchange_client.modify_orders(
        modify_requests=[
            ModifyParams(
                order_id=33961871564,
                order={
                    "asset": "BTC",
                    "limit_price": Decimal("104_000"),
                    "is_buy": True,
                    "size": Decimal("0.004"),
                    "order_type": LIMIT_GTC,
                    "reduce_only": False,
                },
            )
        ]
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "order"
    assert "resting" in response_data["response"]["data"]["statuses"][0]
    status = cast(
        OrderResponseDataStatusResting, response_data["response"]["data"]["statuses"][0]
    )
    assert status["resting"]["oid"] == 33962423094


async def test_update_leverage(exchange_client: Exchange) -> None:
    response = await exchange_client.update_leverage(
        asset="BTC",
        leverage=14,
        margin_mode="isolated",
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_update_margin(exchange_client: Exchange) -> None:
    response = await exchange_client.update_margin(
        asset="BTC",
        amount=Decimal("175"),
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_adjust_margin_to_1(exchange_client: Exchange) -> None:
    response = await exchange_client.adjust_margin(
        asset="WIF",
        leverage=Decimal("1.0"),
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_adjust_margin_to_0_5(exchange_client: Exchange) -> None:
    response = await exchange_client.adjust_margin(
        asset="WIF",
        leverage=Decimal("0.5"),
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_send_usd(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.time": 1750180760107,
            "action.destination": SECOND_ADDRESS,
        },
    ):
        response = await exchange_client.send_usd(
            amount=Decimal("100"),
            destination=SECOND_ADDRESS,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_send_spot(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.time": 1750181062363,
            "action.destination": SECOND_ADDRESS,
        },
    ):
        response = await exchange_client.send_spot(
            asset="USDC",
            amount=Decimal("100"),
            destination=SECOND_ADDRESS,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"


async def test_send_spot_without_sufficient_balance(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.time": 1750181062363,
            "action.destination": SECOND_ADDRESS,
        },
    ):
        response = await exchange_client.send_spot(
            asset="PURR",
            amount=Decimal("100_000"),
            destination=SECOND_ADDRESS,
        )
        # The API returns a successful HTTP response but with error status due to insufficient balance
        assert response.is_err()
        error = response.unwrap_err()
        assert isinstance(error, StatusError)


async def test_send_spot_purr(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.time": 1750181453275,
            "action.destination": SECOND_ADDRESS,
        },
    ):
        response = await exchange_client.send_spot(
            asset="PURR",
            amount=Decimal("10"),
            destination=SECOND_ADDRESS,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"


async def test_withdraw_funds(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.time": 1750181714145,
            "action.destination": TEST_ACCOUNT.address,
        },
    ):
        response = await exchange_client.withdraw_funds(
            amount=Decimal("100"),
            destination=TEST_ACCOUNT.address,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"


async def test_transfer_usd(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1750019107110,
        },
    ):
        response = await exchange_client.transfer_usd(
            amount=Decimal("25_000"), to_perp=True
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


# TODO: Find a perp dex to work with
@pytest.mark.skip(reason="Removed from API docs. Is this still supported?")
async def test_transfer_tokens(exchange_client: Exchange) -> None:
    response = await exchange_client.transfer_tokens(
        amount=Decimal("100"),
        to_perp=True,
        dex="PURR",
        token="PURR",
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"


async def test_stake_tokens(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1750357771819,
        },
    ):
        response = await exchange_client.stake_tokens(amount=Decimal("6"))
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_unstake_tokens(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1750357814486,
        },
    ):
        response = await exchange_client.unstake_tokens(amount=Decimal("2.1"))
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_delegate_tokens(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1750358092063,
            "action.validator": VALIDATOR_ADDRESS,
        },
    ):
        response = await exchange_client.delegate_tokens(
            validator=VALIDATOR_ADDRESS,
            amount=Decimal("0.5"),
            is_undelegate=False,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_undelegate_tokens(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1751094082904,
            "action.validator": VALIDATOR_ADDRESS,
        },
    ):
        response = await exchange_client.delegate_tokens(
            validator=VALIDATOR_ADDRESS,
            amount=Decimal("0.5"),
            is_undelegate=True,
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_transfer_vault_funds(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={"request.vaultAddress": VAULT_ADDRESS},
    ):
        response = await exchange_client.transfer_vault_funds(
            vault=VAULT_ADDRESS, amount=Decimal("62"), is_deposit=True
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"


async def test_transfer_vault_funds_withdrawal(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.vaultAddress": VAULT_ADDRESS,
        },
    ):
        response = await exchange_client.transfer_vault_funds(
            vault=VAULT_ADDRESS, amount=Decimal("431"), is_deposit=False
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"


async def test_approve_agent(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={"action.nonce": 1750330228648, "action.agentAddress": AGENT_ADDRESS},
    ):
        response = await exchange_client.approve_agent(
            agent=AGENT_ADDRESS, name="TestAgent"
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_approve_builder(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={
            "action.nonce": 1751093867901,
            "action.builder": SECOND_ADDRESS,
        },
    ):
        response = await exchange_client.approve_builder(
            builder=SECOND_ADDRESS,
            max_fee_rate=Decimal("0.0001"),  # 0.01%
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "default"


async def test_place_twap(exchange_client: Exchange) -> None:
    response = await exchange_client.place_twap(
        asset="BTC",
        size=Decimal("0.02"),
        minutes=5,
        randomize=True,
        is_buy=True,
    )
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "twapOrder"


async def test_cancel_twap(exchange_client: Exchange) -> None:
    response = await exchange_client.cancel_twap(asset="BTC", twap_id=6552)
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "twapCancel"
    assert response_data["response"]["data"]["status"] == "success"


async def test_reserve_weight(exchange_client: Exchange) -> None:
    response = await exchange_client.reserve_weight(weight=100)
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_create_vault(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        request={"action.nonce": 1750021391791},
        response={"response.data": VAULT_ADDRESS},
    ):
        response = await exchange_client.create_vault(
            name="TestVault1",
            description="This is a test vault please ignore",
            initial_usd=Decimal("200"),
        )
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "createVault"
        assert response_data["response"]["data"] == VAULT_ADDRESS


async def test_create_sub_account(
    exchange_client: Exchange, replace_values: ReplaceValues
) -> None:
    with replace_values(
        exchange_client.transport,
        response={"response.data": SUB_ACCOUNT_ADDRESS},
    ):
        response = await exchange_client.create_sub_account(name="testplsignore")
        assert response.is_ok()
        response_data = response.unwrap()
        assert response_data["status"] == "ok"
        assert response_data["response"]["type"] == "createSubAccount"
        assert response_data["response"]["data"] == SUB_ACCOUNT_ADDRESS


async def test_register_referrer(exchange_client: Exchange) -> None:
    response = await exchange_client.register_referrer(code="TESTCODEPLSIGNORE")
    assert response.is_ok()
    response_data = response.unwrap()
    assert response_data["status"] == "ok"
    assert response_data["response"]["type"] == "default"


async def test_register_referrer_with_not_enough_volume(
    exchange_client: Exchange,
) -> None:
    response = await exchange_client.register_referrer(code="TESTCODEPLSIGNORE")
    assert response.is_err()
    error = response.unwrap_err()
    assert isinstance(error, StatusError)
