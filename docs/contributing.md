# Contributor Guide

## Installation and Setup

### Prerequisites

First, set up `uv` if you haven't already. `uv` is a fast Python package manager that we use for dependency management:

```bash
# Install uv (choose one method)
# Via pip
pip install uv

# Via homebrew (macOS)
brew install uv

# Via curl (Unix)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Project Setup

Now clone the GitHub repository and set up the development environment:

```bash
git clone git@github.com:papicapital/hl-sdk.git
cd hl-sdk/

# Install all dependencies including dev dependencies
uv sync --all-groups

# Run tests to verify everything is working
uv run pytest tests/
```

## Architecture Overview

The SDK is organized into several key modules:

- **`hl.api`**: Main entry point providing unified access to all endpoints
- **`hl.account`**: Authentication credentials and account management
- **`hl.info`**: Read-only information retrieval (market data, user state, etc.)
- **`hl.exchange`**: Write operations (placing orders, transfers, etc.)
- **`hl.ws`**: WebSocket client for real-time data connections
- **`hl.subscriptions`**: WebSocket subscription methods for real-time feeds
- **`hl.signer`**: Cryptographic signing for authenticated requests
- **`hl.types`**: Type definitions for all API requests and responses
- **`hl.transport`**: HTTP and WebSocket transport layers
- **`hl.universe`**: Asset metadata and ID/name resolution
- **`hl.errors`**: Error handling and exception definitions
- **`hl.result`**: Result type for explicit error handling
- **`hl.constants`**: Predefined constants for orders, sides, and groupings
- **`hl.cloid`**: Client order ID generation and management
- **`hl.validator`**: Request and response validation
- **`hl.network`**: Network configuration (mainnet/testnet)
- **`hl._lib`**: Utility functions

## Testing Framework

### Test Structure

Tests are organized in the `tests/` folder and follow a specific pattern for API testing:

```
tests/
├── fixtures/           # Captured API responses
│   ├── http/          # HTTP endpoint fixtures
│   └── ws/            # WebSocket fixtures
├── test_info.py       # Info endpoint tests
├── test_exchange.py   # Exchange endpoint tests
├── test_ws.py         # WebSocket tests
├── test_subscription.py # Subscription tests
├── mock_http_transport.py # HTTP mocking infrastructure
├── mock_ws_transport.py   # WebSocket mocking infrastructure
└── conftest.py        # Test configuration and fixtures
```

### Capture-Replay System

The SDK uses a sophisticated **capture-replay** system for testing:

1. **First run**: Tests make live requests against the testnet API
2. **Capture**: Request/response payloads are saved to fixture files
3. **Subsequent runs**: Tests replay captured responses without live requests

This approach provides:
- **Fast test execution** (no network calls after first run)
- **Consistent test results** (no dependency on live market conditions)
- **Offline development** capability

### Setting Up Environment Variables for Capture Mode

To run tests in capture mode (making live API calls), you need to provide authentication credentials via environment variables. Create a `.env` file in the project root:

```bash
# .env file
HL_ADDRESS=0x1234567890123456789012345678901234567890
HL_SECRET_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890

# Optional: Additional addresses for specific test scenarios
SUB_ACCOUNT_ADDRESS=0x...
VAULT_ADDRESS=0x...
AGENT_ADDRESS=0x...
SECOND_ADDRESS=0x...
VALIDATOR_ADDRESS=0x...
```

**Important**: Never commit the `.env` file to version control. Use testnet credentials only.

### Running Tests in Capture Mode

There are several ways to run tests with environment variables:

```bash
# Method 1: Using uv with --env-file
uv run --env-file=.env pytest tests/

# Method 2: Export variables in your shell
export HL_ADDRESS=0x1234567890123456789012345678901234567890
export HL_SECRET_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
uv run pytest tests/

# Method 3: Set variables inline (one-time usage)
HL_ADDRESS=0x... HL_SECRET_KEY=0x... uv run pytest tests/
```

When credentials are provided:
- Tests will make live API calls to the Hyperliquid testnet
- New fixture files will be created for any missing test scenarios
- Existing fixtures will be used for replay

When credentials are missing:
- Tests will only run in replay mode using existing fixtures
- Tests without fixtures will be skipped or fail

### Creating New Tests

#### Basic Test Structure

```python
async def test_all_mids(info_client: Info) -> None:
    """Test fetching all mids."""
    result = await info_client.all_mids()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    # Add specific assertions for your use case
```

#### Test Fixtures

The test system provides several fixtures automatically:

- **`info_client`**: Pre-configured `Info` instance with capture enabled
- **`exchange_client`**: Pre-configured `Exchange` instance with capture enabled
- **`ws_client`**: Pre-configured WebSocket client for real-time tests
- **`subscriptions_client`**: Pre-configured `Subscriptions` instance for WebSocket subscriptions

#### Capture File Management

Capture files follow the naming convention: `{module_name}-{method_name}.json`

Examples:
- `test_info-test_all_mids.json`
- `test_exchange-test_place_order.json`

**Important**: Renaming test modules or methods without renaming the corresponding capture file will result in new capture files being created on the next run.

#### Testing Authenticated Endpoints

For endpoints requiring authentication, ensure your test environment has proper credentials:

```python
async def test_user_state(info_client: Info) -> None:
    """Test fetching user state."""
    # This will use the test account configured in the fixture
    result = await info_client.user_state()
    assert result.is_ok()

    response = result.unwrap()
    assert "marginSummary" in response
    assert "crossMarginSummary" in response
