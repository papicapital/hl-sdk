from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal

import pytest

from hl import Universe
from hl.types import AssetInfo


@pytest.fixture
def mock_universe() -> Universe:
    """Create a mock universe with various asset types for testing."""
    id_to_info = {
        # PERPETUAL asset with pxDecimals=1 (MAX_DECIMALS_PERPETUAL=6, szDecimals=5)
        1: AssetInfo(
            id=1,
            name="BTC",
            type="PERPETUAL",
            pxDecimals=1,
            szDecimals=5,
        ),
        # PERPETUAL asset with pxDecimals=3 (MAX_DECIMALS_PERPETUAL=6, szDecimals=3)
        2: AssetInfo(
            id=2,
            name="ETH",
            type="PERPETUAL",
            pxDecimals=3,
            szDecimals=3,
        ),
        # SPOT asset with pxDecimals=2 (MAX_DECIMALS_SPOT=8, szDecimals=6)
        10000: AssetInfo(
            id=10000,
            name="BTC/USDC",
            type="SPOT",
            pxDecimals=2,
            szDecimals=6,
        ),
        # SPOT asset with pxDecimals=5 (MAX_DECIMALS_SPOT=8, szDecimals=3)
        10001: AssetInfo(
            id=10001,
            name="ETH/USDC",
            type="SPOT",
            pxDecimals=5,
            szDecimals=3,
        ),
    }
    return Universe(id_to_info)


@pytest.mark.parametrize(
    "asset,input_price,expected_price,description",
    [
        # Test integers (should always be preserved)
        ("BTC", Decimal("100"), Decimal("100"), "integer price unchanged"),
        ("BTC", Decimal("1"), Decimal("1"), "integer 1 unchanged"),
        ("BTC", Decimal("12345"), Decimal("12345"), "large integer unchanged"),
        ("ETH", Decimal("3000"), Decimal("3000"), "integer for ETH unchanged"),
        # Test prices within both rules (≤5 sig figs and ≤pxDecimals decimals)
        ("BTC", Decimal("100.5"), Decimal("100.5"), "price within both rules"),
        (
            "ETH",
            Decimal("3000.123"),
            Decimal("3000.1"),
            "price within both rules for ETH",
        ),
        (
            "BTC/USDC",
            Decimal("50000.12"),
            Decimal("5E+4"),
            "spot price within both rules",
        ),
        # Test significant figures rule (>5 sig figs, but within decimal limit)
        ("ETH", Decimal("12345.6"), Decimal("12346"), "round to 5 sig figs"),
        ("ETH", Decimal("1234.56"), Decimal("1234.6"), "round to 5 sig figs"),
        ("ETH", Decimal("123.456"), Decimal("123.46"), "round to 5 sig figs"),
        ("ETH", Decimal("12.3456"), Decimal("12.346"), "round to 5 sig figs"),
        ("ETH", Decimal("1.23456"), Decimal("1.235"), "round to 5 sig figs"),
        # Test decimal places rule (≤5 sig figs but too many decimals)
        ("BTC", Decimal("100.12"), Decimal("100.1"), "round to pxDecimals=1"),
        ("BTC", Decimal("50.99"), Decimal("51.0"), "round to pxDecimals=1"),
        (
            "BTC/USDC",
            Decimal("1000.123"),
            Decimal("1000.1"),
            "round to pxDecimals=2",
        ),
        # Test both rules violated (should use less restrictive constraint)
        (
            "BTC",
            Decimal("12345.67"),
            Decimal("12346"),
            "both rules violated, sig figs less restrictive",
        ),
        (
            "ETH",
            Decimal("123456.789"),
            Decimal("1.2346E+5"),
            "both rules violated, sig figs less restrictive",
        ),
        # Test very small numbers
        (
            "ETH",
            Decimal("0.001234"),
            Decimal("0.001"),
            "small number rounded to pxDecimals",
        ),
        (
            "ETH",
            Decimal("0.0012345"),
            Decimal("0.001"),
            "small number rounded to pxDecimals",
        ),
        (
            "BTC/USDC",
            Decimal("0.00123456"),
            Decimal("0"),
            "small spot number rounded",
        ),
        # Test very large numbers (integers are preserved)
        (
            "ETH",
            Decimal("123456"),
            Decimal("123456"),
            "large integer unchanged",
        ),
        (
            "ETH",
            Decimal("1234567"),
            Decimal("1234567"),
            "very large integer unchanged",
        ),
        # Test edge cases with zeros
        ("BTC", Decimal("0"), Decimal("0"), "zero unchanged"),
        ("ETH", Decimal("0.0"), Decimal("0"), "zero with decimal unchanged"),
        ("BTC", Decimal("100.0"), Decimal("100"), "trailing zero removed"),
        # Test different asset access methods (by ID vs name)
        (1, Decimal("100.5"), Decimal("100.5"), "access by asset ID"),
        (2, Decimal("3000.123"), Decimal("3000.1"), "access by asset ID for ETH"),
        # Test specific edge cases for different pxDecimals
        (
            "BTC/USDC",
            Decimal("12345.678"),
            Decimal("12346"),
            "spot asset sig figs rule",
        ),
        (
            "ETH/USDC",
            Decimal("1000.123456"),
            Decimal("1000.1"),
            "spot asset with pxDecimals=5",
        ),
        # Test normalization behavior
        (
            "ETH",
            Decimal("1000.000"),
            Decimal("1000"),
            "normalize removes trailing zeros",
        ),
        (
            "ETH",
            Decimal("0001000.500"),
            Decimal("1000.5"),
            "normalize removes leading zeros",
        ),
    ],
)
def test_round_price(
    mock_universe: Universe,
    asset: int | str,
    input_price: Decimal,
    expected_price: Decimal,
    description: str,
) -> None:
    """Test round_price with various input scenarios."""
    result = mock_universe.round_price(asset, input_price)
    assert result == expected_price, (
        f"Failed for {description}: expected {expected_price}, got {result}"
    )


