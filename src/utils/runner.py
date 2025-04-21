import random
from typing import Any, Optional, List, Dict, Callable
from asyncio import sleep
from web3 import Web3

from loguru import logger

from config import *
from functions import *
from src.modules.custom_modules import *
from src.models.bridge import BridgeConfig
from src.models.token import Token
from src.modules.bridges.bridge_factory import SuperBridge, AcrossBridge, RelayBridge
from src.models.route import Route

from src.models.cex import OKXConfig, WithdrawSettings, CEXConfig
from src.modules.cex.okx.okx import OKX
from src.modules.other.contract_deploy.deployer import Deployer
from src.modules.lendings.venus.venus import Venus
from src.modules.other.ink_gm.ink_gm import InkGM
from src.modules.other.rubyscore.rubyscore import RubyScore
from src.modules.swaps.swap_factory import MatchaSwap, BungeeSwap, SushiSwap, OwltoSwap, RelaySwap, InkySwap, OkuSwap, \
    DefillamaSwap
from src.modules.swaps.uniswap.uniswap import Uniswap
from src.modules.swaps.wrapper.eth_wrapper import Wrapper

from src.models.chain import Chain

from src.utils.abc.abc_swap import ABCSwap
from src.utils.data.chains import chain_mapping
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.utils.user.super_account.client import SuperAccount


async def process_cex_withdraw(route: Route) -> Optional[bool]:
    account = Account(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )

    chain = OKXWithdrawSettings.chain
    token = OKXWithdrawSettings.token
    amount = OKXWithdrawSettings.amount

    okx_config = OKXConfig(
        deposit_settings=None,
        withdraw_settings=WithdrawSettings(
            token=token,
            chain=chain,
            to_address=str(account.wallet_address),
            amount=amount
        ),
        API_KEY=OKXSettings.API_KEY,
        API_SECRET=OKXSettings.API_SECRET,
        PASSPHRASE=OKXSettings.API_PASSWORD,
        PROXY=OKXSettings.PROXY
    )

    config = CEXConfig(
        okx_config=okx_config,
    )
    cex = OKX(
        config=config,
        private_key=route.wallet.private_key,
        proxy=OKXSettings.PROXY
    )

    logger.debug(cex)
    withdrawn = await cex.withdraw()

    if withdrawn is True:
        return True


async def process_wrapper_unwrapper(route: Route, chain: Chain) -> Optional[bool]:
    amount = WrapperUnwrapperSettings.amount
    use_all_balance = WrapperUnwrapperSettings.use_all_balance
    use_percentage = WrapperUnwrapperSettings.use_percentage
    percentage_to_wrap = WrapperUnwrapperSettings.percentage_to_wrap

    wrapper = Wrapper(
        private_key=route.wallet.private_key,
        amount=amount,
        use_all_balance=use_all_balance,
        use_percentage=use_percentage,
        percentage_to_wrap=percentage_to_wrap,
        proxy=route.wallet.proxy,
        chain=chain
    )
    logger.debug(wrapper)

    await wrapper.wrap(action='wrap')

    random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
        PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES
    logger.info(f'Сплю {random_sleep} секунд перед анврапом...')
    await sleep(random_sleep)

    await wrapper.wrap(action='unwrap')

    return True


async def process_swap(
        route: Route,
        config_class: Any,
        swap_class: type,
        chain: Chain
) -> Optional[bool]:
    from_token = config_class.from_token
    to_token = config_class.to_token
    amount = config_class.amount
    use_percentage = config_class.use_percentage
    swap_percentage = config_class.swap_percentage
    swap_all_balance = config_class.swap_all_balance

    swap_instance = swap_class(
        private_key=route.wallet.private_key,
        from_token=from_token,
        to_token=to_token,
        amount=amount,
        use_percentage=use_percentage,
        swap_percentage=swap_percentage,
        swap_all_balance=swap_all_balance,
        proxy=route.wallet.proxy,
        chain=chain
    )
    logger.debug(swap_instance)
    swapped = await swap_instance.swap()
    if swapped:
        return True


def create_process_swap_function(config_class: Any, swap_class: type[ABCSwap]) -> Callable:
    async def process(route: Route, chain: Chain) -> None:
        return await process_swap(route, config_class, swap_class, chain)

    return process