```

#### Error Testing

Create tests for common error scenarios:

```python
async def test_invalid_asset(info_client: Info) -> None:
    """Test error handling for invalid asset."""
    result = await info_client.l2_book(asset="INVALID")
    assert result.is_err()

    error = result.unwrap_err()
    assert "not found" in str(error).lower()
```

### Running Tests

```bash
# Run all tests (replay mode if fixtures exist)
uv run pytest

# Run all tests in capture mode
uv run --env-file=.env pytest

# Run specific test file
uv run pytest tests/test_info.py

# Run specific test method
uv run pytest tests/test_info.py::test_all_mids

# Run with verbose output
uv run pytest -v

# Clear cache and run fresh
uv run pytest --cache-clear
```

### Test Coverage

Aim for comprehensive test coverage:

1. **Happy path**: At least one test for every public method
2. **Error cases**: Common error scenarios (invalid inputs, network errors)
3. **Edge cases**: Boundary conditions and special parameters
4. **Integration**: End-to-end workflows combining multiple methods

## Code Quality

### Type Safety

The SDK is fully typed using Python's type system:

- All public methods have complete type annotations
- Use `Result[T, ApiError]` for all API calls to handle errors explicitly
- Leverage the `hl.types` module for request/response types

### Error Handling

Follow the Result pattern consistently:

```python
# Good: Explicit error handling
result = await info.all_mids()
if result.is_err():
    print(f"Error: {result.unwrap_err()}")
    return

mids = result.unwrap()

# Bad: Assuming success
mids = await info.all_mids()  # This won't work!
```

### Documentation

- Add docstrings to all public methods
- Include parameter descriptions and examples
- Document any non-obvious behavior or limitations

## Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality and consistency. These hooks automatically run before each commit to catch issues early.

### Installation

Then install the hooks for this repository:

```bash
# Install the pre-commit hooks
uv run pre-commit install
```

### Configured Hooks

The project includes the following pre-commit hooks:

1. **mypy**: Type checking with strict mode enabled
2. **ruff-check**: Linting to catch code quality issues
3. **ruff-format**: Code formatting for consistent style
4. **pytest**: Running the test suite to ensure functionality

### Running Pre-commit

Pre-commit hooks will automatically run when you make a commit. However, you can also run them manually:

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run all hooks on staged files only
uv run pre-commit run
```

### Manual Quality Checks

You can also run the quality checks manually using uv:

```bash
# Type checking
uv run mypy hl tests

# Linting
uv run ruff check .

# Code formatting
uv run ruff format .

# Tests
uv run pytest --tb=short -v
```

### Fixing Issues

If pre-commit hooks fail:

1. **Formatting issues**: Run `uv run ruff format .` to auto-fix formatting
2. **Linting issues**: Run `uv run ruff check . --fix` to auto-fix where possible
3. **Type issues**: Address mypy errors by adding proper type annotations
4. **Test failures**: Fix the failing tests before committing

### Bypassing Pre-commit (Not Recommended)

In rare cases, you may need to bypass pre-commit hooks:

```bash
# Skip pre-commit hooks (use sparingly)
git commit --no-verify -m "your commit message"
```

**Note**: Only bypass hooks when absolutely necessary, as they help maintain code quality and prevent issues from reaching the main branch.

## Undocumented Methods

We implement some API methods which are not documented in Hyperliquid's official API docs. This enables more complete functionality and better integration with other documented methods.

These methods are reverse-engineered from:
- Hyperliquid's frontend application
- The official Python reference SDK
- Discord community discussions

| Method Name | Status | Source | Description | Notes |
|-------------|--------|---------|-------------|--------|
| `transfer_usd` | ✅ | Reference SDK | Transfer USDC between spot/perp wallets | Previously `usd_class_transfer` |
| `set_referrer` | ✅ | Reference SDK | Set referrer code for fee discounts | One-time operation |
| `transfer_account_funds` | ✅ | Reference SDK | Transfer between main/sub accounts | Previously `sub_account_transfer` |
| `vault_usd_transfer` | ❌ | Reference SDK | Transfer USDC to/from vaults | Planned implementation |
| `vault_summaries` | ❌ | [Discord](https://discord.com/channels/1029781241702129716/1208476333089497189/1287699362704523265) | Get vault performance summaries | Community requested |
| `vault_details` | ✅ | [Discord](https://discord.com/channels/1029781241702129716/1208476333089497189/1287699362704523265) | Get detailed vault information | Recently implemented |
| `convert_to_multi_sig_user` | ❌ | Reference SDK | Convert account to multi-signature | Advanced feature |
| `multi_sig` | ❌ | Reference SDK | Multi-signature operations | Advanced feature |

**Deprecated**: `user_spot_transfer` has been replaced by `transfer_usd` following the API's migration from `spotUser` to `usdClassTransfer`.

### Contributing Undocumented Methods

When implementing undocumented methods:

1. **Verify the source**: Ensure the method exists in the reference implementation or has community validation
2. **Add comprehensive tests**: Since these aren't officially documented, thorough testing is critical
3. **Document limitations**: Note any known issues or incomplete functionality

## Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Implement changes**: Follow the existing patterns and add comprehensive tests
3. **Run tests**: Ensure all tests pass with `uv run pytest`
4. **Update documentation**: Add/update docstrings and examples
5. **Submit PR**: Create a pull request with clear description of changes

## Getting Help

- **API Documentation**: [Hyperliquid Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/)
- **GitHub Issues**: Report bugs or request features via GitHub issues