@pytest.mark.parametrize(
    "asset_name,input_price,rounding_mode,expected_price",
    [
        # Test different rounding modes
        ("BTC", Decimal("100.15"), ROUND_HALF_EVEN, Decimal("100.2")),
        ("BTC", Decimal("100.15"), ROUND_UP, Decimal("100.2")),
        ("BTC", Decimal("100.15"), ROUND_DOWN, Decimal("100.1")),
        (
            "BTC",
            Decimal("100.25"),
            ROUND_HALF_EVEN,
            Decimal("100.2"),
        ),  # Even rounding
        (
            "BTC",
            Decimal("100.35"),
            ROUND_HALF_EVEN,
            Decimal("100.4"),
        ),  # Even rounding
        # Test rounding modes with significant figures
        ("ETH", Decimal("12345.5"), ROUND_HALF_EVEN, Decimal("12346")),
        ("ETH", Decimal("12345.5"), ROUND_UP, Decimal("12346")),
        ("ETH", Decimal("12345.5"), ROUND_DOWN, Decimal("12345")),
    ],
)
def test_round_price_rounding_modes(
    mock_universe: Universe,
    asset_name: str,
    input_price: Decimal,
    rounding_mode: str,
    expected_price: Decimal,
) -> None:
    """Test round_price with different rounding modes."""
    result = mock_universe.round_price(asset_name, input_price, rounding_mode)
    assert result == expected_price


def test_round_price_invalid_asset(mock_universe: Universe) -> None:
    """Test round_price with invalid asset raises KeyError."""
    with pytest.raises(KeyError):
        mock_universe.round_price("INVALID", Decimal("100.5"))


