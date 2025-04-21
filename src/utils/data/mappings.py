from src.utils.runner import *

module_handlers = {
    'OKX_WITHDRAW': process_cex_withdraw,
    'UNISWAP': process_uniswap,
    'MATCHA_SWAP': process_matcha_swap,
    'BUNGEE_SWAP': process_bungee_swap,
    'SUSHI_SWAP': process_sushi_swap,
    'RELAY_SWAP': process_relay_swap,
    'VENUS_DEPOSIT': process_venus_deposit,
    'VENUS_WITHDRAW': process_venus_withdraw,
    'RANDOM_SWAPS': process_random_swaps,
    'SWAP_ALL_TO_ETH': process_swap_all_to_eth,
    'BASE_RANDOM_TX': process_base_activities,
    'INK_RANDOM_TX': process_ink_activities,
    'DISPERSE_BRIDGE': process_chain_disperse,
    'OP_RANDOM_TX': process_op_activities,
    'LISK_RANDOM_TX': process_lisk_activities,
    'UNICHAIN_RANDOM_TX': process_unichain_activities,
    'SONEIUM_RANDOM_TX': process_soneium_activities,
    'ZORA_RANDOM_TX': process_zora_activities,
    'SWELL_RANDOM_TX': process_swell_activities,
    'CLAIM_BADGES': process_badges,
    'STARGATE_BRIDGE': bridge_stargate
}
