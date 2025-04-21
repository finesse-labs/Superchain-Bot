import random

from src.modules import *
from src.utils.networks import *
from config import OMNICHAIN_WRAPED_NETWORKS
from config import GLOBAL_NETWORK
from src.utils.proxy_manager import Proxy


def get_client(account_name, private_key, network, proxy) -> Client:
    proxy = proxy.proxy_url.split("://")[1] if isinstance(proxy, Proxy) else proxy
    return Client(account_name, private_key, network, proxy)


def get_interface_by_chain_id(chain_id):
    return {
        2: ArbitrumNova,
        3: Base,
        4: Linea,
        8: Scroll,
        10: PolygonZkEVM,
        11: ZkSync,
        12: Zora,
        13: Ethereum,
        49: Blast
    }[chain_id]


def get_network_by_chain_id(chain_id):
    return {
        0: ArbitrumRPC,
        1: ArbitrumRPC,
        2: Arbitrum_novaRPC,
        3: BaseRPC,
        4: LineaRPC,
        5: MantaRPC,
        6: PolygonRPC,
        7: OptimismRPC,
        8: ScrollRPC,
        # 9: StarknetRPC,
        10: Polygon_ZKEVM_RPC,
        11: zkSyncEraRPC,
        12: ZoraRPC,
        13: EthereumRPC,
        14: AvalancheRPC,
        15: BSC_RPC,
        16: MoonbeamRPC,
        17: HarmonyRPC,
        18: TelosRPC,
        19: CeloRPC,
        20: GnosisRPC,
        21: CoreRPC,
        22: TomoChainRPC,
        23: ConfluxRPC,
        24: OrderlyRPC,
        25: HorizenRPC,
        26: MetisRPC,
        27: AstarRPC,
        28: OpBNB_RPC,
        29: MantleRPC,
        30: MoonriverRPC,
        31: KlaytnRPC,
        32: KavaRPC,
        33: FantomRPC,
        34: AuroraRPC,
        35: CantoRPC,
        36: DFK_RPC,
        37: FuseRPC,
        38: GoerliRPC,
        39: MeterRPC,
        40: OKX_RPC,
        41: ShimmerRPC,
        42: TenetRPC,
        43: XPLA_RPC,
        44: LootChainRPC,
        45: ZKFairRPC,
        46: BeamRPC,
        47: InEVM_RPC,
        48: RaribleRPC,
        49: BlastRPC,
        50: ModeRPC,
        51: GravityRPC,
        52: TaikoRPC,
        53: MintRPC,
    }[chain_id]


async def okx_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=1)


async def bingx_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=2)


async def binance_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=3)


async def bitget_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=4)

async def bridge_across(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=1)


async def bridge_bungee(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=2)


async def bridge_layerswap(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=3)


async def bridge_nitro(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=4)


async def bridge_orbiter(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=5)


async def bridge_owlto(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=6)


async def bridge_relay(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=7)


async def bridge_rhino(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=8)


async def bridge_native(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=9)


async def bridge_l2pass(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=1, dapp_mode=2)


async def bridge_nogem(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=2, dapp_mode=2)


async def bridge_merkly(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=3, dapp_mode=2)


async def bridge_whale(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=4, dapp_mode=2)


async def bridge_zerius(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=5, dapp_mode=2)


async def l2pass_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=1, dapp_mode=1)


async def nogem_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=2, dapp_mode=1)


async def merkly_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=3, dapp_mode=1)


async def whale_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=4, dapp_mode=1)


async def zerius_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=5, dapp_mode=1)


async def l2pass_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=1, dapp_mode=2)


async def nogem_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=2, dapp_mode=2)


async def merkly_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=3, dapp_mode=2)


async def whale_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=4, dapp_mode=2)


async def zerius_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=5, dapp_mode=2)


async def refuel_l2pass(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=1, dapp_mode=1)


async def refuel_nogem(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=2, dapp_mode=1)


async def refuel_merkly(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=3, dapp_mode=1)


async def refuel_whale(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=4, dapp_mode=1)


async def refuel_zerius(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=5, dapp_mode=1)


async def bridge_hyperlane_nft(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.merkly_omnichain_util(dapp_mode=3, dapp_function=2)


async def bridge_hyperlane_token(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.merkly_omnichain_util(dapp_mode=3, dapp_function=3)


async def okx_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=1)


async def bingx_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=2)


async def binance_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=3)


async def bitget_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=4)


async def withdraw_native_bridge(account_name, private_key, _, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)
    network = get_network_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def transfer_eth(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.transfer_eth()


async def transfer_eth_to_myself(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.transfer_eth_to_myself()


async def wrap_eth(account_name, private_key, network, proxy, *args):
    worker = SimpleEVM(get_client(account_name, private_key, network, proxy))
    return await worker.wrap_eth(*args)


async def unwrap_eth(account_name, private_key, network, proxy, **kwargs):
    worker = SimpleEVM(get_client(account_name, private_key, network, proxy))
    return await worker.unwrap_eth(**kwargs)


async def deploy_contract(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.deploy_contract()


# async  def mint_deployed_token(account_name, private_key, network, proxy, *args, **kwargs):
#     mint = ZkSync(account_name, private_key, network, proxy)
#     await mint.mint_token()


async def random_approve(account_nameaccount_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_nameaccount_name, private_key, network, proxy))
    return await worker.random_approve()


async def smart_random_approve(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_random_approve()


async def collector_eth(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.collect_eth()


async def make_balance_to_average(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.balance_average()


async def wrap_abuser(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.wraps_abuser()


async def bridge_stargate_dust(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1, dust_mode=True)


async def bridge_stargate(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1)


async def bridge_coredao(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=2)


async def swap_bridged_usdc(account_name, private_key, _, proxy):
    network = PolygonRPC
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.swap_bridged_usdc()



async def smart_stake_stg(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_stake_stg()