process_matcha_swap = create_process_swap_function(MatchaSwapSettings, MatchaSwap)
process_bungee_swap = create_process_swap_function(BungeeSwapSettings, BungeeSwap)
process_sushi_swap = create_process_swap_function(SushiSwapSettings, SushiSwap)
process_owlto_swap = create_process_swap_function(OwltoSwapSettings, OwltoSwap)
process_relay_swap = create_process_swap_function(RelaySwapSettings, RelaySwap)
process_inky_swap = create_process_swap_function(InkySwapSettings, InkySwap)
process_oku_swap = create_process_swap_function(OkuSwapSettings, OkuSwap)
process_defillama_swap = create_process_swap_function(DefillamaSwapSettings, DefillamaSwap)


async def process_bridge(route: Route, to_chain: Chain, from_chain: Chain, bridge_class: type) -> Optional[bool]:
    if to_chain.chain_name == from_chain:
        return True

    to_chain_account = Account(
        private_key=route.wallet.private_key,
        rpc=chain_mapping[to_chain.chain_name].rpc,
        proxy=route.wallet.proxy
    )
    
    to_chain_balance = await to_chain_account.get_wallet_balance(is_native=True)
    if to_chain_balance / 10 ** 18 >= DisperseChainsSettings.min_balance_in_chains[to_chain.chain_name]:
        logger.debug(
            f'В сети {to_chain.chain_name} уже есть {round((to_chain_balance / 10 ** 18), 5)} ETH. '
            f'Бридж не требуется.'
        )
        return True

    amount = random.uniform(DisperseChainsSettings.amount_to_bride[0], DisperseChainsSettings.amount_to_bride[1])

    bridge_class = bridge_class(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        bridge_config=BridgeConfig(
            from_chain=from_chain,
            to_chain=to_chain,
            from_token=Token(
                chain_name=from_chain.chain_name,
                name='ETH',
            ),
            to_token=Token(
                chain_name=to_chain.chain_name,
                name='ETH',
            ),
            amount=amount,
            use_percentage=False,
            bridge_percentage=0.01
        )
    )

    logger.debug(bridge_class)
    bridged = await bridge_class.bridge()
    if bridged:
        return True


async def get_balances_for_chains(
        chains: List[str],
        private_key: str,
        proxy: Proxy | None = None
) -> Dict[str, int]:
    balances = {}

    for chain_name in chains:
        rpc = chain_mapping[chain_name].rpc
        account = Account(private_key=private_key, rpc=rpc, proxy=proxy)
        wallet_address = account.wallet_address

        while True:
            try:
                balance = await account.web3.eth.get_balance(wallet_address)
                break
            except Exception as ex:
                logger.info(f'Не удалось проверить баланс | {ex}')
                await sleep(2)
        balances[chain_name] = balance

    return balances


async def process_chain_disperse(route: Route) -> Optional[bool]:
    chains = DisperseChainsSettings.base_chain
    balances = await get_balances_for_chains(
        chains,
        route.wallet.private_key,
        route.wallet.proxy
    )
    from_chain_name = max(balances, key=balances.get)
    from_chain = Chain(
        chain_name=from_chain_name,
        native_token=chain_mapping[from_chain_name].native_token,
        rpc=chain_mapping[from_chain_name].rpc,
        chain_id=chain_mapping[from_chain_name].chain_id
    )
    to_chains = DisperseChainsSettings.to_chains
    random.shuffle(to_chains)

    for to_chain_name in to_chains:
        to_chain = Chain(
            chain_name=to_chain_name,
            native_token=chain_mapping[to_chain_name].native_token,
            rpc=chain_mapping[to_chain_name].rpc,
            chain_id=chain_mapping[to_chain_name].chain_id
        )

        from_chain_bridges = SUPPORTED_BRIDGES_BY_CHAIN.get(from_chain_name, [])
        to_chain_bridges = SUPPORTED_BRIDGES_BY_CHAIN.get(to_chain_name, [])

        compatible_bridges = [bridge for bridge in from_chain_bridges if bridge in to_chain_bridges]

        if compatible_bridges:
            selected_bridge = random.choice(compatible_bridges)
            await process_bridge(route, to_chain, from_chain, selected_bridge)
        else:
            logger.warning(f'No compatible bridges found for {from_chain_name} -> {to_chain_name}. Skipping.')
            continue

        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
            PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

        logger.info(f'Сплю {random_sleep} секунд перед следующим бриджом...')

        await sleep(random_sleep)

    return True


