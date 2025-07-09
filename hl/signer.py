from enum import StrEnum
from typing import Any, cast

# https://github.com/msgpack/msgpack-python/issues/448
import msgpack  # type: ignore
from eth_account.messages import SignableMessage, encode_typed_data
from eth_account.signers.local import LocalAccount
from eth_utils.conversions import to_hex
from eth_utils.crypto import keccak

from hl._lib import get_timestamp_ms
from hl.account import Account
from hl.types import Action, Network, Signature


class Signer:
    """Handles cryptographic signing for Hyperliquid API requests.

    The Signer class manages the cryptographic operations required to authenticate
    and authorize actions on the Hyperliquid exchange. It uses EIP-712 structured
    data signing for security and compatibility with Ethereum wallets.

    Note: This is an internal class. Users typically don't create Signer instances
    directly - they are created automatically by the Api class.

    Attributes:
        account: The account to use for signing.
    """

    account: Account

    def __init__(
        self,
        account: Account,
    ):
        """Initialize a Signer with the provided credentials.

        Args:
            account (hl.account.Account): The account to use for signing.

        Note:
            If the provided address doesn't match the address derived from the
            secret key, the derived address will be used (agent wallet scenario).
        """
        self.account = account

    def sign(
        self,
        action: Action,
        network: Network,
        *,
        nonce: int | None = None,
    ) -> tuple[Signature, int]:
        """Sign an action for submission to the Hyperliquid API.

        Creates a cryptographic signature for the given action using EIP-712
        structured data signing. Different action types use different signing
        methods (L1 actions vs user actions).

        Args:
            action (hl.types.Action): The action to sign (order, transfer, withdrawal, etc.).
            network (hl.network.Network): The network to use for signing.
            nonce (int | None): The nonce to use for signing. If not provided, the current timestamp will be used.

        Returns:
            (tuple[hl.types.Signature, int]): A tuple containing the signature and timestamp used for signing.
        """
        nonce = nonce or get_timestamp_ms()
        if action["type"] in ACTION_TO_MESSAGE_TYPE:
            return sign_user_action(
                self.account.local_account,
                ACTION_TO_MESSAGE_TYPE[action["type"]],
                action,
                network,
            ), nonce
        return (
            sign_l1_action(
                self.account.local_account,
                action,
                self.account.vault_address,
                nonce,
                network,
            ),
            nonce,
        )


L1_DOMAIN_DATA = {
    "chainId": 1337,
    "name": "Exchange",
    "verifyingContract": "0x0000000000000000000000000000000000000000",
    "version": "1",
}


def get_arb_domain_data(network: Network) -> dict[str, Any]:
    return {
        "name": "HyperliquidSignTransaction",
        "version": "1",
        "chainId": int(network["signature_chain_id"], 16),
        "verifyingContract": "0x0000000000000000000000000000000000000000",
    }


class PRIMARY_TYPE(StrEnum):
    """The primary type of a message signed by a user."""

    USD_SEND = "HyperliquidTransaction:UsdSend"
    SPOT_SEND = "HyperliquidTransaction:SpotSend"
    WITHDRAW = "HyperliquidTransaction:Withdraw"
    USD_CLASS_TRANSFER = "HyperliquidTransaction:UsdClassTransfer"
    SEND_MULTI_SIG = "HyperliquidTransaction:SendMultiSig"
    CONVERT_TO_MULTI_SIG_USER = "HyperliquidTransaction:ConvertToMultiSigUser"
    APPROVE_AGENT = "HyperliquidTransaction:ApproveAgent"
    APPROVE_BUILDER_FEE = "HyperliquidTransaction:ApproveBuilderFee"
    DEPOSIT_STAKING = "HyperliquidTransaction:CDeposit"
    WITHDRAW_STAKING = "HyperliquidTransaction:CWithdraw"
    TOKEN_DELEGATE = "HyperliquidTransaction:TokenDelegate"