@pytest.mark.parametrize(
    "input_price,description",
    [
        (Decimal("inf"), "positive infinity"),
        (Decimal("-inf"), "negative infinity"),
        (Decimal("nan"), "NaN"),
    ],
)
def test_round_price_special_values(
    mock_universe: Universe,
    input_price: Decimal,
    description: str,
) -> None:
    """Test round_price with special Decimal values."""
    # The current implementation should handle these gracefully
    result = mock_universe.round_price("BTC", input_price)
    # For special values, we expect them to be returned as-is
    if description == "NaN":
        assert result.is_nan(), f"Failed for {description}: expected NaN, got {result}"
    else:
        assert result == input_price, f"Failed for {description}"


def test_round_price_precision_edge_cases(mock_universe: Universe) -> None:
    """Test edge cases around precision boundaries."""
    # Test exactly 5 significant figures
    result = mock_universe.round_price("ETH", Decimal("12345"))
    assert result == Decimal("12345")

    # Test exactly pxDecimals decimal places
    result = mock_universe.round_price("BTC", Decimal("100.1"))
    assert result == Decimal("100.1")

    # Test just over 5 significant figures (but integers are preserved)
    result = mock_universe.round_price("ETH", Decimal("123456"))
    assert result == Decimal("123456")

    # Test just over pxDecimals
    result = mock_universe.round_price("BTC", Decimal("100.11"))
    assert result == Decimal("100.1")


def test_round_price_very_small_numbers(mock_universe: Universe) -> None:
    """Test round_price with very small numbers."""
    # Test numbers smaller than tick size - will be rounded to 0 due to pxDecimals=3
    result = mock_universe.round_price("ETH", Decimal("0.0001234"))
    expected = Decimal("0")  # Rounded to pxDecimals=3, so 0.000 becomes 0
    assert result == expected

    # Test very small number with too many sig figs
    result = mock_universe.round_price("ETH", Decimal("0.00012345"))
    expected = Decimal("0")  # Same issue, rounds to 0
    assert result == expected


def test_round_price_consistency(mock_universe: Universe) -> None:
    """Test that round_price is consistent and deterministic."""
    price = Decimal("12345.6789")

    # Multiple calls should return the same result
    result1 = mock_universe.round_price("ETH", price)
    result2 = mock_universe.round_price("ETH", price)
    result3 = mock_universe.round_price("ETH", price)

    assert result1 == result2 == result3

    # Result should be the same regardless of input format
    result_str = mock_universe.round_price("ETH", Decimal("12345.6789"))
    result_float = mock_universe.round_price("ETH", Decimal(12345.6789))

    assert result_str == result_float


# Tests for round_size method


@pytest.mark.parametrize(
    "asset,input_size,expected_size,description",
    [
        # Test BTC with szDecimals=5
        (
            "BTC",
            Decimal("1.123456"),
            Decimal("1.12346"),
            "BTC size rounded to 5 decimals",
        ),
        (
            "BTC",
            Decimal("10.000001"),
            Decimal("10.00000"),
            "BTC size rounded to 5 decimals",
        ),
        ("BTC", Decimal("0.123456789"), Decimal("0.12346"), "BTC small size rounded"),
        # Test ETH with szDecimals=3
        (
            "ETH",
            Decimal("5.123456"),
            Decimal("5.123"),
            "ETH size rounded to 3 decimals",
        ),
        ("ETH", Decimal("100.999999"), Decimal("101.000"), "ETH size rounded up"),
        ("ETH", Decimal("0.0001"), Decimal("0.000"), "ETH very small size"),
        # Test BTC/USDC with szDecimals=6
        (
            "BTC/USDC",
            Decimal("0.1234567"),
            Decimal("0.123457"),
            "BTC/USDC size rounded to 6 decimals",
        ),
        (
            "BTC/USDC",
            Decimal("1000.12345678"),
            Decimal("1000.123457"),
            "BTC/USDC large size",
        ),
        # Test ETH/USDC with szDecimals=3
        (
            "ETH/USDC",
            Decimal("50.123456"),
            Decimal("50.123"),
            "ETH/USDC size rounded to 3 decimals",
        ),
        # Test integers (should be preserved but formatted correctly)
        ("BTC", Decimal("10"), Decimal("10.00000"), "BTC integer size"),
        ("ETH", Decimal("5"), Decimal("5.000"), "ETH integer size"),
        # Test zero
        ("BTC", Decimal("0"), Decimal("0.00000"), "BTC zero size"),
        ("ETH", Decimal("0.0"), Decimal("0.000"), "ETH zero size"),
        # Test access by asset ID
        (1, Decimal("1.123456"), Decimal("1.12346"), "BTC by ID"),
        (2, Decimal("5.123456"), Decimal("5.123"), "ETH by ID"),
    ],
)
def test_round_size(
    mock_universe: Universe,
    asset: int | str,
    input_size: Decimal,
    expected_size: Decimal,
    description: str,
) -> None:
    """Test round_size with various input scenarios."""
    result = mock_universe.round_size(asset, input_size)
    assert result == expected_size, (
        f"Failed for {description}: expected {expected_size}, got {result}"
    )