def generate_activities(chain_name) -> list[str]:
    # Выбираем настройки для конкретной сети или используем общие настройки
    transactions_range = RandomTransactionsSettings.transactions_by_chain.get(
        chain_name, [1, 1]
    )

    num_operations = random.randint(
        transactions_range[0],
        transactions_range[1]
    )

    all_activities = AVAILABLE_ACTIVITIES[chain_name]
    filtered_activities = [activity for activity in all_activities
                           if activity not in ['RANDOM_SWAPS', 'SWAP_ALL_TO_ETH']]

    if not filtered_activities:
        logger.warning(f'Нет доступных активностей для сети {chain_name} после фильтрации')
        return []

    random_activities = [random.choice(filtered_activities) for _ in range(num_operations)]

    logger.info(
        f'Создал список активностей: {random_activities} ({num_operations}/{len(filtered_activities)}), для сети - [{chain_name}]')
    return random_activities


async def process_random_activities(route: Route, chain_name: str):
    activities = generate_activities(chain_name)
    await process_activities(route, chain_name, activities)


async def process_activities(route: Route, chain_name: str, activities: list[str]) -> Optional[bool]:
    chain = Chain(
        chain_name=chain_name,
        native_token=chain_mapping[chain_name].native_token,
        rpc=chain_mapping[chain_name].rpc,
        chain_id=chain_mapping[chain_name].chain_id
    )
    if 'SWAP_ALL_TO_ETH' in activities:
        activities.remove('SWAP_ALL_TO_ETH')
        activities.append('SWAP_ALL_TO_ETH')

    has_venus_deposit = 'VENUS_DEPOSIT' in activities
    has_venus_withdraw = 'VENUS_WITHDRAW' in activities

    if has_venus_deposit and has_venus_withdraw:
        venus_deposit_idx = activities.index('VENUS_DEPOSIT')
        venus_withdraw_idx = activities.index('VENUS_WITHDRAW')
        if venus_withdraw_idx < venus_deposit_idx:
            activities[venus_deposit_idx], activities[venus_withdraw_idx] = (
                activities[venus_withdraw_idx], activities[venus_deposit_idx]
            )

    for activity in activities:
        if activity == 'RANDOM_TXS':
            await process_random_activities(route, chain_name)
        if activity not in AVAILABLE_ACTIVITIES[chain.chain_name]:
            logger.warning(f'Активность {activity} не поддерживается в сети {chain.chain_name}')
            continue
        await function_handlers[activity](route, chain)

        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
            PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

        logger.info(f'Сплю {random_sleep} секунд перед следующей активностью...')

        await sleep(random_sleep)
    return True


async def process_ink_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.INK_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'INK', activities)


async def process_base_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.BASE_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'BASE', activities)


async def process_op_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.OPTIMISM_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'OP', activities)


async def process_lisk_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.LISK_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'LISK', activities)


async def process_unichain_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.UNICHAIN_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'UNICHAIN', activities)


async def process_soneium_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.SONEIUM_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'SONEIUM', activities)


async def process_zora_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.ZORA_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'ZORA', activities)


async def process_swell_activities(route: Route) -> Optional[bool]:
    activities = RandomDailyTxConfig.SWELL_MODULES
    random.shuffle(activities)
    return await process_activities(route, 'SWELL', activities)


async def process_uniswap(route: Route, chain: Chain) -> Optional[bool]:
    from_token = UniswapSettings.from_token
    to_token = UniswapSettings.to_token
    amount = UniswapSettings.amount
    use_percentage = UniswapSettings.use_percentage
    swap_percentage = UniswapSettings.swap_percentage
    swap_all_balance = UniswapSettings.swap_all_balance

    uniswap = Uniswap(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        amount=amount,
        from_token=from_token,
        to_token=to_token,
        use_percentage=use_percentage,
        swap_percentage=swap_percentage,
        swap_all_balance=swap_all_balance,
        chain=chain
    )
    logger.debug(uniswap)
    swapped = await uniswap.swap()
    if swapped:
        return True
    
async def bridge_stargate(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1)

async def process_venus_deposit(route: Route, chain: Chain) -> Optional[bool]:
    venus = Venus(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        action='deposit',
        chain=chain
    )
    logger.debug(venus)

    deposited = await venus.deposit_in_pool(
        token=random.choice(VenusDepositSettings.token),
        deposit_percentage=random.uniform(
            VenusDepositSettings.percentage_to_deposit[0],
            VenusDepositSettings.percentage_to_deposit[1]
        )
    )
    if deposited:
        return True


async def process_venus_withdraw(route: Route, chain: Chain) -> Optional[bool]:
    venus = Venus(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        action='withdraw',
        chain=chain
    )
    logger.debug(venus)
    withdrawn = await venus.withdraw_all()
    if withdrawn:
        return True


