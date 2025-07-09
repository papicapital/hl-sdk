from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Sequence, cast

from hl._lib import get_timestamp_ms, to_minor_unit, to_ms
from hl.account import Account
from hl.cloid import Cloid
from hl.errors import ApiError
from hl.result import Result
from hl.signer import Signer
from hl.transport import BaseTransport
from hl.types import (
    Action,
    ApproveAgentAction,
    ApproveAgentResponse,
    ApproveBuilderFeeAction,
    ApproveBuilderFeeResponse,
    BatchModifyAction,
    BatchModifyResponse,
    BuilderOptions,
    CancelAction,
    CancelByCloidAction,
    CancelByCloidParams,
    CancelByCloidResponse,
    CancelParams,
    CancelResponse,
    CreateSubAccountAction,
    CreateSubAccountResponse,
    CreateVaultAction,
    CreateVaultResponse,
    DepositStakingAction,
    DepositStakingResponse,
    Grouping,
    ModifyAction,
    ModifyParams,
    ModifyResponse,
    ModifyWire,
    OrderAction,
    OrderParams,
    OrderResponse,
    OrderType,
    OrderWire,
    PerpDexClassTransferAction,
    PerpDexClassTransferResponse,
    RegisterReferrerAction,
    RegisterReferrerResponse,
    ReserveRequestWeightAction,
    ReserveRequestWeightResponse,
    ScheduleCancelAction,
    ScheduleCancelResponse,
    SetReferrerAction,
    SetReferrerResponse,
    SpotSendAction,
    SpotSendResponse,
    SubAccountTransferAction,
    SubAccountTransferResponse,
    TokenDelegateAction,
    TokenDelegateResponse,
    TopUpIsolatedOnlyMarginAction,
    TopUpIsolatedOnlyMarginResponse,
    TwapCancelAction,
    TwapCancelResponse,
    TwapOrderAction,
    TwapOrderResponse,
    UpdateIsolatedMarginAction,
    UpdateIsolatedMarginResponse,
    UpdateLeverageAction,
    UpdateLeverageResponse,
    UsdClassTransferAction,
    UsdClassTransferResponse,
    UsdSendAction,
    UsdSendResponse,
    VaultTransferAction,
    VaultTransferResponse,
    WithdrawAction,
    WithdrawResponse,
    WithdrawStakingAction,
    WithdrawStakingResponse,
    order_request_to_order_wire,
)
from hl.universe import Universe
from hl.validator import Rule


