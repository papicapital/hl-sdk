class Cloid:
    """A Cloid (client order id) allows for a client to track specific orders."""

    def __init__(self, raw_cloid: str):
        """Create a Cloid from a hex string."""
        self._raw_cloid: str = raw_cloid
        self._validate()

    def _validate(self) -> None:
        assert self._raw_cloid[:2] == "0x", "cloid is not a hex string"
        assert len(self._raw_cloid[2:]) == 32, "cloid is not 16 bytes"

    def __eq__(self, other: object) -> bool:
        """Check if two Cloids are equal."""
        if not isinstance(other, Cloid):
            return False
        return self._raw_cloid == other._raw_cloid

    def __hash__(self) -> int:
        """Hash the Cloid."""
        return hash(self._raw_cloid)

    def __str__(self) -> str:
        """Get the Cloid as a string."""
        return self._raw_cloid

    def __repr__(self) -> str:
        """Get the Cloid as a string."""
        return f"Cloid({self._raw_cloid})"

    @staticmethod
    def from_int(cloid: int) -> "Cloid":
        """Create a Cloid from an integer."""
        return Cloid(f"{cloid:#034x}")

    @staticmethod
    def from_str(cloid: str) -> "Cloid":
        """Create a Cloid from a string."""
        return Cloid(cloid)

    def to_raw(self) -> str:
        """Get the raw cloid as a string."""
        return self._raw_cloid