async def process_random_swaps(route: Route, chain: Chain) -> Optional[bool]:
    num_swaps = RandomSwapsSettings.number_of_swaps
    token_list = [token for token in tokens[chain.chain_name].keys() if token not in ['WETH', 'ETH']]
    if isinstance(num_swaps, list):
        num_swaps = random.randint(num_swaps[0], num_swaps[1])

    settings_mapping = {
        Uniswap: UniswapSettings,
        BungeeSwap: BungeeSwapSettings,
        MatchaSwap: MatchaSwapSettings,
        OwltoSwap: OwltoSwapSettings,
        DefillamaSwap: DefillamaSwapSettings,
        InkySwap: InkySwapSettings,
        OkuSwap: OkuSwapSettings,
        SushiSwap: SushiSwapSettings,
        RelaySwap: RelaySwapSettings
    }

    for _ in range(num_swaps):
        supported_swap_classes = SUPPORTED_SWAPS_BY_CHAIN.get(chain.chain_name, [])
        if not supported_swap_classes:
            logger.error(f"No supported swap classes for chain {chain.chain_name}")
            break
        swap_class = random.choice(supported_swap_classes)

        print(f'Свапаю на {swap_class.__name__}')
        from_token = 'ETH'
        to_token = random.choice(token_list)
        amount = settings_mapping[swap_class].amount
        use_percentage = True
        swap_percentage = RandomSwapsSettings.swap_percentage
        swap_all_balance = False

        swap = swap_class(
            private_key=route.wallet.private_key,
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            use_percentage=use_percentage,
            swap_percentage=swap_percentage,
            swap_all_balance=swap_all_balance,
            proxy=route.wallet.proxy,
            chain=chain
        )
        logger.debug(swap)
        swapped = await swap.swap()

        if swapped:
            random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
                PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

            logger.info(f'Сплю {random_sleep} секунд перед следующим свапом...')
            await sleep(random_sleep)

        if swap == 'ZeroBalance':
            await sleep(2)

    return True


async def process_swap_all_to_eth(route: Route, chain: Chain) -> Optional[bool]:
    token_list = list(tokens[chain.chain_name].keys())
    if 'WETH' in token_list:
        token_list.remove('WETH')
        token_list.append('WETH')

    for token in token_list:
        i = 0
        if token == 'ETH':
            continue

        if token == 'WETH':
            unwrapper = Wrapper(
                private_key=route.wallet.private_key,
                amount=0.01,
                use_all_balance=True,
                use_percentage=False,
                percentage_to_wrap=0.01,
                proxy=route.wallet.proxy,
                chain=chain
            )
            logger.debug(unwrapper)
            await unwrapper.wrap(action='unwrap')
            continue

        while i < 5:
            supported_swap_classes = SUPPORTED_SWAPS_BY_CHAIN.get(chain.chain_name, [])
            if not supported_swap_classes:
                logger.error(f"No supported swap classes for chain {chain.chain_name}")
                break

            swap_class = random.choice(supported_swap_classes)
            i += 1

            swap_all_tokens_swap = swap_class(
                private_key=route.wallet.private_key,
                from_token=token,
                to_token='ETH',
                amount=0.0,
                use_percentage=False,
                swap_percentage=0.1,
                swap_all_balance=True,
                proxy=route.wallet.proxy,
                chain=chain
            )

            logger.debug(swap_all_tokens_swap)
            swap = await swap_all_tokens_swap.swap()

            if swap == 'ZeroBalance':
                await sleep(1)
                break

            elif swap:
                random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
                    PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

                logger.info(f'Sleeping {random_sleep} seconds before next swap...')
                await sleep(random_sleep)
                break

            else:
                await sleep(10)
                continue

    return True


async def process_rubyscore_vote(route: Route, chain: Chain) -> Optional[bool]:
    ruby_score = RubyScore(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        chain=chain
    )
    logger.debug(ruby_score)
    voted = await ruby_score.vote()
    if voted:
        return True


async def process_ink_gm(route: Route, chain: Chain) -> Optional[bool]:
    ruby_score = InkGM(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        chain=chain
    )
    logger.debug(ruby_score)
    gm = await ruby_score.vote()
    if gm:
        return True


async def process_deploy(route: Route, chain: Chain) -> Optional[bool]:
    deployer = Deployer(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        chain=chain
    )
    logger.debug(deployer)
    deployed = await deployer.deploy()
    if deployed:
        return True