class Exchange:
    """The Exchange class provides methods to interact with the /exchange endpoint.

    The methods interact with onchain assets and manages orders on the exchange.
    """

    def __init__(
        self,
        *,
        transport: BaseTransport,
        universe: Universe,
        account: Account | None = None,
    ):
        """Create an Exchange instance.

        Args:
            transport (hl.transport.BaseTransport): The transport to use to make the requests.
            universe (hl.universe.Universe): The universe to use for the exchange.
            account (hl.account.Account | None): The account to use for the exchange. Defaults to None.

        Returns:
            (hl.Exchange): The Exchange instance.
        """
        self.transport = transport
        self.universe = universe
        self.account = account

    def _resolve_signer(self, account: Account | None = None) -> Signer:
        if account is not None:
            return Signer(account)
        if self.account is not None:
            return Signer(self.account)
        raise ValueError(
            "Account is required either as a class-level attribute or as a parameter"
        )

    async def _sign_and_invoke(
        self,
        action: Action,
        nonce: int | None = None,
        account: Account | None = None,
        validators: list[Rule] | None = None,
    ) -> Result[Any, ApiError]:
        signer = self._resolve_signer(account)
        signature, nonce = signer.sign(
            action,
            self.transport.network,
            nonce=nonce,
        )
        payload = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "vaultAddress": signer.account.vault_address,
        }
        return await self.transport.invoke(payload, validators)

    async def place_orders(
        self,
        *,
        order_requests: list[OrderParams],
        grouping: Grouping = "na",
        builder: BuilderOptions | None = None,
        account: Account | None = None,
    ) -> Result[OrderResponse, ApiError]:
        """Place multiple orders.

        POST /exchange

        Args:
            order_requests (list[hl.types.OrderParams]): The orders to place.
            grouping (hl.types.Grouping): The grouping to use for the orders. Defaults to "na".
            builder (hl.types.BuilderOptions | None): The builder options to use for the orders. Defaults to None.
            account (hl.types.Account | None): The account to use for the orders. Defaults to the class-level account.

        Returns:
            (Result[hl.types.OrderResponse, ApiError]): A Result containing the response from placing the orders.
        """
        order_wires: list[OrderWire] = [
            order_request_to_order_wire(
                order, self.universe.to_asset_id(order["asset"])
            )
            for order in order_requests
        ]

        order_action: OrderAction = {
            "type": "order",
            "orders": order_wires,
            "grouping": grouping,
        }
        if builder is not None:
            order_action["builder"] = builder

        response = await self._sign_and_invoke(order_action, account=account)
        return cast(Result[OrderResponse, ApiError], response)

    async def place_order(
        self,
        *,
        asset: int | str,
        is_buy: bool,
        size: Decimal,
        limit_price: Decimal,
        order_type: OrderType,
        reduce_only: bool = False,
        cloid: Cloid | None = None,
        builder: BuilderOptions | None = None,
        account: Account | None = None,
    ) -> Result[OrderResponse, ApiError]:
        """Place a single order.

        POST /exchange

        Args:
            asset (int | str): The asset to place the order on.
            is_buy (bool): Whether the order is a buy order.
            size (decimal.Decimal): The size of the order.
            limit_price (decimal.Decimal): The limit price of the order.
            order_type (hl.types.OrderType): The type (limit, trigger) of order to place.
            reduce_only (bool): Whether the order is a reduce-only order.
            cloid (hl.types.Cloid | None): The cloid to use for the order. Defaults to None.
            builder (hl.types.BuilderOptions | None): The builder options to use for the order. Defaults to None.
            account (hl.account.Account | None): The account to use for the order. Defaults to the class-level account.

        Returns:
            (Result[hl.types.OrderResponse, ApiError]): A Result containing the response from placing the order.
        """
        order: OrderParams = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "limit_price": limit_price,
            "order_type": order_type,
            "reduce_only": reduce_only,
        }
        if cloid:
            order["cloid"] = cloid

        return await self.place_orders(
            order_requests=[order], builder=builder, account=account
        )

    async def cancel_orders(
        self, *, cancel_requests: Sequence[CancelParams], account: Account | None = None
    ) -> Result[CancelResponse, ApiError]:
        """Cancel multiple orders by their oid.

        POST /exchange

        Args:
            cancel_requests (list[hl.types.OrderCancelParams]): The orders to cancel.
            account (hl.account.Account | None): The account to use for the order. Defaults to the class-level account.

        Returns:
            (Result[hl.types.CancelResponse, ApiError]): A Result containing the response from cancelling the orders.
        """
        cancel_action: CancelAction = {
            "type": "cancel",
            "cancels": [
                {
                    "a": self.universe.to_asset_id(cancel["asset"]),
                    "o": cancel["order_id"],
                }
                for cancel in cancel_requests
            ],
        }
        response = await self._sign_and_invoke(cancel_action, account=account)
        return cast(Result[CancelResponse, ApiError], response)

    async def schedule_cancellation(
        self,
        *,
        time: int | datetime | date | None = None,
        account: Account | None = None,
    ) -> Result[ScheduleCancelResponse, ApiError]:
        """Schedule a cancel-all operation at a future time.

        Schedules a time (in UTC millis) to cancel all open orders. The time must be at least 5 seconds after the current time.
        Once the time comes, all open orders will be canceled and a trigger count will be incremented. The max number of triggers
        per day is 10. This trigger count is reset at 00:00 UTC.

        Args:
            time (int | datetime | date | None): if time is not None, then set the cancel time in the future. If None, then unsets any cancel time in the future.
            account (hl.account.Account | None): The account to use for the cancel. Defaults to the class-level account.

        Returns:
            (Result[hl.types.ScheduleCancelResponse, ApiError]): A Result containing the response from scheduling the cancel.
        """
        schedule_cancel_action: ScheduleCancelAction = {
            "type": "scheduleCancel",
        }
        if time:
            schedule_cancel_action["time"] = to_ms(time)
        response = await self._sign_and_invoke(schedule_cancel_action, account=account)
        return cast(Result[ScheduleCancelResponse, ApiError], response)

    async def modify_order(
        self,
        *,
        order_id: int | Cloid,
        asset: int | str,
        is_buy: bool,
        size: Decimal,
        limit_price: Decimal,
        order_type: OrderType,
        reduce_only: bool = False,
    ) -> Result[ModifyResponse, ApiError]:
        """Modify an order.

        POST /exchange

        Args:
            order_id (int | Cloid): The oid of the order to modify.
            asset (int | str): The asset to modify the order to.
            is_buy (bool): Whether the order is a buy order.
            size (decimal.Decimal): The size of the order.
            limit_price (decimal.Decimal): The limit price of the order.
            order_type (hl.types.OrderType): The type (limit, trigger) of order to modify.
            reduce_only (bool): Whether the order is a reduce-only order.

        Returns:
            (Result[hl.types.ModifyResponse, ApiError]): A Result containing the response from modifying the order.
        """
        action = ModifyAction(
            type="modify",
            oid=order_id if isinstance(order_id, int) else order_id.to_raw(),
            order=order_request_to_order_wire(
                {
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": size,
                    "limit_price": limit_price,
                    "order_type": order_type,
                    "reduce_only": reduce_only,
                },
                self.universe.to_asset_id(asset),
            ),
        )
        response = await self._sign_and_invoke(action)
        return cast(Result[ModifyResponse, ApiError], response)

    async def modify_orders(
        self, modify_requests: list[ModifyParams]
    ) -> Result[BatchModifyResponse, ApiError]:
        """Modify multiple orders.

        POST /exchange

        Args:
            modify_requests (list[hl.types.ModifyParams]): The orders to modify.

        Returns:
            (Result[hl.types.BatchModifyResponse, ApiError]): A Result containing the response from modifying the orders.
        """
        modify_wires: list[ModifyWire] = [
            {
                "oid": modify["order_id"]
                if isinstance(modify["order_id"], int)
                else modify["order_id"].to_raw(),
                "order": order_request_to_order_wire(
                    modify["order"],
                    self.universe.to_asset_id(modify["order"]["asset"]),
                ),
            }
            for modify in modify_requests
        ]
        action: BatchModifyAction = {
            "type": "batchModify",
            "modifies": modify_wires,
        }
        response = await self._sign_and_invoke(action)
        return cast(Result[BatchModifyResponse, ApiError], response)

    async def update_leverage(
        self,
        *,
        asset: int | str,
        leverage: int,
        margin_mode: Literal["cross", "isolated"],
    ) -> Result[UpdateLeverageResponse, ApiError]:
        """Update the leverage for a given asset.

        POST /exchange

        Args:
            asset (int | str): The asset to update the leverage for.
            leverage (int): The leverage to set for the asset.
            margin_mode (Literal["cross", "isolated"]): Either "cross" or "isolated".

        Returns:
            (Result[hl.types.UpdateLeverageResponse, ApiError]): A Result containing the response from updating the leverage.
        """
        asset = self.universe.to_asset_id(asset)
        update_leverage_action: UpdateLeverageAction = {
            "type": "updateLeverage",
            "asset": asset,
            "isCross": margin_mode == "cross",
            "leverage": leverage,
        }
        response = await self._sign_and_invoke(update_leverage_action)
        return cast(Result[UpdateLeverageResponse, ApiError], response)

    async def update_margin(
        self,
        *,
        asset: int | str,
        amount: Decimal,
    ) -> Result[UpdateIsolatedMarginResponse, ApiError]:
        """Update the isolated margin for a given asset.

        POST /exchange

        Args:
            asset (int | str): The asset to update the isolated margin for.
            amount (Decimal): The amount to remove from or to add to the isolated margin.

        Returns:
            (Result[hl.types.UpdateIsolatedMarginResponse, ApiError]): A Result containing the response from updating the isolated margin.
        """
        asset = self.universe.to_asset_id(asset)
        amount_int = to_minor_unit(amount, "USDC")
        update_isolated_margin_action: UpdateIsolatedMarginAction = {
            "type": "updateIsolatedMargin",
            "asset": asset,
            "isBuy": True,
            "ntli": amount_int,
        }
        response = await self._sign_and_invoke(update_isolated_margin_action)
        return cast(Result[UpdateIsolatedMarginResponse, ApiError], response)

    async def adjust_margin(
        self,
        *,
        asset: int | str,
        leverage: Decimal,
    ) -> Result[TopUpIsolatedOnlyMarginResponse, ApiError]:
        """Adjust the isolated margin for a given asset to a specific leverage ratio.

        This function allows you to target a specific leverage ratio instead of a specific USDC amount.

        POST /exchange

        Args:
            asset (int | str): The asset to adjust the isolated margin for.
            leverage (Decimal): The leverage to set for the asset.

        Returns:
            (Result[hl.types.TopUpIsolatedOnlyMarginResponse, ApiError]): A Result containing the response from adjusting the isolated margin.
        """
        asset = self.universe.to_asset_id(asset)
        top_up_isolated_only_margin_action: TopUpIsolatedOnlyMarginAction = {
            "type": "topUpIsolatedOnlyMargin",
            "asset": asset,
            "leverage": str(leverage),
        }
        response = await self._sign_and_invoke(top_up_isolated_only_margin_action)
        return cast(Result[TopUpIsolatedOnlyMarginResponse, ApiError], response)

    async def send_usd(
        self, *, amount: Decimal, destination: str, account: Account | None = None
    ) -> Result[UsdSendResponse, ApiError]:
        """Send USDC to another address.

        POST /exchange

        Args:
            amount (Decimal): The amount of USDC to send.
            destination (str): The address to send the USDC to.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.UsdSendResponse, ApiError]): A Result containing the response from sending the USDC.
        """
        nonce = get_timestamp_ms()
        action: UsdSendAction = {
            "type": "usdSend",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "amount": str(amount),
            "destination": destination,
            "time": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[UsdSendResponse, ApiError], response)

    async def approve_agent(
        self, *, agent: str, name: str | None = None, account: Account | None = None
    ) -> Result[ApproveAgentResponse, ApiError]:
        """Approve an agent (also known as an API Wallet).

        POST /exchange

        Args:
            agent (str): The address of the agent to approve.
            name (str | None): The name of the agent to approve.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.ApproveAgentResponse, ApiError]): A Result containing the response from approving the agent.
        """
        # TODO:
        # Discord (`#api-announcements`, 2024-09-10): A custom expiration can be added to the
        # ApproveAgent action by appending valid_until {timestamp} to the name field.
        # The expiration can be at most 180 days in the future.
        nonce = get_timestamp_ms()
        action: ApproveAgentAction = {
            "type": "approveAgent",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "agentAddress": agent,
            "agentName": name,
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[ApproveAgentResponse, ApiError], response)

    async def set_referrer(self, code: str) -> Result[SetReferrerResponse, ApiError]:
        """Set a referrer.

        POST /exchange

        Args:
            code (str): The code of the referrer to set.

        Returns:
            (Result[hl.types.SetReferrerResponse, ApiError]): A Result containing the response from setting the referrer.
        """
        set_referrer_action: SetReferrerAction = {
            "type": "setReferrer",
            "code": code,
        }
        response = await self._sign_and_invoke(set_referrer_action)
        return cast(Result[SetReferrerResponse, ApiError], response)

    async def create_vault(
        self,
        name: str,
        description: str,
        initial_usd: Decimal,
    ) -> Result[CreateVaultResponse, ApiError]:
        """Create a vault.

        POST /exchange

        Returns:
            (Result[hl.types.CreateVaultResponse, ApiError]): A Result containing the response from creating the vault.
        """
        # NOTE: This method is not documented in the API reference.
        nonce = get_timestamp_ms()
        # Convert value 200 USD == 200_000_000
        create_vault_action: CreateVaultAction = {
            "type": "createVault",
            "name": name,
            "description": description,
            "initialUsd": to_minor_unit(initial_usd, "USDC"),
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(create_vault_action, nonce=nonce)
        return cast(Result[CreateVaultResponse, ApiError], response)

    async def register_referrer(
        self, *, code: str, account: Account | None = None
    ) -> Result[RegisterReferrerResponse, ApiError]:
        """Register a referrer.

        POST /exchange

        Args:
            code (str): The code of the referrer to register.
            account (Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.RegisterReferrerResponse, ApiError]): A Result containing the response from registering the referrer.
        """
        # NOTE: This method is not documented in the API reference.
        register_referrer_action: RegisterReferrerAction = {
            "type": "registerReferrer",
            "code": code,
        }
        response = await self._sign_and_invoke(
            register_referrer_action, account=account
        )
        return cast(Result[RegisterReferrerResponse, ApiError], response)

    async def cancel_order(
        self,
        *,
        asset: int | str,
        order_id: int,
        account: Account | None = None,
    ) -> Result[CancelResponse, ApiError]:
        """Cancel an order by its oid.

        Args:
            asset (int | str): The asset to cancel the order on.
            order_id (int): The oid of the order to cancel.
            account (hl.account.Account | None): The account to use for the order. Defaults to the class-level account.

        Returns:
            (Result[hl.types.CancelResponse, ApiError]): A Result containing the response from cancelling the order.
        """
        return await self.cancel_orders(
            cancel_requests=[{"asset": asset, "order_id": order_id}],
            account=account,
        )

    async def cancel_orders_by_id(
        self, cancel_requests: list[CancelByCloidParams]
    ) -> Result[CancelByCloidResponse, ApiError]:
        """Cancel one or more orders by their client order id.

        POST /exchange

        Args:
            cancel_requests (list[hl.types.CancelByCloidParams]): The orders to cancel.

        Returns:
            (Result[hl.types.CancelByCloidResponse, ApiError]): A Result containing the response from cancelling the orders.
        """
        cancel_action: CancelByCloidAction = {
            "type": "cancelByCloid",
            "cancels": [
                {
                    "asset": self.universe.to_asset_id(cancel["asset"]),
                    "cloid": cancel["client_order_id"]
                    if isinstance(cancel["client_order_id"], str)
                    else cancel["client_order_id"].to_raw(),
                }
                for cancel in cancel_requests
            ],
        }
        response = await self._sign_and_invoke(cancel_action)
        return cast(Result[CancelByCloidResponse, ApiError], response)

    async def cancel_order_by_id(
        self, asset: int | str, client_order_id: Cloid | str
    ) -> Result[CancelByCloidResponse, ApiError]:
        """Cancel an order by its client order id.

        POST /exchange

        Args:
            asset (int | str): The asset to cancel the order on.
            client_order_id (hl.types.Cloid | str): The client order id to cancel the order by.

        Returns:
            (Result[hl.types.CancelByCloidResponse, ApiError]): A Result containing the response from cancelling the order.
        """
        return await self.cancel_orders_by_id(
            [{"asset": asset, "client_order_id": client_order_id}]
        )

    async def send_spot(
        self,
        *,
        asset: int | str,
        amount: Decimal,
        destination: str,
        account: Account | None = None,
    ) -> Result[SpotSendResponse, ApiError]:
        """Send a spot asset to another address.

        POST /exchange

        Args:
            asset (int | str): The asset to send.
            amount (Decimal): The amount of the coin to send.
            destination (str): The address to send the coin to.
            account (hl.account.Account | None): The account to use for the request from which tokens are sent. Defaults to the class-level account.

        Returns:
            (Result[hl.types.SpotSendResponse, ApiError]): A Result containing the response from sending the spot asset.
        """
        # NOTE: API docs state that the token should be in the format of tokenName:tokenId
        # where tokenId is the token's address on the chain, however, so far the name was
        # sufficient.
        nonce = get_timestamp_ms()
        action: SpotSendAction = {
            "type": "spotSend",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "destination": destination,
            "token": self.universe.to_asset_name(asset),
            "amount": str(amount),
            "time": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[SpotSendResponse, ApiError], response)

    async def withdraw_funds(
        self, *, amount: Decimal, destination: str, account: Account | None = None
    ) -> Result[WithdrawResponse, ApiError]:
        """Withdraw USDC via Arbitrum.

        POST /exchange

        Args:
            amount (Decimal): The amount of USDC to withdraw.
            destination (str): The address to withdraw the USDC to.
            account (hl.account.Account | None): The account to use for the request from which USDC are sent. Defaults to the class-level account.

        Returns:
            (Result[hl.types.WithdrawResponse, ApiError]): A Result containing the response from withdrawing the USDC.
        """
        nonce = get_timestamp_ms()
        action: WithdrawAction = {
            "type": "withdraw3",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "amount": str(amount),
            "destination": destination,
            "time": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[WithdrawResponse, ApiError], response)

    async def transfer_usd(
        self, *, amount: Decimal, to_perp: bool, account: Account | None = None
    ) -> Result[UsdClassTransferResponse, ApiError]:
        """Transfer USDC between a user's spot wallet and their perp wallet and vice versa.

        POST /exchange

        Args:
            amount (Decimal): The amount of USDC to transfer.
            to_perp (bool): Whether to transfer the USDC to the perp wallet (True) or to the spot wallet (False).
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.UsdClassTransferResponse, ApiError]): A Result containing the response from transferring the USDC.
        """
        str_amount = str(amount)
        if self._resolve_signer(account).account.vault_address:
            # NOTE: This approach is only found in the reference implementation not in docs.
            str_amount = (
                f"{str_amount} {self._resolve_signer(account).account.vault_address}"
            )

        nonce = get_timestamp_ms()
        action: UsdClassTransferAction = {
            "type": "usdClassTransfer",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "amount": str_amount,
            "toPerp": to_perp,
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[UsdClassTransferResponse, ApiError], response)

    async def transfer_tokens(
        self,
        *,
        amount: Decimal,
        to_perp: bool,
        dex: str,
        token: str,
        account: Account | None = None,
    ) -> Result[PerpDexClassTransferResponse, ApiError]:
        """Transfer a token from a user's spot wallet to their perp wallet and vice versa.

        POST /exchange

        Args:
            amount (Decimal): The amount of the token to transfer.
            to_perp (bool): Whether to transfer the token to the perp wallet (True) or to the spot wallet (False).
            dex (str): The name of the dex to transfer the token from.
            token (str): The name of the token to transfer.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.PerpDexClassTransferResponse, ApiError]): A Result containing the response from transferring the token.
        """
        # TODO: Not tested
        nonce = get_timestamp_ms()
        action: PerpDexClassTransferAction = {
            "type": "perpDexClassTransfer",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "amount": str(amount),
            "toPerp": to_perp,
            "dex": dex,
            "token": token,
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[PerpDexClassTransferResponse, ApiError], response)

    async def stake_tokens(
        self,
        *,
        amount: Decimal,
        account: Account | None = None,
    ) -> Result[DepositStakingResponse, ApiError]:
        """Stake HYPE tokens.

        POST /exchange

        Args:
            amount (Decimal): The amount of HYPE to stake.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.DepositStakingResponse, ApiError]): A Result containing the response from staking HYPE tokens.
        """
        nonce = get_timestamp_ms()
        action: DepositStakingAction = {
            "type": "cDeposit",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "wei": to_minor_unit(amount, "HYPE"),
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[DepositStakingResponse, ApiError], response)

    async def unstake_tokens(
        self, *, amount: Decimal, account: Account | None = None
    ) -> Result[WithdrawStakingResponse, ApiError]:
        """Unstake HYPE tokens.

        POST /exchange

        Args:
            amount (Decimal): The amount of HYPE to unstake.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.WithdrawStakingResponse, ApiError]): A Result containing the response from unstaking HYPE tokens.
        """
        nonce = get_timestamp_ms()
        action: WithdrawStakingAction = {
            "type": "cWithdraw",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            "wei": to_minor_unit(amount, "HYPE"),
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[WithdrawStakingResponse, ApiError], response)

    async def delegate_tokens(
        self,
        *,
        validator: str,
        amount: Decimal,
        is_undelegate: bool,
        account: Account | None = None,
    ) -> Result[TokenDelegateResponse, ApiError]:
        """Delegate or undelegate HYPE tokens to or from a validator.

        Note that delegations to a particular validator have a lockup duration of 1 day.

        POST /exchange

        Args:
            validator (str): The address to delegate to or to undelegate from.
            amount (Decimal): The amount of HYPE to delegate or undelegate.
            is_undelegate (bool): Whether the action is to undelegate or delegate an amount.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.TokenDelegateResponse, ApiError]): A Result containing the response from delegating to or undelegating from staking.
        """
        nonce = get_timestamp_ms()
        action: TokenDelegateAction = {
            "type": "tokenDelegate",
            "hyperliquidChain": self.transport.network["name"],
            "signatureChainId": self.transport.network["signature_chain_id"],
            "validator": validator,
            "wei": to_minor_unit(amount, "HYPE"),
            "isUndelegate": is_undelegate,
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[TokenDelegateResponse, ApiError], response)

    async def transfer_vault_funds(
        self,
        *,
        vault: str,
        amount: Decimal,
        is_deposit: bool,
        account: Account | None = None,
    ) -> Result[VaultTransferResponse, ApiError]:
        """Transfer USDC to or from a vault.

        POST /exchange

        Args:
            vault (str): The address of the vault to transfer USDC to or from.
            amount (Decimal): The amount of USDC to transfer.
            is_deposit (bool): Whether to transfer USDC to the vault (True) or from the vault (False).
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.VaultTransferResponse, ApiError]): A Result containing the response from transferring USDC to or from the vault.
        """
        action: VaultTransferAction = {
            "type": "vaultTransfer",
            "vaultAddress": vault,
            "isDeposit": is_deposit,
            "usd": to_minor_unit(amount, "USDC"),
        }
        response = await self._sign_and_invoke(action, account=account)
        return cast(Result[VaultTransferResponse, ApiError], response)

    async def approve_builder(
        self, *, builder: str, max_fee_rate: Decimal, account: Account | None = None
    ) -> Result[ApproveBuilderFeeResponse, ApiError]:
        """Approve a builder with a maximum fee rate.

        POST /exchange

        Args:
            builder (str): The address of the builder to approve.
            max_fee_rate (Decimal): The maximum fee rate to approve for the builder. Decimal percentage (e.g. 0.01 for 1%) must be between 0 and 1.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.ApproveBuilderFeeResponse, ApiError]): A Result containing the response from approving the builder.
        """
        nonce = get_timestamp_ms()
        action: ApproveBuilderFeeAction = {
            "type": "approveBuilderFee",
            "hyperliquidChain": self.transport.network["name"],  # Mainnet or Testnet
            "signatureChainId": self.transport.network["signature_chain_id"],
            # TODO: Validate number of decimals / significant figures
            "maxFeeRate": f"{str(max_fee_rate * 100)}%",
            "builder": builder,
            "nonce": nonce,
        }
        response = await self._sign_and_invoke(action, nonce=nonce, account=account)
        return cast(Result[ApproveBuilderFeeResponse, ApiError], response)

    async def place_twap(
        self,
        *,
        asset: int | str,
        size: Decimal,
        minutes: int,
        randomize: bool,
        is_buy: bool,
        reduce_only: bool = False,
        account: Account | None = None,
    ) -> Result[TwapOrderResponse, ApiError]:
        """Place a TWAP order.

        POST /exchange

        Args:
            asset (int | str): The asset to place the TWAP order on.
            size (decimal.Decimal): The size of the TWAP order.
            minutes (int): The number of minutes this TWAP order should run for.
            randomize (bool): Whether to randomize the TWAP order.
            is_buy (bool): Whether the TWAP order is a buy order.
            reduce_only (bool): Whether the order is a reduce-only order.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.TwapOrderResponse, ApiError]): A Result containing the response from placing a TWAP order.
        """
        action: TwapOrderAction = {
            "type": "twapOrder",
            "twap": {
                "a": self.universe.to_asset_id(asset),
                "b": is_buy,
                "s": str(size),
                "r": reduce_only,
                "m": minutes,
                "t": randomize,
            },
        }
        response = await self._sign_and_invoke(action, account=account)
        return cast(Result[TwapOrderResponse, ApiError], response)

    async def cancel_twap(
        self,
        *,
        asset: str | int,
        twap_id: int,
        account: Account | None = None,
    ) -> Result[TwapCancelResponse, ApiError]:
        """Cancel a TWAP order.

        POST /exchange

        Args:
            asset (str|int): The asset id or name of the twap order to cancel.
            twap_id (int): The id of the TWAP order to cancel.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.TwapCancelResponse, ApiError]): A Result containing the response from canceling the TWAP order.
        """
        action: TwapCancelAction = {
            "type": "twapCancel",
            "a": self.universe.to_asset_id(asset),
            "t": twap_id,
        }
        response = await self._sign_and_invoke(action, account=account)
        return cast(Result[TwapCancelResponse, ApiError], response)

    async def reserve_weight(
        self, *, weight: int, account: Account | None = None
    ) -> Result[ReserveRequestWeightResponse, ApiError]:
        """Reserve additional request weight which counts against the rate limit.

        Instead of trading to increase the address based rate limits, this action allows reserving additional actions for 0.0005 USDC per request

        Args:
            weight (int): The number of actions for which to purchase request weight.
            account (hl.account.Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.ReserveRequestWeightResponse, ApiError]): A Result containing the response from reserving additional request weight.
        """
        action: ReserveRequestWeightAction = {
            "type": "reserveRequestWeight",
            "weight": weight,
        }
        response = await self._sign_and_invoke(action, account=account)
        return cast(Result[ReserveRequestWeightResponse, ApiError], response)

    async def create_sub_account(
        self, name: str
    ) -> Result[CreateSubAccountResponse, ApiError]:
        """Create a subaccount.

        POST /exchange

        Args:
            name (str): The name of the subaccount to create.

        Returns:
            (Result[hl.types.CreateSubAccountResponse, ApiError]): A Result containing the response from creating the subaccount.
        """
        create_sub_account_action: CreateSubAccountAction = {
            "type": "createSubAccount",
            "name": name,
        }
        response = await self._sign_and_invoke(create_sub_account_action)
        return cast(Result[CreateSubAccountResponse, ApiError], response)

    async def transfer_account_funds(
        self,
        *,
        amount: Decimal,
        address: str,
        is_deposit: bool,
        account: Account | None = None,
    ) -> Result[SubAccountTransferResponse, ApiError]:
        """Transfer USDC between a user's main account and a subaccount.

        POST /exchange

        Args:
            amount (Decimal): The amount of USDC to transfer.
            address (str): The address of the subaccount to transfer the USDC to.
            is_deposit (bool): Whether to transfer the USDC to the subaccount (True) or to the main account (False).
            account (Account | None): The account to use for the request. Defaults to the class-level account.

        Returns:
            (Result[hl.types.SubAccountTransferResponse, ApiError]): A Result containing the response from transferring the USDC.
        """
        sub_account_transfer_action: SubAccountTransferAction = {
            "type": "subAccountTransfer",
            "subAccountUser": address,
            "isDeposit": is_deposit,
            "usd": str(amount),
        }
        response = await self._sign_and_invoke(
            sub_account_transfer_action, account=account
        )
        return cast(Result[SubAccountTransferResponse, ApiError], response)
