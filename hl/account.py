"""Account management for Hyperliquid API authentication."""

import logging
from dataclasses import dataclass, field

import eth_account
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Lightweight authentication credentials for Hyperliquid API.

    Contains only the essential authentication data, keeping chain
    configuration separate at the transport layer.

    Attributes:
        address: The Ethereum address for the account.
        secret_key: The private key for signing operations.
        vault_address: Optional vault address for vault-based operations.

    Examples:
        Create account with explicit address:
        >>> account = Account(
        ...     address="0x1234...",
        ...     secret_key="0xabcd...",
        ...     vault_address="0x5678..."  # optional
        ... )

        Create account from just a secret key:
        >>> account = Account.from_key("0xabcd...")
    """

    address: str
    secret_key: str
    vault_address: str | None = None

    local_account: LocalAccount = field(init=False)

    def __post_init__(self) -> None:
        """Validate the account on creation."""
        self.local_account = eth_account.Account.from_key(self.secret_key)
        self.validate()

    def validate(self) -> None:
        """Validate that address matches the derived address from secret_key."""
        derived_address = self.local_account.address
        if self.address.lower() != derived_address.lower():
            # Handle agent wallet scenario
            logger.warning(
                f"Address mismatch: provided {self.address}, using derived {derived_address}"
            )

    @classmethod
    def from_key(cls, secret_key: str, vault_address: str | None = None) -> "Account":
        """Create Account from just a secret key.

        Args:
            secret_key: The private key for the account.
            vault_address: Optional vault address for vault operations.

        Returns:
            Account instance with address derived from the secret key.
        """
        local_account = eth_account.Account.from_key(secret_key)
        return cls(local_account.address, secret_key, vault_address)