MESSAGE_TYPES: dict[PRIMARY_TYPE, list[dict[str, str]]] = {
    PRIMARY_TYPE.USD_SEND: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "destination", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "time", "type": "uint64"},
    ],
    PRIMARY_TYPE.SPOT_SEND: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "destination", "type": "string"},
        {"name": "token", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "time", "type": "uint64"},
    ],
    PRIMARY_TYPE.WITHDRAW: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "destination", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "time", "type": "uint64"},
    ],
    PRIMARY_TYPE.USD_CLASS_TRANSFER: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "toPerp", "type": "bool"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.SEND_MULTI_SIG: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "multiSigActionHash", "type": "bytes32"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.CONVERT_TO_MULTI_SIG_USER: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "signers", "type": "string"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.APPROVE_AGENT: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "agentAddress", "type": "address"},
        {"name": "agentName", "type": "string"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.APPROVE_BUILDER_FEE: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "maxFeeRate", "type": "string"},
        {"name": "builder", "type": "address"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.DEPOSIT_STAKING: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "wei", "type": "uint64"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.WITHDRAW_STAKING: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "wei", "type": "uint64"},
        {"name": "nonce", "type": "uint64"},
    ],
    PRIMARY_TYPE.TOKEN_DELEGATE: [
        {"name": "hyperliquidChain", "type": "string"},
        {"name": "validator", "type": "address"},
        {"name": "wei", "type": "uint64"},
        {"name": "isUndelegate", "type": "bool"},
        {"name": "nonce", "type": "uint64"},
    ],
}


ACTION_TO_MESSAGE_TYPE: dict[str, PRIMARY_TYPE] = {
    "usdSend": PRIMARY_TYPE.USD_SEND,
    "spotSend": PRIMARY_TYPE.SPOT_SEND,
    "withdraw3": PRIMARY_TYPE.WITHDRAW,
    "usdClassTransfer": PRIMARY_TYPE.USD_CLASS_TRANSFER,
    "approveAgent": PRIMARY_TYPE.APPROVE_AGENT,
    "approveBuilderFee": PRIMARY_TYPE.APPROVE_BUILDER_FEE,
    "convertToMultiSigUser": PRIMARY_TYPE.CONVERT_TO_MULTI_SIG_USER,
    "cDeposit": PRIMARY_TYPE.DEPOSIT_STAKING,
    "cWithdraw": PRIMARY_TYPE.WITHDRAW_STAKING,
    "tokenDelegate": PRIMARY_TYPE.TOKEN_DELEGATE,
}


def address_to_bytes(address: str) -> bytes:
    return bytes.fromhex(address[2:] if address.startswith("0x") else address)


def action_hash(action: Action, vault_address: str | None, nonce: int) -> bytes:
    data = cast(bytes, msgpack.packb(action))
    data += nonce.to_bytes(8, "big")
    if vault_address is None:
        data += b"\x00"
    else:
        data += b"\x01"
        data += address_to_bytes(vault_address)
    return keccak(data)


def sign_message(wallet: LocalAccount, signable: SignableMessage) -> Signature:
    signed = wallet.sign_message(signable)
    return Signature(r=to_hex(signed["r"]), s=to_hex(signed["s"]), v=signed["v"])


def sign_l1_action(
    wallet: LocalAccount,
    action: Action,
    vault_address: str | None,
    nonce: int,
    network: Network,
) -> Signature:
    hash = action_hash(action, vault_address, nonce)
    phantom_agent = {"source": network["phantom_agent_source"], "connectionId": hash}
    message = encode_typed_data(
        domain_data=L1_DOMAIN_DATA,
        message_types={
            "Agent": [
                {"name": "source", "type": "string"},
                {"name": "connectionId", "type": "bytes32"},
            ]
        },
        message_data=phantom_agent,
    )
    return sign_message(wallet, message)


def sign_user_action(
    wallet: LocalAccount, key: PRIMARY_TYPE, action: Action, network: Network
) -> Signature:
    # User actions are actions which cannot be performed by agents (API wallets).
    signable = encode_typed_data(
        domain_data=get_arb_domain_data(network),
        message_types={key: MESSAGE_TYPES[key]},
        message_data=cast(dict[str, Any], action),
    )
    return sign_message(wallet, signable)