async def process_badges(route: Route) -> Optional[bool]:
    super_account = SuperAccount(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    claimed = await super_account.claim_badges()
    if claimed:
        return True


AVAILABLE_ACTIVITIES = {
    'BASE': ['UNISWAP', 'SUSHI_SWAP', 'MATCHA_SWAP', 'BUNGEE_SWAP', 'OWLTO_SWAP', 'SWAP_ALL_TO_ETH', 'RANDOM_SWAPS',
             'RELAY_SWAP', 'OKU_SWAP', 'DEFILLAMA_SWAP', 'RUBYSCORE_VOTE', 'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'ZORA': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'OWLTO_SWAP', 'RELAY_SWAP', 'UNISWAP', 'RUBYSCORE_VOTE',
             'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'INK': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'OWLTO_SWAP', 'RELAY_SWAP', 'INKY_SWAP', 'WRAPPER_UNWRAPPER', 'INK_GM',
            'CONTRACT_DEPLOY'],
    'OP': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'OWLTO_SWAP', 'RELAY_SWAP', 'UNISWAP', 'SUSHI_SWAP', 'MATCHA_SWAP',
           'BUNGEE_SWAP', 'OKU_SWAP', 'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'MODE': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'OWLTO_SWAP', 'RELAY_SWAP', 'SUSHI_SWAP', 'MATCHA_SWAP',
             'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'UNICHAIN': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'UNISWAP', 'OWLTO_SWAP', 'BUNGEE_SWAP', 'RELAY_SWAP', 'MATCHA_SWAP',
                 'WRAPPER_UNWRAPPER', 'VENUS_DEPOSIT', 'VENUS_WITHDRAW', 'CONTRACT_DEPLOY'],
    'LISK': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'RELAY_SWAP', 'OKU_SWAP', 'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'SONEIUM': ['SWAP_ALL_TO_ETH', 'RANDOM_SWAPS', 'RELAY_SWAP', 'OKU_SWAP', 'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY'],
    'SWELL': ['SWAP_ALL_TO_ETH', 'WRAPPER_UNWRAPPER', 'CONTRACT_DEPLOY']
}

function_handlers = {
    'UNISWAP': process_uniswap,
    'SUSHI_SWAP': process_sushi_swap,
    'MATCHA_SWAP': process_matcha_swap,
    'BUNGEE_SWAP': process_bungee_swap,
    'OWLTO_SWAP': process_owlto_swap,
    'SWAP_ALL_TO_ETH': process_swap_all_to_eth,
    'RANDOM_SWAPS': process_random_swaps,
    'RELAY_SWAP': process_relay_swap,
    'INKY_SWAP': process_inky_swap,
    'OKU_SWAP': process_oku_swap,
    'DEFILLAMA_SWAP': process_defillama_swap,
    'RUBYSCORE_VOTE': process_rubyscore_vote,
    'CONTRACT_DEPLOY': process_deploy,
    'WRAPPER_UNWRAPPER': process_wrapper_unwrapper,
    'VENUS_DEPOSIT': process_venus_deposit,
    'VENUS_WITHDRAW': process_venus_withdraw,
    'INK_GM': process_ink_gm
}

SUPPORTED_SWAPS_BY_CHAIN = {
    "UNICHAIN": [Uniswap, BungeeSwap, MatchaSwap, OwltoSwap, RelaySwap],
    "BASE": [Uniswap, MatchaSwap, SushiSwap, OwltoSwap, RelaySwap, OkuSwap, DefillamaSwap],
    "ZORA": [Uniswap, OwltoSwap, RelaySwap],
    "OP": [Uniswap, MatchaSwap, SushiSwap, OwltoSwap, RelaySwap, OkuSwap, DefillamaSwap],
    "INK": [OwltoSwap, RelaySwap, InkySwap],
    "MODE": [MatchaSwap, SushiSwap, OwltoSwap, RelaySwap],
    "SONEIUM": [OwltoSwap, RelaySwap],
    "LISK": [RelaySwap, OkuSwap],
    "SWELL": [RelaySwap]
}

SUPPORTED_BRIDGES_BY_CHAIN = {
    "UNICHAIN": [RelayBridge],
    "BASE": [RelayBridge, AcrossBridge],
    "ZORA": [RelayBridge],
    "OP": [RelayBridge, AcrossBridge],
    "INK": [RelayBridge, AcrossBridge],
    "MODE": [RelayBridge],
    "SONEIUM": [RelayBridge],
    "LISK": [RelayBridge, AcrossBridge],
    "SWELL": [RelayBridge]
}