@pytest.mark.parametrize(
    "asset_name,input_size,rounding_mode,expected_size",
    [
        # Test different rounding modes with BTC (szDecimals=5)
        (
            "BTC",
            Decimal("1.123455"),
            ROUND_HALF_EVEN,
            Decimal("1.12346"),
        ),  # Round up (even)
        (
            "BTC",
            Decimal("1.123445"),
            ROUND_HALF_EVEN,
            Decimal("1.12344"),
        ),  # Round down (even)
        ("BTC", Decimal("1.123455"), ROUND_UP, Decimal("1.12346")),
        ("BTC", Decimal("1.123455"), ROUND_DOWN, Decimal("1.12345")),
        # Test with ETH (szDecimals=3)
        (
            "ETH",
            Decimal("5.1235"),
            ROUND_HALF_EVEN,
            Decimal("5.124"),
        ),  # Round up (even)
        (
            "ETH",
            Decimal("5.1225"),
            ROUND_HALF_EVEN,
            Decimal("5.122"),
        ),  # Round down (even)
        ("ETH", Decimal("5.1235"), ROUND_UP, Decimal("5.124")),
        ("ETH", Decimal("5.1235"), ROUND_DOWN, Decimal("5.123")),
    ],
)
def test_round_size_rounding_modes(
    mock_universe: Universe,
    asset_name: str,
    input_size: Decimal,
    rounding_mode: str,
    expected_size: Decimal,
) -> None:
    """Test round_size with different rounding modes."""
    result = mock_universe.round_size(asset_name, input_size, rounding_mode)
    assert result == expected_size


def test_round_size_invalid_asset(mock_universe: Universe) -> None:
    """Test round_size with invalid asset raises KeyError."""
    with pytest.raises(KeyError):
        mock_universe.round_size("INVALID", Decimal("1.5"))


def test_round_size_special_values(mock_universe: Universe) -> None:
    """Test round_size with special Decimal values."""
    from decimal import InvalidOperation

    # Test infinity values - should raise InvalidOperation
    with pytest.raises(InvalidOperation):
        mock_universe.round_size("BTC", Decimal("inf"))

    with pytest.raises(InvalidOperation):
        mock_universe.round_size("BTC", Decimal("-inf"))

    # Test NaN - should return NaN
    result_nan = mock_universe.round_size("BTC", Decimal("nan"))
    assert result_nan.is_nan()


def test_round_size_consistency(mock_universe: Universe) -> None:
    """Test that round_size is consistent and deterministic."""
    size = Decimal("1.123456789")

    # Multiple calls should return the same result
    result1 = mock_universe.round_size("BTC", size)
    result2 = mock_universe.round_size("BTC", size)
    result3 = mock_universe.round_size("BTC", size)

    assert result1 == result2 == result3

    # Result should be the same regardless of input format
    result_str = mock_universe.round_size("BTC", Decimal("1.123456789"))
    result_float = mock_universe.round_size("BTC", Decimal(1.123456789))

    assert result_str == result_float
