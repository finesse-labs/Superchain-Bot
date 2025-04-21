from config import UNICHAIN_RPC


class Chain:
    def __init__(self, chain_id: int, rpc: str, scan: str, native_token: str) -> None:
        self.chain_id = chain_id
        self.rpc = rpc
        self.scan = scan
        self.native_token = native_token


UNICHAIN = Chain(
    chain_id=130,
    rpc=UNICHAIN_RPC,
    scan='https://unichain.blockscout.com/tx',
    native_token='ETH'
)

BASE = Chain(
    chain_id=8453,
    rpc='https://base.meowrpc.com',
    scan='https://basescan.org/tx',
    native_token='ETH'
)

OP = Chain(
    chain_id=10,
    rpc='https://optimism.drpc.org',
    scan='https://optimistic.etherscan.io/tx',
    native_token='ETH',
)

ARB = Chain(
    chain_id=42161,
    rpc='https://arbitrum.meowrpc.com',
    scan='https://arbiscan.io/tx',
    native_token='ETH',
)

SEPOLIA = Chain(
    chain_id=11155111,
    rpc='https://ethereum-sepolia-rpc.publicnode.com',
    scan='https://sepolia.etherscan.io/tx',
    native_token='ETH'  # sETH
)

ZORA = Chain(
    chain_id=7777777,
    rpc='https://rpc.zora.energy',
    scan='https://explorer.zora.energy/tx',
    native_token='ETH'
)

MODE = Chain(
    chain_id=34443,
    rpc='https://mode.drpc.org',
    scan='https://explorer.mode.network/tx',
    native_token='ETH'
)

LISK = Chain(
    chain_id=1135,
    rpc='https://lisk.drpc.org',
    scan='https://blockscout.lisk.com/tx',
    native_token='ETH'
)

INK = Chain(
    chain_id=57073,
    rpc='https://ink.drpc.org',
    scan='https://explorer.inkonchain.com/tx',
    native_token='ETH'
)

SONEIUM = Chain(
    chain_id=1868,
    rpc='https://rpc.soneium.org',
    scan='https://soneium.blockscout.com/tx',
    native_token='ETH'
)

SWELL = Chain(
    chain_id=1923,
    rpc='https://rpc.ankr.com/swell',
    scan='https://explorer.swellnetwork.io/tx',
    native_token='ETH'
)

chain_mapping = {
    'BASE': BASE,
    'ARBITRUM ONE': ARB,
    'ARB': ARB,
    'OP': OP,
    'OPTIMISM': OP,
    'SEPOLIA': SEPOLIA,
    'UNICHAIN': UNICHAIN,
    'ZORA': ZORA,
    'MODE': MODE,
    'LISK': LISK,
    'INK': INK,
    'SONEIUM': SONEIUM,
    'SWELL': SWELL
}
