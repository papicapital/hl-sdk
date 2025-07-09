from hl.types import Network

MAINNET_API_URL = "https://api.hyperliquid.xyz"
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"

MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"


MAINNET = Network(
    api_url=MAINNET_API_URL,
    ws_url=MAINNET_WS_URL,
    name="Mainnet",
    signature_chain_id="0xa4b1",
    phantom_agent_source="a",
)

TESTNET = Network(
    api_url=TESTNET_API_URL,
    ws_url=TESTNET_WS_URL,
    name="Testnet",
    signature_chain_id="0x66eee",
    phantom_agent_source="b",
)
